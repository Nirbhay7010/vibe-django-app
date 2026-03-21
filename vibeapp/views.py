import re
import base64
import uuid
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.files.base import ContentFile
from django.db.models import Q 

# DRF & Channels Imports
from rest_framework import generics, permissions
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Local imports
from .models import Profile, Post, Follow, Notification, Thread, Message, Reel, ReelComment
from .forms import ProfileSetupForm, ProfileUpdateForm
from .serializers import ThreadSerializer, MessageSerializer

# ==========================
# AUTHENTICATION VIEWS
# ==========================

def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not username or not email or not password:
            messages.error(request, "All fields are required")
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect('signup')

        password_pattern = r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'
        if not re.match(password_pattern, password):
            messages.error(request, "Password must be at least 8 chars, 1 uppercase, 1 number, 1 special char")
            return redirect('signup')

        User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, "Account created successfully. Please login.")
        return redirect('login')

    return render(request, 'signup.html')


def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            return redirect('post_login_redirect')
        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'login.html')


@login_required(login_url='login')
def post_login_redirect(request):
    if not hasattr(request.user, 'profile') or not request.user.profile.is_completed:
        return redirect('profilesetup')
    return redirect('Vibe')


def logoutUser(request):
    logout(request)
    return redirect('login')


# ==========================
# FEED & PROFILE LOGIC
# ==========================

@login_required(login_url='login')
def Vibe(request):
    following_users_ids = Follow.objects.filter(
        follower=request.user, 
        status='accepted'
    ).values_list('following_id', flat=True)

    posts = Post.objects.filter(
        Q(user__id__in=following_users_ids) | 
        Q(user=request.user)
    ).distinct().order_by("-created_at")

    existing_relationships = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
    
    suggested_users = User.objects.exclude(
        Q(id=request.user.id) | 
        Q(id__in=existing_relationships)
    )[:5]

    people_who_follow_me = Follow.objects.filter(
        following=request.user, 
        status='accepted'
    ).values_list('follower_id', flat=True)

    for u in suggested_users:
        u.is_following_you = u.id in people_who_follow_me

    return render(request, "vide.html", {
        "posts": posts,
        "users": suggested_users
    })

@login_required(login_url='login')
def user_profile(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    
    follow_status = Follow.objects.filter(
        follower=request.user, 
        following=target_user
    ).first()

    is_following = False
    is_requested = False

    if follow_status:
        if follow_status.status == 'accepted':
            is_following = True
        elif follow_status.status == 'pending':
            is_requested = True

    is_followed_by = Follow.objects.filter(
        follower=target_user,
        following=request.user,
        status='accepted'
    ).exists()

    is_public_profile = getattr(target_user.profile, 'is_public', True)

    can_view = False
    if request.user == target_user: 
        can_view = True
    elif is_public_profile:         
        can_view = True
    elif is_following:              
        can_view = True
    
    if can_view:
        posts = Post.objects.filter(user=target_user).order_by('-created_at')
    else:
        posts = []

    followers_count = Follow.objects.filter(following=target_user, status='accepted').count()
    following_count = Follow.objects.filter(follower=target_user, status='accepted').count()

    context = {
        'target_user': target_user,
        'posts': posts,
        'followers_count': followers_count,
        'following_count': following_count,
        'is_following': is_following,
        'is_requested': is_requested,
        'is_followed_by': is_followed_by,
        'is_private': not is_public_profile,
        'can_view': can_view
    }
    return render(request, 'user_profile.html', context)


@login_required(login_url='login')
def profile(request):
    return user_profile(request, request.user.id)


# ==========================
# FOLLOW SYSTEM
# ==========================

@login_required(login_url='login')
def follow_user(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    
    if not Follow.objects.filter(follower=request.user, following=target_user).exists():
        is_public = getattr(target_user.profile, 'is_public', True)
        status = 'accepted' if is_public else 'pending'

        Follow.objects.create(
            follower=request.user, 
            following=target_user, 
            status=status
        )
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'followed'})
        
    return redirect('user_profile', user_id=user_id)


