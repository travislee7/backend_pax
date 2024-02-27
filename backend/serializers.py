from rest_framework import serializers
from .models import User, PlayerUser, PlayerCategories

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'phone_number', 'password', 'first_name', 'last_name', 'media1', 'media2', 'media3', 'location', 'age', 'bio']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Check if email or phone number already exists
        if User.objects.filter(email=validated_data['email']).exists():
            raise serializers.ValidationError({'email': 'This email is already in use.'})
        if User.objects.filter(phone_number=validated_data['phone_number']).exists():
            raise serializers.ValidationError({'phone_number': 'This phone number is already in use.'})
        
        # Create new user
        user = User.objects.create(**validated_data)
        return user


class PlayerUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerUser
        fields = ['id', 'email', 'phone_number', 'password', 'first_name', 'last_name', 'location', 'age', 'photo']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        if PlayerUser.objects.filter(email=validated_data['email']).exists():
            raise serializers.ValidationError({'email': 'This email is already in use.'})
        if PlayerUser.objects.filter(phone_number=validated_data['phone_number']).exists():
            raise serializers.ValidationError({'phone_number': 'This phone number is already in use.'})
        
        # Here, add hashing for password or any additional logic
        player_user = PlayerUser.objects.create(**validated_data)
        return player_user
    
class PlayerCategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerCategories
        fields = '__all__'

