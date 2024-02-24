# bp/urls.py
from django.urls import path
from .views import UserCreate, UserSignIn, PlayerUserCreate, PlayerUserSignIn, PlayerCategoriesCreate, PlayerCategoriesRead, PlayerCategoriesUpdate, PlayerCategoriesDelete

urlpatterns = [
    path('api/user/', UserCreate.as_view(), name='user-create'),
    path('api/signin/', UserSignIn.as_view(), name='user-signin'),  

    path('api/userplayer/', PlayerUserCreate.as_view(), name='playeruser-create'),
    path('api/signinplayer/', PlayerUserSignIn.as_view(), name='playeruser-signin'),

    path('api/playercategories/create/', PlayerCategoriesCreate.as_view(), name='playercategories-create'),
    path('api/playercategories/read/<int:player_id>/', PlayerCategoriesRead.as_view(), name='playercategories-read'),
    path('api/playercategories/update/<int:pk>/', PlayerCategoriesUpdate.as_view(), name='playercategories-update'),
    path('api/playercategories/delete/<int:pk>/', PlayerCategoriesDelete.as_view(), name='playercategories-delete'), 

]
