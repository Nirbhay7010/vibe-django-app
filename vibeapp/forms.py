from django import forms
from .models import Profile

class ProfileSetupForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_image', 'bio', 'website', 'location']
        widgets = {
            'bio': forms.Textarea(attrs={'placeholder': 'Tell something about yourself...'}),
            'website': forms.URLInput(attrs={'placeholder': 'https://yourwebsite.com'}),
            'location': forms.TextInput(attrs={'placeholder': 'City, Country'}),
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        # Added the notification fields so the settings page can save them
        fields = [
            'profile_image', 'bio', 'website', 'location', 'is_public',
            'notif_likes_comments', 'notif_followers', 'notif_messages'
        ] 
        
        widgets = {
            'bio': forms.Textarea(attrs={'placeholder': 'Update your bio...'}),
            'website': forms.URLInput(attrs={'placeholder': 'https://yourwebsite.com'}),
            'location': forms.TextInput(attrs={'placeholder': 'Update location...'}),
            'is_public': forms.CheckboxInput(),
            
            # Form widgets for the new dynamic toggles
            'notif_likes_comments': forms.CheckboxInput(),
            'notif_followers': forms.CheckboxInput(),
            'notif_messages': forms.CheckboxInput(),
        }