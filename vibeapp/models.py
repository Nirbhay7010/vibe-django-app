from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save 
from django.dispatch import receiver 

# --- PROFILE MODEL ---
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to="profiles/", default="profiles/d2.png")
    website = models.URLField(blank=True) 
    location = models.CharField(max_length=100, blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=True)

    # --- Notification Preferences ---
    notif_likes_comments = models.BooleanField(default=True)
    notif_followers = models.BooleanField(default=True)
    notif_messages = models.BooleanField(default=True)

    # --- Blocked Users ---
    blocked_users = models.ManyToManyField(User, related_name='blocked_by', blank=True)

    def __str__(self):
        return self.user.username

    @property
    def unread_notifications_count(self):
        return self.user.notifications.filter(is_seen=False).count()

    @property
    def followers_count(self):
        return Follow.objects.filter(following=self.user, status='accepted').count()

    @property
    def following_count(self):
        return Follow.objects.filter(follower=self.user, status='accepted').count()


# --- FOLLOW MODEL ---
class Follow(models.Model):
    follower = models.ForeignKey(User, related_name="following_rel", on_delete=models.CASCADE)
    following = models.ForeignKey(User, related_name="followers_rel", on_delete=models.CASCADE)
    
    STATUS_CHOICES = (
        ('accepted', 'Accepted'), 
        ('pending', 'Pending'), 
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='accepted')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f"{self.follower.username} -> {self.following.username} ({self.status})"


# --- POST MODEL ---
class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    image = models.ImageField(upload_to="posts/")
    caption = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # New fields for Feed interactions
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    saved_by = models.ManyToManyField(User, related_name='saved_posts', blank=True)

    def __str__(self):
        return f"Post by {self.user.username} at {self.created_at.strftime('%Y-%m-%d')}"


# --- POST COMMENT MODEL ---
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.text[:20]}"


# --- REEL MODELS ---
class Reel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reels")
    video = models.FileField(upload_to="reels_videos/")
    caption = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name='liked_reels', blank=True)
    
    hidden_by = models.ManyToManyField(User, related_name='hidden_reels', blank=True)
    saved_by = models.ManyToManyField(User, related_name='saved_reels', blank=True)

    def __str__(self):
        return f"Reel by {self.user.username} at {self.created_at.strftime('%Y-%m-%d')}"

class ReelComment(models.Model):
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.text[:20]}"


# --- NOTIFICATION MODEL ---
class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('like_post', 'Like Post'),           
        ('comment_post', 'Comment Post'),     
        ('follow', 'Follow'),           
        ('follow_request', 'Request'),  
        ('accept', 'Accepted Request'), 
    )

    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    notification_type = models.CharField(choices=NOTIFICATION_TYPES, max_length=20)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_seen = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username} ({self.notification_type})"


# --- CHAT / DM MODELS ---
class Thread(models.Model):
    participants = models.ManyToManyField(User, related_name='threads')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_pending = models.BooleanField(default=False)
    initiator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='initiated_threads')

    def __str__(self):
        return f"Thread {self.id}"

class Message(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    
    content = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    
    shared_reel = models.ForeignKey(Reel, on_delete=models.SET_NULL, null=True, blank=True, related_name='shared_in_messages')
    shared_post = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True, blank=True, related_name='shared_in_messages')
    
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


# --- SIGNALS ---
@receiver(post_save, sender=Follow)
def follow_notification(sender, instance, created, **kwargs):
    if created:
        # Check settings before sending follow notifications
        if instance.status == 'accepted' and instance.following.profile.notif_followers:
            Notification.objects.create(
                sender=instance.follower,
                receiver=instance.following,
                notification_type='follow'
            )
        elif instance.status == 'pending' and instance.following.profile.notif_followers:
            Notification.objects.create(
                sender=instance.follower,
                receiver=instance.following,
                notification_type='follow_request'
            )
    else:
        if instance.status == 'accepted':
            Notification.objects.filter(
                sender=instance.follower,
                receiver=instance.following,
                notification_type='follow_request'
            ).delete()
            
            if instance.follower.profile.notif_followers and not Notification.objects.filter(sender=instance.following, receiver=instance.follower, notification_type='accept').exists():
                Notification.objects.create(
                    sender=instance.following,
                    receiver=instance.follower,
                    notification_type='accept'
                )