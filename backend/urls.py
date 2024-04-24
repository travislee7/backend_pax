# bp/urls.py
from django.urls import path
from .views import UserCreate, UserSignIn, PlayerUserCreate, PlayerUserSignIn, PlayerCategoriesCreate, PlayerCategoriesRead, PlayerCategoriesDelete, UserProfileRead, PlayerProfileRead, UserUpdate, MatchedPlayerCategoriesView, PlayerUserUpdate, CreateReview, ReadReviews, generate_token, initiateOrFetchConversation, MediaMessageAPI, savePushToken, send_notification, updateStatus #bind_user_to_notifications #update_push_configuration

urlpatterns = [
    path('api/user/', UserCreate.as_view(), name='user-create'),
    path('api/signin/', UserSignIn.as_view(), name='user-signin'),  
    path('api/user/update/<int:pk>/', UserUpdate.as_view(), name='user-update'),

    path('api/matched-players/<int:user_id>/', MatchedPlayerCategoriesView.as_view(), name='matched-player-profiles'),


    path('api/userplayer/', PlayerUserCreate.as_view(), name='playeruser-create'),
    path('api/signinplayer/', PlayerUserSignIn.as_view(), name='playeruser-signin'),
    path('api/playeruser/update/<int:pk>/', PlayerUserUpdate.as_view(), name='playeruser-update'),

    path('api/playercategories/create/', PlayerCategoriesCreate.as_view(), name='playercategories-create'),
    path('api/playercategories/read/<int:player_id>/', PlayerCategoriesRead.as_view(), name='playercategories-read'),
    #path('api/playercategories/update/<int:pk>/', PlayerCategoriesUpdate.as_view(), name='playercategories-update'),
    path('api/playercategories/delete/<int:pk>/', PlayerCategoriesDelete.as_view(), name='playercategories-delete'), 


    path('api/userprofileread/<int:pk>/', UserProfileRead.as_view(), name='user-profile-read'),  
    path('api/playerprofileread/<int:pk>/', PlayerProfileRead.as_view(), name='user-profile-read'),  

    path('api/reviews/', CreateReview.as_view(), name='create-review'),
    path('api/reviews/<int:user_id>/', ReadReviews.as_view(), name='user-reviews'),

    path('generate-token/<str:id>/', generate_token, name='generate-token'),
    path('initiate-conversation/', initiateOrFetchConversation, name='initiate-conversation'),

    path('api/media-message/', MediaMessageAPI.as_view(), name='media-message'),

    #path('push-notifications/', push_notifications, name='push-notifications'),
    #path('api/update-push-config/', update_push_configuration, name='update_push_config'),

    #path('api/bind-user/', bind_user_to_notifications, name='bind-user'),
    path('api/save-push-token/', savePushToken, name='save-token'),
    path('api/send-notification/', send_notification, name='send-notification'),

    path('api/update-status/', updateStatus, name='update-status'),



]
