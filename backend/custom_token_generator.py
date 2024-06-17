from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six

class CustomTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        is_active = getattr(user, 'is_active', True)  # Default to True if is_active is missing
        return (
            six.text_type(user.pk) + six.text_type(timestamp) +
            six.text_type(is_active)
        )

custom_token_generator = CustomTokenGenerator()