@login_required(login_url='login')
def unfollow_user(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    Follow.objects.filter(follower=request.user, following=target_user).delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'unfollowed'})
        
    return redirect('user_profile', user_id=user_id)


@login_required(login_url='login')
def accept_request(request, user_id):
    if request.method == "POST":
        requester = get_object_or_404(User, id=user_id)
        follow_req = Follow.objects.filter(follower=requester, following=request.user, status='pending').first()
        
        if follow_req:
            follow_req.status = 'accepted'
            follow_req.save()
            
        Notification.objects.filter(sender=requester, receiver=request.user, notification_type='follow_request').delete()
            
        is_following_back = Follow.objects.filter(follower=request.user, following=requester, status='accepted').exists()
        
        return JsonResponse({
            'status': 'success', 
            'is_following_back': is_following_back
        })
    return JsonResponse({'status': 'error'}, status=400)


@login_required(login_url='login')
def decline_request(request, user_id):
    if request.method == "POST":
        requester = get_object_or_404(User, id=user_id)
        Follow.objects.filter(follower=requester, following=request.user, status='pending').delete()
        Notification.objects.filter(sender=requester, receiver=request.user, notification_type='follow_request').delete()
        
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required(login_url='login')
def remove_follower(request, user_id):
    follower_to_remove = get_object_or_404(User, id=user_id)
    Follow.objects.filter(follower=follower_to_remove, following=request.user).delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'removed'})
        
    return redirect('user_profile', user_id=request.user.id)


# ==========================
# SETTINGS & ACTIONS
# ==========================

@login_required(login_url='login')
def create_post(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            image_data = data.get("image")
            caption = data.get("caption", "")

            if not image_data:
                return JsonResponse({"status": "error", "message": "No image data provided"}, status=400)

            if ";base64," in image_data:
                format, imgstr = image_data.split(";base64,")
                ext = format.split("/")[-1]
                
                image_content = base64.b64decode(imgstr)
                file_name = f"post_{uuid.uuid4()}.{ext}"
                image_file = ContentFile(image_content, name=file_name)

                new_post = Post.objects.create(
                    user=request.user, 
                    image=image_file, 
                    caption=caption
                )
                
                return JsonResponse({
                    "status": "success", 
                    "message": "Post created!",
                    "post_id": new_post.id
                })
            else:
                return JsonResponse({"status": "error", "message": "Invalid image format"}, status=400)

        except Exception as e:
            print(f"--- CREATE POST ERROR: {str(e)} ---")
            return JsonResponse({"status": "error", "message": "Internal server error during save"}, status=500)

    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)


@login_required(login_url='login')
def setting(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully")
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=profile)
    return render(request, 'setting.html', {'form': form})


