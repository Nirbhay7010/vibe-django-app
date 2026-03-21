from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile, Follow, Notification

# --- PROFILE SIGNALS ---

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create a Profile when a new User is registered."""
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Ensure the profile is saved whenever the User object is saved."""
    instance.profile.save()


# --- FOLLOW & NOTIFICATION SIGNALS ---

@receiver(post_save, sender=Follow)
def follow_notification(sender, instance, created, **kwargs):
    if created:
        # Check if the account being followed is private (status='pending')
        notif_type = 'follow_request' if instance.status == 'pending' else 'follow'
        
        Notification.objects.create(
            sender=instance.follower,
            receiver=instance.following,
            notification_type=notif_type
        )
        
    elif instance.status == 'accepted':
        # Notify the requester that their follow request was confirmed
        Notification.objects.get_or_create(
            sender=instance.following,
            receiver=instance.follower,
            notification_type='accept'
        )