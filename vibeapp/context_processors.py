# context_processors.py
from .models import Notification

def user_notifications(request):
    """
    This makes the 'notifications' variable available globally 
    in all HTML templates, including your sidebar/sliding panel.
    """
    if request.user.is_authenticated:
        # Fetch notifications where the logged-in user is the receiver
        notifications = Notification.objects.filter(receiver=request.user).order_by('-created_at')
        
        # We return a dictionary. The key 'notifications' matches the 
        # {% for notif in notifications %} loop in your HTML.
        return {'notifications': notifications}
    
    # If the user is not logged in (e.g., on the login page), return an empty list
    return {'notifications': []}