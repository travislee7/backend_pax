# bp/urls.py
from django.urls import path
from .views import UserCreate  # Import your view here

urlpatterns = [
    path('api/user/', UserCreate.as_view(), name='user-create'),
    # Remove the recursive include statement
]
