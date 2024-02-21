# bp/urls.py
from django.urls import path
from .views import UserCreate, UserSignIn  # Import your view here

urlpatterns = [
    path('api/user/', UserCreate.as_view(), name='user-create'),
    path('api/signin/', UserSignIn.as_view(), name='user-signin'),  # Add your sign-in endpoint here
]
