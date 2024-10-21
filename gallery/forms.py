from django import forms
# from django.contrib.auth.models import User
from .models import Photo
from .models import CustomUser
class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ['username', 'password']

class PhotoUploadForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['image']