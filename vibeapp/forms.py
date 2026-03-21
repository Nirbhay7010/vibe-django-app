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
        # Ensure 'is_public' and 'location' are included to match your model and settings page
        fields = ['profile_image', 'bio', 'website', 'location', 'is_public'] 
        
        widgets = {
            'bio': forms.Textarea(attrs={'placeholder': 'Update your bio...'}),
            'website': forms.URLInput(attrs={'placeholder': 'https://yourwebsite.com'}),
            'location': forms.TextInput(attrs={'placeholder': 'Update location...'}),
            # The checkbox styling is handled by the CSS in setting.html
            'is_public': forms.CheckboxInput(),
        }