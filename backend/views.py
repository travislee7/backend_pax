from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User, PlayerUser, PlayerCategories
from .serializers import UserSerializer, PlayerUserSerializer, PlayerCategoriesSerializer, PlayerCategoriesWithPlayerSerializer
from rest_framework.generics import UpdateAPIView
from rest_framework.parsers import MultiPartParser, FormParser
import boto3
from django.conf import settings
import uuid
from django.db.models import Q
import base64
from django.http import QueryDict
import logging
from django.shortcuts import get_object_or_404



# Coach Signup and signin / upload coach images to aws s3 bucket / patch request for media2 and media3 attributes

class UserCreate(APIView):
    def post(self, request, format=None):
        data = request.data

        try:
            media_files = []
            for key in ['media1', 'media2', 'media3']:
                media_file = request.FILES.get(key)
                if media_file:
                    s3_client = boto3.client(
                        's3',
                        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                        region_name='us-east-1'
                    )
                    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
                    unique_file_name = f"uploads/{uuid.uuid4()}_{media_file.name}"
                    s3_client.upload_fileobj(
                        media_file,  # Ensure this is a file-like object
                        bucket_name,
                        unique_file_name,
                        ExtraArgs={'ACL': 'public-read'}
                    )
                    media_url = f"https://{bucket_name}.s3.amazonaws.com/{unique_file_name}"
                    # Update the request data with the media URL
                    #request.data['media1'] = media_url
                    request.data[key] = media_url
        except Exception as e:
            logger.error(f"Failed to upload image to S3: {e}", exc_info=True)
            return Response({"error": "Failed to upload image to S3"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class UserUpdate(APIView):
    def patch(self, request, pk, format=None):
        user = get_object_or_404(User, pk=pk)
        data = request.data

        try:
            for key in ['media1', 'media2', 'media3']:
                media_file = request.FILES.get(key)
                if media_file:
                    s3_client = boto3.client(
                        's3',
                        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                        region_name='us-east-1'
                    )
                    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
                    unique_file_name = f"uploads/{uuid.uuid4()}_{media_file.name}"
                    s3_client.upload_fileobj(
                        media_file,
                        bucket_name,
                        unique_file_name,
                        ExtraArgs={'ACL': 'public-read'}
                    )
                    media_url = f"https://{bucket_name}.s3.amazonaws.com/{unique_file_name}"
                    request.data[key] = media_url  # Update the data dict with the new media URL
        except Exception as e:
            logger.error(f"Failed to upload image to S3: {e}", exc_info=True)
            return Response({"error": "Failed to upload image to S3"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = UserSerializer(user, data=request.data, partial=True)  # Now using the updated data with new media URLs
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class UserSignIn(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email', None)
        phone_number = request.data.get('phone_number', None)
        password = request.data.get('password', None)

        print("Request data:", request.data)

        # Attempt to retrieve a user by email or phone number
        user = User.objects.filter(Q(email=email) | Q(phone_number=phone_number)).first()

        if user and user.password == password:
            # If credentials are valid, return success response
            return Response({
                'message': 'Sign in successful',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'phone_number': user.phone_number,
                    # Include any other fields you want to return
                }
            }, status=status.HTTP_200_OK)
        else:
            print('hi')
            # If authentication fails, return an error response
            return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

# Player signup and signin
        
logger = logging.getLogger(__name__)

class PlayerUserCreate(APIView):
    def post(self, request, format=None):
        # Initialize data variable from request.data
        data = request.data

        try:
            photo = request.FILES.get('photo')
            if photo:
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name='us-east-1'
                )
                bucket_name = settings.AWS_STORAGE_BUCKET_NAME
                unique_file_name = f"uploads/{uuid.uuid4()}_{photo.name}"
                # You may need to read the file before uploading
                s3_client.upload_fileobj(
                    photo,  # Make sure this is a file-like object
                    bucket_name,
                    unique_file_name,
                    ExtraArgs={'ACL': 'public-read'}
                )
                media_url = f"https://{bucket_name}.s3.amazonaws.com/{unique_file_name}"
                # Use request.data directly to avoid immutability issues
                request.data['photo'] = media_url
        except Exception as e:
            logger.error(f"Failed to upload image to S3: {e}", exc_info=True)
            return Response({"error": "Failed to upload image to S3"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Proceed with serialization and saving
        serializer = PlayerUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PlayerUserSignIn(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        phone_number = request.data.get('phone_number')
        password = request.data.get('password')

        user = PlayerUser.objects.filter(Q(email=email) | Q(phone_number=phone_number)).first()

        if user and user.password == password:  # Consider using hashed passwords
            return Response({
                'message': 'Sign in successful',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'phone_number': user.phone_number,
                    # Add other fields as needed
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
# Player categories CRUD operations
        
class PlayerCategoriesCreate(APIView):
    def post(self, request, format=None):
        serializer = PlayerCategoriesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# Matching algorithm for player view
    
class PlayerCategoriesRead(APIView):
    def get(self, request, player_id, format=None):
        categories = PlayerCategories.objects.filter(player_id=player_id)
        serializer = PlayerCategoriesSerializer(categories, many=True)
        return Response(serializer.data)

class PlayerCategoriesDelete(APIView):
    def delete(self, request, pk, format=None):
        category = PlayerCategories.objects.get(pk=pk)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
#Matching algorithm for coach view

class MatchedPlayerCategoriesView(APIView):
    def get(self, request, user_id):
        # Fetch the User instance
        user = get_object_or_404(User, pk=user_id)
        
        # Split the coach_category string into a list on commas
        coach_categories = user.coach_category.split(',')
        print(coach_categories)
        
        # Initialize an empty list to hold matched PlayerCategory instances
        matched_categories = []
        
        # Iterate through each element of coach_categories
        for category in coach_categories:
            # Strip to ensure no leading/trailing whitespace, if any
            category = category.strip()
            # Filter PlayerCategory instances for the current category
            # and extend the matched_categories list with the results
            current_matches = PlayerCategories.objects.filter(category=category)
            matched_categories.extend(current_matches)
        
        # Serialize the matched PlayerCategory instances
        serializer = PlayerCategoriesWithPlayerSerializer(matched_categories, many=True)
        
        # Return the serialized data
        return Response(serializer.data, status=status.HTTP_200_OK)

# Coach profile characteristics read given id 
    
class UserProfileRead(APIView):
    def get(self, request, pk, format=None):
        try:
            user = User.objects.get(pk=pk)
            serializer = UserSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

# Player profile characteristics read given id 

class PlayerProfileRead(APIView):
    def get(self, request, pk, format=None):
        try:
            user = PlayerUser.objects.get(pk=pk)
            serializer = PlayerUserSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)