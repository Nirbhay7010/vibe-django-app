from django.shortcuts import redirect
from django.urls import reverse

class ProfileSetupMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # Only run if user is logged in
        if request.user.is_authenticated:

            profile = request.user.profile

            # If profile NOT completed
            if not profile.is_completed:

                allowed_urls = [
                    reverse('profilesetup'),
                    reverse('logout'),
                ]

                # If user tries to access anything else
                if request.path not in allowed_urls:
                    return redirect('profilesetup')

        # Continue normal request
        return self.get_response(request)
