from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User, PlayerUser, PlayerCategories, Conversation, MediaFiles, PushStatus, StripeAccounts, TransactionHistory, ReviewStatus, Reviews, UnreadPushCount
from .serializers import UserSerializer, PlayerUserSerializer, PlayerCategoriesSerializer, PlayerCategoriesWithPlayerSerializer, StripeAccountSerializer
from rest_framework.generics import UpdateAPIView
from rest_framework.parsers import MultiPartParser, FormParser
import boto3
from django.conf import settings
import uuid
from django.db.models import Q
import base64
from django.http import QueryDict, JsonResponse, HttpResponseRedirect
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
import stripe
from django.db.models import Avg
import subprocess
from decimal import Decimal, ROUND_HALF_UP



# Coach Signup and signin / upload coach images to aws s3 bucket / patch request for media2 and media3 attributes

class UserCreate(APIView):
    def post(self, request, format=None):
        data = request.data
        logger.info("Received request data: %s", data)


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
        '''if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)'''

        if serializer.is_valid():
            try:
                serializer.save()
                logger.info("Successfully saved user data: %s", serializer.data)

                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.info('DID NOT SAVE SERIALIZER DATA')
                logger.error(f"Failed to save serializer data: {e}", exc_info=True)
                return Response({"error": "Failed to save user data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Log the serializer errors to help diagnose the problem
            logger.info('STRAIGHT UP SERIALIER ERROR')
            logger.error(f"Serializer errors: {serializer.errors}")
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


#Twilio 
        
def generate_token(request, id):
    try:
        #logger.info("Starting token generation process")

        account_sid = settings.TWILIO_ACCOUNT_SID
        #logger.info(f"Using Account SID: {account_sid}")
        
        api_key = settings.TWILIO_API_KEY
        api_secret = settings.TWILIO_API_KEY_SECRET
        #logger.info("API Key and Secret retrieved")

        # Required for Chat grants
        service_sid = settings.TWILIO_CHAT_SERVICE_SID
        #logger.info('GENERATE TOKEN: ' + id)
        identity = id
        #logger.info(f"Service SID: {service_sid}, Identity: {identity}")

        # Log before creating the token
        #logger.info("Creating access token")

        token = AccessToken(account_sid, api_key, api_secret, identity=identity, ttl=86400)

        # Log after token creation
        #logger.info("Access token created successfully")

        #fcm_token = settings.FCM_CREDENTIAL_SID
        #logger.info('FCM: ' + fcm_token)
        # Create a Chat grant and add to token
        #pushCredential = settings.APN_CREDENTIAL_SID
        chat_grant = ChatGrant(service_sid=service_sid) #push_credential_sid=pushCredential)
        token.add_grant(chat_grant)

        #logger.info("Chat grant added to token")

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
        elif file_extension.lower() in ['doc', 'docx', 'document']:
            output_pdf = f"{file_obj.name.rsplit('.', 1)[0]}.pdf"
            output_pdf_path = f"/tmp/{output_pdf}"
            try:
                subprocess.run(['unoconv', '-f', 'pdf', '-o', output_pdf_path, file_obj.temporary_file_path()], check=True)
                with open(output_pdf_path, 'rb') as f:
                    file_obj = ContentFile(f.read(), name=output_pdf)
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to convert document: {str(e)}")
                return Response({"error": "Failed to convert document to PDF"}, status=500)


        
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
        category_push = data.get('category')

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


        logger.info('WHO ' + user_id)
        logger.info('CAT ' + category_push)
        '''#For push notification badge count
        if user_id == conversation.player_id:
            # Current user is the player, other_user_id is the coach
            unread_status, created = UnreadPushCount.objects.get_or_create(
                coach_id=other_user_id, player_id=user_id, category=category_push,
                defaults={'unreadPushFromPlayer': 'true'}
            )
            if not created:
                unread_status.unreadPushFromPlayer = 'true'
                unread_status.save()
        else:
            # Current user is the coach, other_user_id is the player
            unread_status, created = UnreadPushCount.objects.get_or_create(
                player_id=other_user_id, coach_id=user_id, category=category_push,
                defaults={'unreadPushFromCoach': 'true'}
            )
            if not created:
                unread_status.unreadPushFromCoach = 'true'
                unread_status.save()'''

        # Send push notification according to the device type
        response = PushClient().publish(
            PushMessage(to=push_token,
                        body=message_text,
                        data={"extra": "data"})
        )

        # Check for errors in the response and return appropriate response
        if response.errors:
            logger.info('CONTINUE')
            #return JsonResponse({'status': 'error', 'message': str(response.errors)}, status=500)

        return JsonResponse({'status': 'success', 'message': 'Notification sent successfully'}, status=200)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@csrf_exempt
def create_unread_push_count(request):
        data = json.loads(request.body)
        user_id = data.get('userId')
        conversation_sid = data.get('conversationSid')
        category_push = data.get('category')

        # Check if conversation SID exists
        conversation = Conversation.objects.filter(conversation_sid=conversation_sid).first()
        if not conversation:
            return JsonResponse({'status': 'error', 'message': 'Conversation not found'}, status=404)

        # Determine the other party's ID
        other_user_id = conversation.coach_id if user_id == conversation.player_id else conversation.player_id
        logger.info('OTHER: ' + other_user_id)

        #For push notification badge count
        if user_id == conversation.player_id:
            # Current user is the player, other_user_id is the coach
            unread_status, created = UnreadPushCount.objects.get_or_create(
                coach_id=other_user_id, player_id=user_id, category=category_push,
                defaults={'unreadPushFromPlayer': 'true'}
            )
            if not created:
                unread_status.unreadPushFromPlayer = 'true'
                unread_status.save()
        else:
            # Current user is the coach, other_user_id is the player
            unread_status, created = UnreadPushCount.objects.get_or_create(
                player_id=other_user_id, coach_id=user_id, category=category_push,
                defaults={'unreadPushFromCoach': 'true'}
            )
            if not created:
                unread_status.unreadPushFromCoach = 'true'
                unread_status.save()
        

@require_http_methods(["GET"])
def get_unread_player_push_count(request):
    user_id = request.GET.get('userID')
    player_id = request.GET.get('playerID')
    category = request.GET.get('category')

    if not all([user_id, player_id, category]):
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    user_id += '_coach'
    player_id += '_player'

    #logger.info('C ' + user_id)
    #logger.info('P ' + player_id)
    #logger.info('cat ' + category)
    
    try:
        unread_status = UnreadPushCount.objects.filter(
            coach_id=user_id,
            player_id=player_id,
            category=category
        ).first()

        '''if (unread_status):
            logger.info('obj')
        else:
            logger.info('nah')'''

        logger.info(unread_status.unreadPushFromPlayer)
        if unread_status and unread_status.unreadPushFromPlayer == 'true':
            return JsonResponse({'has_unread': True})
        else:
            return JsonResponse({'has_unread': False})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@csrf_exempt
@require_http_methods(["POST"])
def mark_player_as_read(request):
    # Assuming data is sent as JSON
    data = json.loads(request.body)
    user_id = data.get('userID')
    player_id = data.get('playerID')
    category = data.get('category')

    if not all([user_id, player_id, category]):
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    try:
        # Append suffixes as needed
        user_id = f"{user_id}_coach"
        player_id = f"{player_id}_player"

        logger.info('C ' + user_id)
        logger.info('P ' + player_id)
        logger.info('cat ' + category)        
        # Try to get the UnreadPushCount instance
        unread_status = UnreadPushCount.objects.filter(
            coach_id=user_id,
            player_id=player_id,
            category=category
        ).first()

        if unread_status:
            unread_status.unreadPushFromPlayer = 'false'
            unread_status.save()
            return JsonResponse({'status': 'success', 'message': 'Marked as read successfully'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No matching record found'}, status=404)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@require_http_methods(["GET"])
def get_unread_coach_push_count(request):
    user_id = request.GET.get('userID')
    coach_id = request.GET.get('coachID')
    category = request.GET.get('category')

    if not all([user_id, coach_id, category]):
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    user_id += '_player'
    coach_id += '_coach'

    logger.info('P ' + user_id)
    logger.info('C ' + coach_id)
    logger.info('cat ' + category)
    
    try:
        unread_status = UnreadPushCount.objects.filter(
            coach_id=coach_id,
            player_id=user_id,
            category=category
        ).first()

        if (unread_status):
            logger.info('obj')
        else:
            logger.info('nah')

        #logger.info(unread_status.unreadPushFromPlayer)
        if unread_status and unread_status.unreadPushFromCoach == 'true':
            return JsonResponse({'has_unread': True})
        else:
            return JsonResponse({'has_unread': False})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@csrf_exempt
@require_http_methods(["POST"])
def mark_coach_as_read(request):
    # Assuming data is sent as JSON
    data = json.loads(request.body)
    player_id = data.get('playerID')
    user_id = data.get('userID')
    category = data.get('category')

    if not all([user_id, player_id, category]):
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    #logger.info('C ' + user_id)
    #logger.info('P ' + player_id)
    #logger.info('cat ' + category)

    try:
        # Append suffixes as needed
        user_id = f"{user_id}_coach"
        player_id = f"{player_id}_player"

        logger.info('C ' + user_id)
        logger.info('P ' + player_id)
        logger.info('cat ' + category)        
        # Try to get the UnreadPushCount instance
        unread_status = UnreadPushCount.objects.filter(
            coach_id=user_id,
            player_id=player_id,
            category=category
        ).first()

        if unread_status:
            unread_status.unreadPushFromCoach = 'false'
            unread_status.save()
            return JsonResponse({'status': 'success', 'message': 'Marked as read successfully'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No matching record found'}, status=404)

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
    


class ManageStripeAccount(APIView):
    def post(self, request, *args, **kwargs):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe_account_id = request.data.get('stripe_account_id', '').strip()
        coach_id = request.data.get('coach_id')  # Get coach ID from the request

        logger.info('ACCT: ' + stripe_account_id)
        try:
            if stripe_account_id:
                # Retrieve the existing account
                account = stripe.Account.retrieve(stripe_account_id)
                # Assume need to check if onboarding is complete
                if account.charges_enabled and account.details_submitted:
                    return JsonResponse({'status': 'onboarding_complete', 'account_id': account.id}, status=status.HTTP_200_OK)
                else:
                    # Incomplete onboarding
                    account_link = stripe.AccountLink.create(
                        account=account.id,
                        refresh_url=f"https://connect.stripe.com/setup/c/{account.id}",
                        #return_url=f"https://connect.stripe.com/setup/c/{account.id}",
                        return_url="https://stripe.com/connect",

                        type="account_onboarding"
                    )
                    return JsonResponse({'status': 'onboarding_incomplete', 'url': account_link.url}, status=status.HTTP_202_ACCEPTED)
            else:
                # Create a new account
                new_account = stripe.Account.create(type="express")
                account_link = stripe.AccountLink.create(
                    account=new_account.id,
                    refresh_url=f"https://connect.stripe.com/setup/c/{new_account.id}",
                    #refresh_url=f"http://10.0.0.165:8000/api/refresh-stripe/{new_account.id}/",  # This URL should point to your Django server endpoint
                    #return_url=f"https://connect.stripe.com/setup/c/{new_account.id}",
                    return_url="https://stripe.com/connect",

                    type="account_onboarding"
                )

                StripeAccounts.objects.create(coach_id=coach_id, stripe_account_id=new_account.id)
                return JsonResponse({'status': 'account_created', 'url': account_link.url}, status=status.HTTP_201_CREATED)

        except stripe.error.StripeError as e:
            logger.error(f'Stripe API error: {str(e)}')
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

def redirect_to_app(request):
    return HttpResponseRedirect('performaxxionapp://setup_payments')


class RetrieveStripeAccount(APIView):
    def get(self, request, coach_id):
        try:
            stripe_account = StripeAccounts.objects.get(coach_id=coach_id)
            serializer = StripeAccountSerializer(stripe_account)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except StripeAccounts.DoesNotExist:
            return Response({"message": "Coach ID does not have a Stripe account."}, status=status.HTTP_404_NOT_FOUND)

class CreatePaymentIntentView(APIView):
    def post(self, request, *args, **kwargs):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        logger.info(request.data)
        conversation_sid = request.data.get('conversationSID')
        amount = request.data.get('amount')

        try:
            # Retrieve conversation to find coach ID
            conversation = Conversation.objects.get(conversation_sid=conversation_sid)
            coach_id = conversation.coach_id.replace('_coach', '')
            logger.info(coach_id)

            # Retrieve Stripe account ID
            stripe_account = StripeAccounts.objects.get(coach=coach_id)
            stripe_account_id = stripe_account.stripe_account_id
            logger.info('Str id' + stripe_account_id)


            # Calculate amount and application fee
            amount = int(float(amount) * 100)  # Convert dollars to cents
            logger.info('AMOUNT' + str(amount))

            application_fee = int(float(amount * 0.2))
            total_amount = int(float(amount * 1.1))

            logger.info(type(total_amount))

            logger.info(type(application_fee))

            '''customer = stripe.Customer.create()
            ephemeralKey = stripe.EphemeralKey.create(
                customer=customer['id'],
                stripe_version='2024-04-10',
            )'''
            # Create PaymentIntent
            intent = stripe.PaymentIntent.create(
                amount= total_amount,
                currency='usd',
                #customer=customer['id'],

                application_fee_amount=application_fee,
                automatic_payment_methods={
                    'enabled': True,
                },
                transfer_data={
                    'destination': stripe_account_id,
                }
            )
            logger.info('INTENT')
            return JsonResponse({
                'clientSecret': intent.client_secret,
                'publishableKey': settings.STRIPE_PUBLISHABLE_KEY,
                #'customer': customer.id, 
                #'ephemeralKey': ephemeralKey.secret
            })
        except stripe.error.StripeError as e:
            # Handle Stripe API errors
            logger.info('STRIPE ERROR')
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Handle general errors
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
def log_transaction(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        conversation_sid = data['conversationSid']
        charge_amount = data['chargeAmount']
        charge_amount = round(float(charge_amount) * 1.1, 2)

        try:
            # Fetch conversation data
            conversation = Conversation.objects.get(conversation_sid=conversation_sid)
            # Strip suffixes from player_id and coach_id
            player_id = conversation.player_id.rstrip('_player')
            coach_id = conversation.coach_id.rstrip('_coach')

            # Create a new transaction history record
            TransactionHistory.objects.create(
                player_id=player_id,
                coach_id=coach_id,
                transaction_amount=charge_amount
            )
            return JsonResponse({'status': 'success'}, status=200)
        except Conversation.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Conversation not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def get_player_past_lessons(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_id = data['userID']

        # Fetch all transactions where the user is the player
        transactions = TransactionHistory.objects.filter(player_id=user_id)
        response_data = []

        for transaction in transactions:
            try:
                coach = User.objects.get(pk=transaction.coach_id)
                response_data.append({
                    'first_name': coach.first_name,
                    'last_name': coach.last_name,
                    'transaction_amount': f'${transaction.transaction_amount}'
                })
            except User.DoesNotExist:
                continue  # Skip if no coach found with the id

        return JsonResponse(response_data, safe=False, status=200)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@csrf_exempt
def get_coach_past_lessons(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_id = data['userID']

        # Fetch all transactions where the user is the player
        transactions = TransactionHistory.objects.filter(coach_id=user_id)
        response_data = []

        for transaction in transactions:
            try:
                player = PlayerUser.objects.get(pk=transaction.player_id)
                #modified_amount = transaction.transaction_amount * 10 / 11 * 0.9
                #formatted_amount = f"${modified_amount:.2f}"  # Formats the amount to two decimal places

                modified_amount = transaction.transaction_amount * Decimal('10') / Decimal('11') * Decimal('0.9')
                # Round to two decimal places
                modified_amount = modified_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                formatted_amount = f"${modified_amount:.2f}"  # Formats the amount to two decimal places
                response_data.append({
                    'first_name': player.first_name,
                    'last_name': player.last_name,
                    'transaction_amount': formatted_amount # Rounded for cleanliness
                })
            except PlayerUser.DoesNotExist:
                continue  # Skip if no coach found with the id

        return JsonResponse(response_data, safe=False, status=200)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@csrf_exempt
def pending_review(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        conversation_sid = data['conversationSid']
        charge_amount = data['chargeAmount']
        charge_amount = round(float(charge_amount) * 1.1, 2)
        
        conversation = Conversation.objects.get(conversation_sid=conversation_sid)
        player_id = conversation.player_id.rstrip('_player')
        coach_id = conversation.coach_id.rstrip('_coach')

        ReviewStatus.objects.create(
            player_id=player_id,
            coach_id=coach_id,
            charge_amount=charge_amount
        )

        return JsonResponse({'status': 'success'}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)

def get_reviews_to_do(request, player_id):
    if request.method == 'GET':
        # Fetch all pending reviews for the given player_id
        reviews = ReviewStatus.objects.filter(player_id=player_id, status='pending')
        results = []
        for review in reviews:
            try:
                coach = User.objects.get(pk=review.coach_id)
                results.append({
                    'review_id': review.id,
                    'coach_first_name': coach.first_name,
                    'coach_last_name': coach.last_name,
                    'transaction_amount': review.charge_amount,
                    'coach_id': review.coach_id,
                    'player_id': review.player_id
                })
            except User.DoesNotExist:
                continue  # Handle the case where no coach is found

        return JsonResponse(results, safe=False)  # 'safe=False' for non-dict objects
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def submit_review(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            # Update the ReviewStatus to 'complete'
            review_status = ReviewStatus.objects.get(id=data['review_id'])
            review_status.status = 'complete'
            review_status.save()

            # Create a new Review entry
            Reviews.objects.create(
                player_id=data['player_id'],
                coach_id=data['coach_id'],
                coach_first_name=data['coach_first_name'],
                coach_last_name=data['coach_last_name'],
                rating=data['rating'],
                description=data['description']
            )
            return JsonResponse({'message': 'Review submitted successfully'}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)

def check_pending_reviews(request, user_id):
    if request.method == 'GET':
        # Check for any pending reviews
        pending_reviews = ReviewStatus.objects.filter(player_id=user_id, status='pending').exists()
        
        if pending_reviews:
            return JsonResponse({"hasPending": True}, status=200)
        else:
            return JsonResponse({"hasPending": False}, status=200)
        
def get_coach_reviews(request, coach_id):
    if request.method == 'GET':
        reviews = Reviews.objects.filter(coach_id=coach_id)
        average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        review_list = []
        
        for review in reviews:
            player = PlayerUser.objects.get(pk=review.player_id)
            review_list.append({
                'player_first_name': player.first_name,
                'player_last_name': player.last_name,
                'player_age': player.age,
                'rating': review.rating,
                'description': review.description
            })

        response_data = {
            'average_rating': round(average_rating, 2),
            'reviews': review_list
        }
        
        return JsonResponse(response_data, safe=False)