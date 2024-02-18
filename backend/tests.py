'''from django.test import TestCase
from rest_framework.exceptions import ValidationError
from .models import User
from .serializers import UserSerializer

class UserSerializerTestCase(TestCase):
    def setUp(self):
        # Create a user to test duplicate entries
        User.objects.create(email='test@example.com', phone_number='1234567890', password='testpassword', first_name='Test', last_name='User', location='Test Location', age=25)

    def test_create_user_successfully(self):
        # Define valid serializer data
        valid_serializer_data = {
            'email': 'newuser@example.com',
            'phone_number': '0987654321',
            'password': 'newpassword',
            'first_name': 'New',
            'last_name': 'User',
            'location': 'New Location',
            'age': 30
        }
        serializer = UserSerializer(data=valid_serializer_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertIsNotNone(user.id)  # Check if the user object was created
        self.assertEqual(User.objects.count(), 2)  # Including the one created in setUp

    def test_create_user_with_existing_email(self):
        # Define serializer data with an existing email
        serializer_data_with_existing_email = {
            'email': 'test@example.com',  # Existing email
            'phone_number': '9876543210',
            'password': 'anotherpassword',
            'first_name': 'Another',
            'last_name': 'User',
            'location': 'Another Location',
            'age': 28
        }
        serializer = UserSerializer(data=serializer_data_with_existing_email)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_create_user_with_existing_phone_number(self):
        # Define serializer data with an existing phone number
        serializer_data_with_existing_phone = {
            'email': 'unique@example.com',
            'phone_number': '1234567890',  # Existing phone number
            'password': 'uniquepassword',
            'first_name': 'Unique',
            'last_name': 'User',
            'location': 'Unique Location',
            'age': 29
        }
        serializer = UserSerializer(data=serializer_data_with_existing_phone)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)'''

