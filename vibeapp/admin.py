from django.contrib import admin
from .models import Profile, Follow, Post, Reel, ReelComment, Notification, Thread, Message

# --- PROFILE & FOLLOW ---
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_completed', 'is_public', 'created_at')
    search_fields = ('user__username', 'location')

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following', 'status', 'created_at')
    list_filter = ('status',)

# --- POSTS & REELS ---
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('user', 'caption', 'created_at')
    search_fields = ('user__username', 'caption')

@admin.register(Reel)
class ReelAdmin(admin.ModelAdmin):
    list_display = ('user', 'caption', 'created_at')
    search_fields = ('user__username', 'caption')

@admin.register(ReelComment)
class ReelCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'reel', 'text', 'created_at')
    search_fields = ('user__username', 'text')

# --- NOTIFICATIONS ---
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'notification_type', 'is_seen', 'created_at')
    list_filter = ('notification_type', 'is_seen')

# --- CHAT & MESSAGES ---
@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ('id', 'is_pending', 'created_at')
    list_filter = ('is_pending',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'thread', 'timestamp', 'is_read')
    search_fields = ('sender__username', 'content')