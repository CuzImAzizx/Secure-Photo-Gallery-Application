from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.http import HttpResponse

#from django.contrib.auth.models import User
from .models import CustomUser # Import your custom user model

from .forms import UserRegistrationForm, PhotoUploadForm
from .models import Photo
from django.contrib import messages
import os
#from cryptography.fernet import Fernet
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
import secrets


# AES Encryption settings
# KEY = os.urandom(16)
def encrypt_aes(data: bytes, key: bytes) -> bytes:
    """Encrypt data using AES."""
    iv = os.urandom(16)  # Generate a random IV
    key_bytes = key.encode('utf-8')  
    cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # Pad the data to make it a multiple of the block size
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(data) + padder.finalize()

    # Encrypt the data
    encrypted_data = iv + encryptor.update(padded_data) + encryptor.finalize()
    return encrypted_data


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'gallery/login.html')

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            
            user.key = base64.b64encode(os.urandom(32)).decode('utf-8')

            user.save()
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'gallery/register.html', {'form': form})

def home_view(request):
    if request.user.is_authenticated:
        return render(request, 'gallery/home.html')
    return redirect('login')

def upload_photo_view(request):
    if request.method == 'POST':
        form = PhotoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            image_data = form.cleaned_data['image'].read()

            # TODO: Encrypt before saving/storing
            key = request.user.key

            encrypted_image = encrypt_aes(image_data, key)

            photo = Photo(user=request.user, encrypted_image=encrypted_image)

            # photo.user = request.user
            photo.save()
            return redirect('view_photos')
    else:
        form = PhotoUploadForm()
    return render(request, 'gallery/upload.html', {'form': form})

def view_photos(request):
    photos = Photo.objects.filter(user=request.user)
    return render(request, 'gallery/photos.html', {'photos': photos})