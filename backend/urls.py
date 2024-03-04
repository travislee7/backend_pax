# bp/urls.py
from django.urls import path
from .views import UserCreate, UserSignIn, PlayerUserCreate, PlayerUserSignIn, PlayerCategoriesCreate, PlayerCategoriesRead, PlayerCategoriesDelete, UserProfileRead, PlayerProfileRead, UserUpdate, MatchedPlayerCategoriesView, PlayerUserUpdate

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

]
