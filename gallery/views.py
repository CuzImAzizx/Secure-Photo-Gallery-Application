from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.http import HttpResponse
from django.core.files.uploadedfile import InMemoryUploadedFile
from datetime import datetime
from .forms import UserRegistrationForm, PhotoUploadForm
from .models import Photo
from django.contrib import messages
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from io import BytesIO
from django.contrib.auth.decorators import login_required

def encrypt_image(data: bytes, key: str) -> bytes:
    """
    Encrypts data using AES encryption.

    Args:
        data (bytes): The data to encrypt.
        key (str): The AES key as a hexadecimal string.

    Returns:
        bytes: The encrypted data, prefixed with the initialization vector (IV).
    """
    iv = os.urandom(16)  # Generate a random IV
    key_bytes = bytes.fromhex(key)
    cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # Pad the data to ensure it is a multiple of the block size
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(data) + padder.finalize()

    # Encrypt the data and prepend the IV
    encrypted_data = iv + encryptor.update(padded_data) + encryptor.finalize()
    return encrypted_data

def decrypt_image(encrypted_data: bytes, key: str) -> bytes:
    """
    Decrypts data using AES encryption.

    Args:
        encrypted_data (bytes): The data to decrypt.
        key (str): The AES key as a hexadecimal string.

    Returns:
        bytes: The decrypted data.
    """
    key_bytes = bytes.fromhex(key)

    # Extract the IV from the beginning of the encrypted data
    iv = encrypted_data[:16]  # First 16 bytes are the IV
    encrypted_content = encrypted_data[16:]  # The rest is the encrypted content

    cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    # Decrypt the data
    padded_data = decryptor.update(encrypted_content) + decryptor.finalize()

    # Unpad the data
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    decrypted_data = unpadder.update(padded_data) + unpadder.finalize()

    return decrypted_data

def login_view(request):
    """
    Handles user login.

    If the user is already authenticated, redirects to the home page.
    If the request method is POST, authenticates the user.
    Displays an error message for invalid credentials.

    Returns:
        HttpResponse: Renders the login page or redirects to home.
    """
    if request.user.is_authenticated:
        return redirect('home')
    
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
    """
    Handles user registration.

    If the user is authenticated, redirects to the home page.
    If the request method is POST, processes the registration form.
    Generates a random AES key for the user upon successful registration.

    Returns:
        HttpResponse: Renders the registration page or redirects to login.
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.key = os.urandom(16).hex()  # Generate a random AES key
            user.save()
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'gallery/register.html', {'form': form})

@login_required
def home_view(request):
    """
    Renders the home page for authenticated users.

    Returns:
        HttpResponse: Renders the home page.
    """
    return render(request, 'gallery/home.html')

@login_required
def upload_photo_view(request):
    """
    Handles photo upload.

    If the request method is POST, processes the upload form.
    Encrypts the uploaded image using AES before saving it to the database.

    Returns:
        HttpResponse: Renders the upload page or redirects to view photos.
    """
    if request.method == 'POST':
        form = PhotoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            
            original_image = form.cleaned_data['image']
            original_image.seek(0)  # Reset file pointer
            
            # Encrypt the image data
            encrypted_image = BytesIO()
            key = request.user.key
            encrypted_data = encrypt_image(original_image.read(), key)
            encrypted_image.write(encrypted_data)
            encrypted_image.seek(0)
            
            # Create an InMemoryUploadedFile for the encrypted image
            image_file = InMemoryUploadedFile(
                file=encrypted_image,
                field_name=None,
                name=datetime.today().__str__() + ".jpeg",
                content_type='image/jpeg',
                size=encrypted_image.getbuffer().nbytes,
                charset=None
            )

            photo = Photo(user=request.user, image=image_file)
            photo.save()
            return redirect('view_photos')
    else:
        form = PhotoUploadForm()
    return render(request, 'gallery/upload.html', {'form': form})

@login_required
def view_photos(request):
    """
    Displays photos uploaded by the authenticated user.

    Decrypts the images for display.

    Returns:
        HttpResponse: Renders the photos page with decrypted images.
    """
    photos = Photo.objects.filter(user=request.user)
    
    decrypted_images = []

    for photo in photos:
        encrypted_data = photo.image.read()  # Read the encrypted image data
        key = request.user.key
        decrypted_image_data = decrypt_image(encrypted_data, key)  # Decrypt the image data

        decrypted_images.append((photo.id, decrypted_image_data))  # Store the ID for reference
    
    return render(request, 'gallery/photos.html', {'photos': decrypted_images})