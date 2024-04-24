from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User, PlayerUser, PlayerCategories, Review, Conversation, MediaFiles, PushStatus
from .serializers import UserSerializer, PlayerUserSerializer, PlayerCategoriesSerializer, PlayerCategoriesWithPlayerSerializer, ReviewSerializer, ReviewReadSerializer
from rest_framework.generics import UpdateAPIView
from rest_framework.parsers import MultiPartParser, FormParser
import boto3
from django.conf import settings
import uuid
from django.db.models import Q
import base64
from django.http import QueryDict, JsonResponse
import logging
import json
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import ChatGrant
from twilio.rest import Client
import subprocess
from django.core.files.base import ContentFile
import requests
from exponent_server_sdk import (
    DeviceNotRegisteredError,
    PushClient,
    PushMessage,
    PushServerError,
    PushTicketError,
)

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
            # If authentication fails, return an error response
            return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
#Coach update profile
        
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
                    # Delete the old file from S3 if it exists
                    old_media_url = getattr(user, key)  # Assuming the model has media1, media2, media3 fields with URLs
                    if old_media_url:
                        old_file_key = old_media_url.replace(f"https://{bucket_name}.s3.amazonaws.com/", "")
                        s3_client.delete_object(Bucket=bucket_name, Key=old_file_key)

                    # Upload new file
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

        serializer = UserSerializer(user, data=request.data, partial=True)  # Use the updated data with new media URLs
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

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
        
# Player update profile
        
