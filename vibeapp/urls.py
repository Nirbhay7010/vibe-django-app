from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import ThreadListView, MessageListView

urlpatterns = [
    # ==========================
    # AUTHENTICATION
    # ==========================
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('logout/', views.logoutUser, name='logout'),
    path('post_login_redirect/', views.post_login_redirect, name='post_login_redirect'),

    # ==========================
    # MAIN APP & PROFILES
    # ==========================
    path('', views.Vibe, name='Vibe'),
    path('setup/', views.profilsetup, name='profilesetup'),
    path('settings/', views.setting, name='setting'),
    path('profile/', views.profile, name='profile'),
    path('p/<int:user_id>/', views.user_profile, name='user_profile'),
    path('create_post/', views.create_post, name='create_post'),
    path('delete_post/<int:post_id>/', views.delete_post, name='delete_post'),

    # ==========================
    # FOLLOW SYSTEM
    # ==========================
    # FIXED: This now points to toggle_follow for the AJAX JS to work!
    path('follow/<int:user_id>/', views.toggle_follow, name='toggle_follow'),
    path('unfollow/<int:user_id>/', views.unfollow_user, name='unfollow_user'),
    path('accept/<int:user_id>/', views.accept_request, name='accept_request'),
    path('decline/<int:user_id>/', views.decline_request, name='decline_request'),
    path('remove_follower/<int:user_id>/', views.remove_follower, name='remove_follower'),
    path('profile/<int:user_id>/followers/', views.followers_list, name='followers_list'),
    path('profile/<int:user_id>/following/', views.following_list, name='following_list'),

    # ==========================
    # SEARCH & NOTIFICATIONS
    # ==========================
    path('search/', views.search_results, name='search_results'),
    path('live-search/', views.live_search, name='live_search'),
    path('notifications/read/', views.mark_notifications_as_read, name='mark_notifications_read'),

    # ==========================
    # CHAT & DIRECT MESSAGES
    # ==========================
    path('direct/inbox/', views.inbox_view, name='inbox'),
    path('direct/call/<int:thread_id>/', views.video_call_view, name='video_call_view'), 
    
    # Chat API Endpoints
    path('api/chat/threads/', ThreadListView.as_view(), name='thread-list'),
    path('api/chat/threads/<int:thread_id>/messages/', MessageListView.as_view(), name='message-list'),
    path('api/chat/start/<int:user_id>/', views.get_or_create_thread, name='start-chat'),
    path('api/chat/accept/<int:thread_id>/', views.accept_chat_request, name='accept-chat'),
    path('api/chat/decline/<int:thread_id>/', views.decline_chat_request, name='decline-chat'),
    path('api/chat/<int:thread_id>/upload_image/', views.upload_chat_image, name='upload-chat-image'),

    # ==========================
    # REELS
    # ==========================
    path('reels/', views.reels_feed, name='reels_feed'),
    path('api/reels/create/', views.create_reel, name='create_reel'),
    path('api/reels/<int:reel_id>/like/', views.like_reel, name='like_reel'),
    path('api/reels/<int:reel_id>/comment/', views.add_reel_comment, name='add_reel_comment'),
    path('api/reels/<int:reel_id>/share/<int:thread_id>/', views.share_reel_to_chat, name='share_reel_to_chat'),
    path('api/reels/<int:reel_id>/save/', views.save_reel, name='save_reel'),
    path('api/reels/<int:reel_id>/not-interested/', views.not_interested_reel, name='not_interested_reel'),
    
    # ==========================
    # POST APIs & SUGGESTIONS
    # ==========================
    path('api/posts/<int:post_id>/like/', views.like_post, name='like_post'),
    path('api/posts/<int:post_id>/save/', views.save_post, name='save_post'),
    path('api/posts/<int:post_id>/comment/', views.comment_post, name='comment_post'),
    path('api/posts/<int:post_id>/share/<int:thread_id>/', views.share_post, name='share_post'),
    path('suggestions/', views.suggested_users_view, name='suggested_users'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)