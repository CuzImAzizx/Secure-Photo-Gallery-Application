from django import forms
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