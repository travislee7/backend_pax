from rest_framework import serializers
from .models import User, PlayerUser, PlayerCategories, Review

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'phone_number', 'password', 'first_name', 'last_name', 'media1', 'media2', 'media3', 'location', 'age', 'bio', 'coach_category']
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
    matched_coaches = serializers.SerializerMethodField()

    class Meta:
        model = PlayerCategories
        fields = ['id', 'player', 'category', 'budget', 'description', 'matched_coaches']
    
    def get_matched_coaches(self, obj):
        # Filter User instances where 'coach_category' matches 'obj.category'
        #matched_coaches = User.objects.filter(coach_category=obj.category)
        
        matched_coaches = User.objects.filter(coach_category__icontains=obj.category)

        # You might want to use a simplified User serializer here
        return UserSerializer(matched_coaches, many=True).data
    
class SimplifiedPlayerUserSerializer(serializers.ModelSerializer):
    """
    A simplified version of PlayerUserSerializer to be used for nested serialization
    within PlayerCategoriesWithPlayerSerializer to avoid exposing sensitive fields like password.
    """
    class Meta:
        model = PlayerUser
        fields = ['id', 'email', 'phone_number', 'first_name', 'last_name', 'location', 'age', 'photo']

class PlayerCategoriesWithPlayerSerializer(serializers.ModelSerializer):
    matched_players = serializers.SerializerMethodField()

    class Meta:
        model = PlayerCategories
        fields = ['id', 'category', 'budget', 'description', 'matched_players']

    def get_matched_players(self, obj):
        """
        Dynamically add the PlayerUser data associated with the PlayerCategory instance.
        This method is designed to include player data, enhancing the detail provided for each player category.
        """
        # Directly return the associated PlayerUser data using the SimplifiedPlayerUserSerializer
        return SimplifiedPlayerUserSerializer(obj.player).data

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'playeruser', 'user', 'rating', 'description']


class ReviewReadSerializer(serializers.ModelSerializer):
    playeruser_details = SimplifiedPlayerUserSerializer(source='playeruser', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'playeruser', 'user', 'rating', 'description', 'playeruser_details']
    
    
