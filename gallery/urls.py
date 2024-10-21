from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('', views.home_view, name='home'),
    path('upload/', views.upload_photo_view, name='upload_photo'),
    path('photos/', views.view_photos, name='view_photos'),
]