@login_required(login_url='login')
def profilsetup(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if profile.is_completed:
        return redirect('Vibe')

    if request.method == 'POST':
        form = ProfileSetupForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.is_completed = True 
            profile.save()
            return redirect('Vibe')
    else:
        form = ProfileSetupForm(instance=profile)

    return render(request, 'profilesetup.html', {'form': form})


@login_required(login_url='login')
def followers_list(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    relationships = Follow.objects.filter(following=target_user, status='accepted')
    users = [rel.follower for rel in relationships]
    
    return render(request, 'follow_list.html', {
        'type': 'Followers',
        'target_user': target_user,
        'users': users
    })


@login_required(login_url='login')
def following_list(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    relationships = Follow.objects.filter(follower=target_user, status='accepted')
    users = [rel.following for rel in relationships]
    
    return render(request, 'follow_list.html', {
        'type': 'Following',
        'target_user': target_user,
        'users': users
    })
    

@login_required(login_url='login')
def mark_notifications_as_read(request):
    if request.method == 'POST':
        Notification.objects.filter(receiver=request.user, is_seen=False).update(is_seen=True)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)


@login_required(login_url='login')
def delete_post(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(Post, id=post_id, user=request.user)
        post.delete()
        messages.success(request, "Post deleted successfully.")
    return redirect('profile')


# ==========================
# SEARCH LOGIC
# ==========================

@login_required(login_url='login')
def search_results(request):
    query = request.GET.get('q', '') 
    results = []

    if query:
        results = User.objects.filter(username__icontains=query)
    
    context = {
        'query': query,
        'results': results
    }
    return render(request, 'search_results.html', context)


@login_required(login_url='login')
def live_search(request):
    query = request.GET.get('q', '')
    results = []

    if query:
        users = User.objects.filter(username__icontains=query)[:10]
        
        for user in users:
            profile_image_url = ''
            if hasattr(user, 'profile') and user.profile.profile_image:
                profile_image_url = user.profile.profile_image.url
                
            results.append({
                'id': user.id,
                'username': user.username,
                'profile_image': profile_image_url,
            })

    return JsonResponse({'results': results})


# ==========================
# CHAT & DIRECT MESSAGES
# ==========================

@login_required(login_url='login')
def inbox_view(request):
    # Pass suggested users to the frontend for the "New Message" modal
    suggested_users = User.objects.exclude(id=request.user.id)[:30] 
    return render(request, 'inbox.html', {'suggested_users': suggested_users})

@login_required
def video_call_view(request, thread_id):
    """
    Dedicated view to render the video call UI securely.
    Ensures that only participants of a thread can access the call room.
    """
    thread = get_object_or_404(Thread, id=thread_id)
    
    if request.user not in thread.participants.all():
        messages.error(request, "You do not have permission to join this call.")
        return redirect('inbox_view')
        
    return render(request, 'video_call.html', {'thread': thread})


class ThreadListView(generics.ListAPIView):
    """ Returns a list of all conversations for the logged-in user. """
    serializer_class = ThreadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Thread.objects.filter(participants=self.request.user).order_by('-updated_at')


class MessageListView(generics.ListCreateAPIView):
    """ Returns message history for a thread, and allows sending a basic message. """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        thread_id = self.kwargs['thread_id']
        return Message.objects.filter(
            thread__id=thread_id, 
            thread__participants=self.request.user
        )

    def perform_create(self, serializer):
        thread_id = self.kwargs['thread_id']
        thread = Thread.objects.get(id=thread_id)
        serializer.save(sender=self.request.user, thread=thread)
        thread.save()


def get_or_create_thread(request, user_id):
    if request.method == 'POST' and request.user.is_authenticated:
        other_user = get_object_or_404(User, id=user_id)
        
        thread = Thread.objects.filter(participants=request.user).filter(participants=other_user).first()
        
        if not thread:
            thread = Thread.objects.create(initiator=request.user)
            thread.participants.add(request.user, other_user)
            
            # Check if the other user follows you back
            is_followed_by = Follow.objects.filter(follower=other_user, following=request.user, status='accepted').exists()
            
            # If they don't follow you, it goes to their requests
            thread.is_pending = not is_followed_by
            thread.save()
            
        avatar_url = '/media/profiles/d2.png'
        if hasattr(other_user, 'profile') and other_user.profile.profile_image:
            avatar_url = other_user.profile.profile_image.url
            
        return JsonResponse({
            'thread_id': thread.id,
            'username': other_user.username,
            'avatar_url': avatar_url,
            'is_pending': thread.is_pending,
            'initiator_id': thread.initiator.id if thread.initiator else None
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def accept_chat_request(request, thread_id):
    if request.method == 'POST':
        thread = get_object_or_404(Thread, id=thread_id)
        thread.is_pending = False
        thread.save()
        return JsonResponse({'status': 'accepted'})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def upload_chat_image(request, thread_id):
    if request.method == 'POST' and request.FILES.get('image'):
        thread = get_object_or_404(Thread, id=thread_id)
        image = request.FILES['image']
        
        # 1. Save message to DB
        msg = Message.objects.create(
            thread=thread, sender=request.user, content="Sent an image", image=image
        )
        thread.save() # trigger updated_at
        
        # 2. Blast it instantly over WebSockets
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'chat_{thread_id}',
            {
                'type': 'chat_message',
                'message': msg.content,
                'image_url': msg.image.url,
                'sender_id': request.user.id,
                'sender_username': request.user.username,
                'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M')
            }
        )
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'failed'}, status=400)

@login_required
def decline_chat_request(request, thread_id):
    if request.method == 'POST':
        thread = get_object_or_404(Thread, id=thread_id)
        # Ensure the user is actually part of this thread before deleting
        if request.user in thread.participants.all():
            thread.delete()
            return JsonResponse({'status': 'deleted'})
    return JsonResponse({'error': 'Invalid request'}, status=400)


# ==========================
# REELS VIEWS
# ==========================

@login_required
def reels_feed(request):
    # Fetch all reels, EXCLUDING the ones the user marked as hidden/not interested
    reels = Reel.objects.exclude(hidden_by=request.user).order_by('-created_at')
    
    # We pass the user's chat threads so they can easily pick who to share a reel with
    user_threads = request.user.threads.all()
    
    context = {
        'reels': reels,
        'user_threads': user_threads,
    }
    return render(request, 'reels.html', context)


@login_required
def like_reel(request, reel_id):
    if request.method == 'POST':
        reel = get_object_or_404(Reel, id=reel_id)
        if request.user in reel.likes.all():
            reel.likes.remove(request.user)
            liked = False
        else:
            reel.likes.add(request.user)
            liked = True
            
        return JsonResponse({
            'status': 'success', 
            'liked': liked, 
            'like_count': reel.likes.count()
        })
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


@login_required
def add_reel_comment(request, reel_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        text = data.get('text', '').strip()
        
        if text:
            reel = get_object_or_404(Reel, id=reel_id)
            comment = ReelComment.objects.create(
                reel=reel,
                user=request.user,
                text=text
            )
            return JsonResponse({
                'status': 'success', 
                'username': request.user.username,
                'text': comment.text,
                'comment_count': reel.comments.count()
            })
    return JsonResponse({'status': 'error', 'message': 'Comment cannot be empty'})


@login_required
def share_reel_to_chat(request, reel_id, thread_id):
    if request.method == 'POST':
        reel = get_object_or_404(Reel, id=reel_id)
        thread = get_object_or_404(Thread, id=thread_id)
        
        # Ensure the user is actually part of the thread before sharing
        if request.user in thread.participants.all():
            Message.objects.create(
                thread=thread,
                sender=request.user,
                content="Check out this reel!", # Default text accompanying the reel
                shared_reel=reel
            )
            return JsonResponse({'status': 'success', 'message': 'Reel sent!'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Not a participant in this thread'}, status=403)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
def create_reel(request):
    if request.method == 'POST':
        video = request.FILES.get('video')
        caption = request.POST.get('caption', '')
        
        if video:
            Reel.objects.create(
                user=request.user,
                video=video,
                caption=caption
            )
            return JsonResponse({'status': 'success'})
            
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def save_reel(request, reel_id):
    """Toggles saving/unsaving a reel for the user"""
    if request.method == 'POST':
        reel = get_object_or_404(Reel, id=reel_id)
        if request.user in reel.saved_by.all():
            reel.saved_by.remove(request.user)
            saved = False
        else:
            reel.saved_by.add(request.user)
            saved = True
            
        return JsonResponse({'status': 'success', 'saved': saved})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def not_interested_reel(request, reel_id):
    """Marks a reel as hidden for the user"""
    if request.method == 'POST':
        reel = get_object_or_404(Reel, id=reel_id)
        reel.hidden_by.add(request.user)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def toggle_follow(request, user_id):
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        current_user = request.user

        # Prevent a user from following themselves
        if current_user == target_user:
            return JsonResponse({'error': 'You cannot follow yourself'}, status=400)

        # Check if a follow relationship already exists
        follow_instance = Follow.objects.filter(follower=current_user, following=target_user).first()

        if follow_instance:
            # If it exists, clicking the button means "Unfollow"
            follow_instance.delete()
            return JsonResponse({'action': 'unfollowed'})
        else:
            # If it doesn't exist, create it!
            # If private, it's pending. If public, it's accepted.
            is_public = getattr(target_user.profile, 'is_public', True)
            status = 'accepted' if is_public else 'pending'
            
            Follow.objects.create(follower=current_user, following=target_user, status=status)
            return JsonResponse({'action': 'followed', 'status': status})

    return JsonResponse({'error': 'Invalid request'}, status=400)