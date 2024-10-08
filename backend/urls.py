# bp/urls.py
from django.urls import path
from .views import UserCreate, UserSignIn, PlayerUserCreate, PlayerUserSignIn, PlayerCategoriesCreate, PlayerCategoriesRead, PlayerCategoriesDelete, UserProfileRead, PlayerProfileRead, UserUpdate, MatchedPlayerCategoriesView, PlayerUserUpdate, generate_token, initiateOrFetchConversation, MediaMessageAPI, savePushToken, send_notification, updateStatus, RetrieveStripeAccount, ManageStripeAccount, CreatePaymentIntentView, log_transaction, get_player_past_lessons, get_coach_past_lessons, pending_review, get_reviews_to_do, submit_review, check_pending_reviews, get_coach_reviews, get_unread_player_push_count, mark_player_as_read, get_unread_coach_push_count, mark_coach_as_read, create_unread_push_count, search_coaches, password_reset_request, password_reset_confirm, checkPushStatus, deletePushToken #RefreshStripeOnboarding #bind_user_to_notifications #update_push_configuration

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


    path('generate-token/<str:id>', generate_token, name='generate-token'),
    path('initiate-conversation/', initiateOrFetchConversation, name='initiate-conversation'),

    path('api/media-message/', MediaMessageAPI.as_view(), name='media-message'),

    #path('push-notifications/', push_notifications, name='push-notifications'),
    #path('api/update-push-config/', update_push_configuration, name='update_push_config'),

    #path('api/bind-user/', bind_user_to_notifications, name='bind-user'),
    path('api/check-push-status/', checkPushStatus, name='check-push-status'),
    path('api/delete-push-token/', deletePushToken, name='delete-push-token'),

    path('api/save-push-token/', savePushToken, name='save-token'),
    path('api/send-notification/', send_notification, name='send-notification'),
    path('api/create-unread-push-count/', create_unread_push_count, name='create-unread'),


    path('api/get-unread-player-push-count/', get_unread_player_push_count, name='get-unread-player-push-count'),
    path('api/mark-player-as-read/', mark_player_as_read, name='mark-player-as-read'),

    path('api/get-unread-coach-push-count/', get_unread_coach_push_count, name='get-unread-coach-push-count'),
    path('api/mark-coach-as-read/', mark_coach_as_read, name='mark-coach-as-read'),




    path('api/update-status/', updateStatus, name='update-status'),
    
    path('api/retrieve-stripe-account/<int:coach_id>/', RetrieveStripeAccount.as_view(), name='retrieve-stripe-account'),

    path('api/manage_stripe_account/', ManageStripeAccount.as_view(), name='manage-stripe-account'),

    path('api/create-payment-intent/', CreatePaymentIntentView.as_view(), name='create-payment-intent'),

    path('api/log-transaction/', log_transaction, name='log_transaction'),

    path('api/get-player-past-lessons/', get_player_past_lessons, name='get-player-past-lessons'),
    path('api/get-coach-past-lessons/', get_coach_past_lessons, name='get-coach-past-lessons'),

    path('api/pending-review/', pending_review, name='pending-review'),

    path('api/get-reviews-to-do/<str:player_id>/', get_reviews_to_do, name='get-reviews-to-do'),

    path('api/submit-review/', submit_review, name='submit_review'),
    
    path('api/check-pending-reviews/<int:user_id>/', check_pending_reviews, name='check_pending_reviews'),

    path('api/get-coach-reviews/<int:coach_id>/', get_coach_reviews, name='get_coach_reviews'),

    path('api/search-coaches/', search_coaches, name='search-coaches'),


    path('api/password-reset/', password_reset_request, name='password_reset_request'),
    path('api/password-reset-confirm/', password_reset_confirm, name='password_reset_confirm'),





    #path('api/refresh-stripe/<str:account_id>/', RefreshStripeOnboarding.as_view(), name='refresh-stripe'),


]
