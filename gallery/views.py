from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from .forms import UserRegistrationForm, PhotoUploadForm
from .models import Photo
from django.contrib import messages
import os

# AES Encryption settings
KEY = os.urandom(16)

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
            photo.user = request.user
            photo.save()
            return redirect('view_photos')
    else:
        form = PhotoUploadForm()
    return render(request, 'gallery/upload.html', {'form': form})

def view_photos(request):
    photos = Photo.objects.filter(user=request.user)
    return render(request, 'gallery/photos.html', {'photos': photos})