from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User, PlayerUser, PlayerCategories
from .serializers import UserSerializer, PlayerUserSerializer, PlayerCategoriesSerializer
import boto3
from django.conf import settings
import uuid
from django.db.models import Q

'''class UserCreate(APIView):
    def post(self, request, format=None):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)'''

# Coach Signup and signin / upload coach images to aws s3 bucket

class UserCreate(APIView):
    def post(self, request, format=None):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            photo = request.FILES.get('photo')
            if photo:
                # Initialize the boto3 client with the AWS region
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name='us-east-1'  # Ensure this is set to your bucket's region
                )
                bucket_name = settings.AWS_STORAGE_BUCKET_NAME

                # Generate a unique file name for the photo to avoid name collisions
                unique_file_name = f"uploads/{uuid.uuid4()}_{photo.name}"

                # Upload the photo to S3
                s3_client.upload_fileobj(
                    photo,
                    bucket_name,
                    unique_file_name,
                    ExtraArgs={'ACL': settings.AWS_DEFAULT_ACL}  # Use the ACL from your settings
                )

                # Construct the URL of the uploaded file
                # Note: Adjust the URL pattern if your bucket is in a region that requires a different URL format
                photo_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{unique_file_name}"

                # Update the serializer data with the photo URL
                serializer.validated_data['photo'] = photo_url

            user = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
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
        
class PlayerUserCreate(APIView):
    def post(self, request, format=None):
        serializer = PlayerUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
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
    
class PlayerCategoriesRead(APIView):
    def get(self, request, player_id, format=None):
        categories = PlayerCategories.objects.filter(player_id=player_id)
        serializer = PlayerCategoriesSerializer(categories, many=True)
        return Response(serializer.data)

class PlayerCategoriesUpdate(APIView):
    def patch(self, request, pk, format=None):
        category = PlayerCategories.objects.get(pk=pk)
        serializer = PlayerCategoriesSerializer(category, data=request.data, partial=True) # partial=True allows partial update
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PlayerCategoriesDelete(APIView):
    def delete(self, request, pk, format=None):
        category = PlayerCategories.objects.get(pk=pk)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