class PlayerUserUpdate(APIView):
    def patch(self, request, pk, format=None):
        player_user = get_object_or_404(PlayerUser, pk=pk)
        
        # Create a mutable copy of request.data
        data = request.data
        photo = request.FILES.get('photo')
        if photo:
            try:
                s3_client = boto3.client('s3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name='us-east-1')
                bucket_name = settings.AWS_STORAGE_BUCKET_NAME
                # Delete the old photo from S3 if it exists
                old_photo_url = player_user.photo
                if old_photo_url:
                    old_file_key = old_photo_url.replace(f"https://{bucket_name}.s3.amazonaws.com/", "")
                    s3_client.delete_object(Bucket=bucket_name, Key=old_file_key)

                # Upload new photo
                unique_file_name = f"uploads/{uuid.uuid4()}_{photo.name}"
                s3_client.upload_fileobj(
                    photo,
                    bucket_name,
                    unique_file_name,
                    ExtraArgs={'ACL': 'public-read'}
                )
                media_url = f"https://{bucket_name}.s3.amazonaws.com/{unique_file_name}"
                request.data['photo'] = media_url  # Update the mutable copy with the new photo URL
            except Exception as e:
                logger.error(f"Failed to upload photo to S3: {e}", exc_info=True)
                return Response({"error": "Failed to upload photo to S3"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Use the updated data for serialization
        serializer = PlayerUserSerializer(player_user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

# Create reviews, and show reviews on Coach Profile page

class CreateReview(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ReadReviews(APIView):
    def get(self, request, user_id, format=None):
        reviews = Review.objects.filter(user=user_id)
        serializer = ReviewReadSerializer(reviews, many=True)
        return Response(serializer.data)

#Twilio 
        
def generate_token(request, id):
    try:
        logger.info("Starting token generation process")

        account_sid = settings.TWILIO_ACCOUNT_SID
        logger.info(f"Using Account SID: {account_sid}")
        
        api_key = settings.TWILIO_API_KEY
        api_secret = settings.TWILIO_API_KEY_SECRET
        logger.info("API Key and Secret retrieved")

        # Required for Chat grants
        service_sid = settings.TWILIO_CHAT_SERVICE_SID
        logger.info('GENERATE TOKEN: ' + id)
        identity = id
        logger.info(f"Service SID: {service_sid}, Identity: {identity}")

        # Log before creating the token
        logger.info("Creating access token")

        token = AccessToken(account_sid, api_key, api_secret, identity=identity)

        # Log after token creation
        logger.info("Access token created successfully")

        #fcm_token = settings.FCM_CREDENTIAL_SID
        #logger.info('FCM: ' + fcm_token)
        # Create a Chat grant and add to token
        #pushCredential = settings.APN_CREDENTIAL_SID
        chat_grant = ChatGrant(service_sid=service_sid) #push_credential_sid=pushCredential)
        token.add_grant(chat_grant)

        logger.info("Chat grant added to token")

        jwt_token = token.to_jwt()

        logger.info("JWT token generated successfully")

        return JsonResponse({'access_token': jwt_token})
    except Exception as e:
        logger.error(f"Error generating token: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])    
def initiateOrFetchConversation(request):
    try:
        # Extract user IDs from the request
        data = json.loads(request.body)
        player_id = data.get('userID')
        coach_id = data.get('coachID')
        notificationsEnabled = data.get('notificationsEnabled')
        deviceType = data.get('deviceType')
        pushToken = data.get('token')

        # Fetch users from the database
        #player = PlayerUser.objects.get(id=player_id)
        #coach = User.objects.get(id=coach_id)

        # Construct Twilio identities using the specified naming convention
        player_identity = f"{player_id}_player"
        coach_identity = f"{coach_id}_coach"

        # Check if a conversation between the player and coach already exists
        existing_conversation = Conversation.objects.filter(
            player_id=player_identity, 
            coach_id=coach_identity
        ).first()

        # If the conversation exists, return its SID
        if existing_conversation:
            logger.info('retrieving convo')
            return JsonResponse({'conversationSid': existing_conversation.conversation_sid})

        # Initialize Twilio client
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        client = Client(account_sid, auth_token)

        # Create a new conversation
        conversation = client.conversations \
                             .v1 \
                             .conversations \
                             .create(friendly_name='Friendly Conversation')
        

        '''if notificationsEnabled == 'yes':
            participant = client.conversations.conversations(conversation.sid) \
            .participants \
            .create(identity='user_identity', 
                    messaging_binding_address='device_address', 
                    messaging_binding_proxy_address='proxy_address')
            print(participant.sid)'''


            # Add both users as participants (example uses the user's phone number as identity)
        client.conversations \
            .v1 \
            .conversations(conversation.sid) \
            .participants \
            .create(identity=coach_identity)  # Adjust attribute as necessary

        client.conversations \
            .v1 \
            .conversations(conversation.sid) \
            .participants \
            .create(identity=player_identity)  # Adjust attribute as necessary

        
        Conversation.objects.create(
            player_id=player_identity,
            coach_id=coach_identity,
            conversation_sid=conversation.sid
        )

        logger.info('new convo')
        # Return the conversation SID to the frontend
        return JsonResponse({'conversationSid': conversation.sid})

    except Exception as e:
        # Handle errors
        return JsonResponse({'error': str(e)}, status=500)
    
class MediaMessageAPI(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES['file']
        conversation_sid = request.data.get('conversation_sid')

        file_extension = file_obj.name.split('.')[-1]
        logger.info(file_extension.lower())
        if file_extension.lower() in ['mov', 'quicktime', 'MOV']:
            # Convert video to mp4
            output_name = f"{file_obj.name.split('.')[0]}.mp4"
            output_path = f"/tmp/{output_name}"
            command = ['ffmpeg', '-y', '-i', file_obj.temporary_file_path(), '-preset', 'fast', '-crf', '28', '-c:v', 'libx264', '-c:a', 'aac', '-b:a', '192k', output_path]
            subprocess.run(command, check=True)
            # Reassign file_obj to the new file
            with open(output_path, 'rb') as f:
                file_obj = ContentFile(f.read(), name=output_name)

        
        # Upload to S3
        s3_client = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY, region_name='us-east-1')
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME2
        unique_file_name = f"uploads/{uuid.uuid4()}_{file_obj.name}"
        s3_client.upload_fileobj(
            file_obj,
            bucket_name,
            unique_file_name,
            ExtraArgs={'ACL': 'public-read'}
        )
        media_url = f"https://{bucket_name}.s3.amazonaws.com/{unique_file_name}"

        # Save to database
        MediaFiles.objects.create(conversation_sid=conversation_sid, s3url=media_url)

        # Return the URL
        return JsonResponse({"url": media_url}, status=201)
    
@csrf_exempt
@require_http_methods(["POST"])
def savePushToken(request):
    try:
        data = json.loads(request.body)
        user_id = data.get('userId')
        push_token = data.get('pushToken')
        deviceType = data.get('deviceType')

        # Check if the entry already exists or update the existing one
        PushStatus.objects.update_or_create(
            user_id=user_id,
            defaults={'push_token': push_token},
            deviceType=deviceType,
        )

        return JsonResponse({'status': 'success', 'message': 'Push token saved successfully'}, status=201)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)    

@csrf_exempt
def send_notification(request):
    try:
        data = json.loads(request.body)
        user_id = data.get('userId')
        conversation_sid = data.get('conversationSid')

        # Check if conversation SID exists
        conversation = Conversation.objects.filter(conversation_sid=conversation_sid).first()
        if not conversation:
            return JsonResponse({'status': 'error', 'message': 'Conversation not found'}, status=404)

        # Determine the other party's ID
        other_user_id = conversation.coach_id if user_id == conversation.player_id else conversation.player_id
        logger.info('OTHER: ' + other_user_id)
        # Check for the other party's push status
        push_status = PushStatus.objects.filter(user_id=other_user_id).first()
        if not push_status or not push_status.push_token:
            return JsonResponse({'status': 'error', 'message': 'No push token available for the user'}, status=404)

        # Prepare and send the push notification
        push_token = push_status.push_token
        if not push_token.startswith('ExponentPushToken['):
            push_token = f'ExponentPushToken[{push_token}]'

        logger.info('PUSH TOK ' + push_token)
        device_type = push_status.deviceType
        message_text = "You have a new message!"  # Customizable message text

        # Send push notification according to the device type
        response = PushClient().publish(
            PushMessage(to=push_token,
                        body=message_text,
                        data={"extra": "data"})
        )

        # Check for errors in the response and return appropriate response
        if response.errors:
            return JsonResponse({'status': 'error', 'message': str(response.errors)}, status=500)
        
        return JsonResponse({'status': 'success', 'message': 'Notification sent successfully'}, status=200)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@csrf_exempt
@require_http_methods(["POST"])
def updateStatus(request):
    try:
        data = json.loads(request.body)
        user_id = data.get('userId')
        status = data.get('status')

        if not user_id or not status:
            return JsonResponse({'status': 'error', 'message': 'Missing userId or status'}, status=400)

        # Update or create the entry with the user_id and status
        PushStatus.objects.update_or_create(
            user_id=user_id,
            defaults={'status': status}
        )

        return JsonResponse({'status': 'success', 'message': 'Status updated successfully'}, status=201)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
'''
@csrf_exempt
@require_http_methods(["POST"])
def push_notifications(request):
    try:
        # Parse the incoming JSON to get the FCM token
        data = json.loads(request.body)
        fcm_token = data['fcmToken']
        user_identity = data['userIdentity']  # Assuming the identity is also sent
        logger.info('FCM IN PLAY')
        # Twilio setup
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        service_sid = settings.TWILIO_CHAT_SERVICE_SID

        client = Client(account_sid, auth_token)
        
        # Create a binding between the user and the FCM token
        binding = client.notify.services(service_sid).bindings.create(
            identity=user_identity,
            binding_type='fcm',
            address=fcm_token,
        )
        ('FCM WORKING')
        # Return a success response
        return JsonResponse({"message": "FCM token registered successfully", "binding_sid": binding.sid}, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
'''



'''@csrf_exempt
def bind_user_to_notifications(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('userID')
            user_type = data.get('userType')
            token = data.get('pushToken')
            device_type = data.get('deviceType')  # Retrieve device type from POST data


            # Twilio credentials from environment variables or settings
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
            service_sid = settings.TWILIO_CHAT_SERVICE_SID

            # Initialize Twilio client
            client = Client(account_sid, auth_token)

            # Determine binding type based on device type
            if device_type == 'ios':
                binding_type = 'apn'  # Apple Push Notification service
            elif device_type == 'android':
                binding_type = 'gcm'  # Google Cloud Messaging service, or 'fcm' for Firebase Cloud Messaging
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid device type'}, status=400)

            # Create binding to Twilio
            binding = client.conversations.services(service_sid).bindings.create(
                identity=f"{user_id}_{user_type}",  # Identity as a combination of user_id and user_type
                binding_type=binding_type,  # For Apple Push Notification service
                address=token
                #tag=[user_type]  # Optional: Use tags for segmenting notifications
            )

            logger.info('prebind')

            identity = f"{user_id}_{user_type}"
            logger.info('user:' + identity)
            binding = client.conversations.services(service_sid) \
            .bindings \
            .create(identity=identity, 
                    binding_type=binding_type, 
                    address=token
                    #tag=['premium_user']
                    )
            
            logger.info(binding.sid)
            logger.info('BINDINGGGGGGGG')


            return JsonResponse({'status': 'success', 'message': 'User bound to notifications', 'binding_sid': binding.sid}, status=201)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)'''