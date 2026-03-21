from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Thread, Message, Reel

class UserBasicSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'profile_image']
        
    def get_profile_image(self, obj):
        # Grabs the profile image URL if the user has a profile set up
        if hasattr(obj, 'profile') and obj.profile.profile_image:
            return obj.profile.profile_image.url
        # Fallback to the default Vibe avatar if none exists
        return '/media/profiles/d2.png'

class MessageSerializer(serializers.ModelSerializer):
    sender = UserBasicSerializer(read_only=True)
    # ✨ NEW: Tell Django how to package the shared reel data
    shared_reel = serializers.SerializerMethodField()

    class Meta:
        model = Message
        # ✨ Added 'shared_reel' to the fields array!
        fields = ['id', 'sender', 'content', 'image', 'shared_reel', 'timestamp', 'is_read']

    def get_shared_reel(self, obj):
        if obj.shared_reel:
            return {
                'id': obj.shared_reel.id,
                'video_url': obj.shared_reel.video.url if obj.shared_reel.video else '',
                'username': obj.shared_reel.user.username
            }
        return None

class ThreadSerializer(serializers.ModelSerializer):
    participants = UserBasicSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Thread
        fields = ['id', 'participants', 'created_at', 'updated_at', 'last_message', 'is_pending', 'initiator']

    def get_last_message(self, obj):
        # Grabs the most recent message to display in the inbox preview
        last_msg = obj.messages.last() 
        if last_msg:
            return MessageSerializer(last_msg).data
        return None