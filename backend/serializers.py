from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'phone_number', 'password', 'first_name', 'last_name', 'photo', 'location', 'age']
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