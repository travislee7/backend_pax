from django.db import models
from django.core.validators import MinLengthValidator
from django.contrib.postgres.fields import ArrayField

class User(models.Model):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, unique=True)  
    password = models.CharField(max_length=50)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    media1 = models.CharField(max_length=500, null=True, blank=True)
    media2 = models.CharField(max_length=500, null=True, blank=True)
    media3 = models.CharField(max_length=500, null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    bio = models.CharField(max_length=1000, null=True, blank=True)  
    coach_category = models.CharField(max_length=100, null=True, blank=True)
    #coach_category = ArrayField(models.CharField(max_length=100), blank=True, null=True)

    def __str__(self):
        return self.email

class PlayerUser(models.Model):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, unique=True)  
    password = models.CharField(max_length=50)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    location = models.CharField(max_length=100, null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    photo = models.CharField(max_length=500, null=True, blank=True)  

    def __str__(self):
        return self.email

class PlayerCategories(models.Model):
    player = models.ForeignKey(PlayerUser, on_delete=models.CASCADE, related_name='player_categories')
    category = models.CharField(max_length=100)
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Optional budget field
    description = models.CharField(max_length=500, null=True, blank=True, validators=[MinLengthValidator(30)])

    def __str__(self):
        return f"Categories for {self.player.email}"

#Twilio conversations
class Conversation(models.Model):
    player_id = models.CharField(max_length=255)
    coach_id = models.CharField(max_length=255)
    conversation_sid = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.player_id} <-> {self.coach_id}"
    
#Twilio media/doc file messages
class MediaFiles(models.Model):
    conversation_sid = models.CharField(max_length=255)
    s3url = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.s3url

#User's app state for push notifications
class PushStatus(models.Model):
    user_id = models.CharField(max_length=255)
    push_token = models.CharField(max_length=255, null=True, blank=True)
    deviceType = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255, null=True, blank=True)  # Optional status field


    def __str__(self):
        return self.user_id
    
'''class UnreadPushCount(models.Model):
    player_id = models.CharField(max_length=255)
    unreadPushFromPlayer = models.IntegerField(default=0)
    coach_id = models.CharField(max_length=255)
    unreadPushFromCoach = models.IntegerField(default=0)
    category = models.CharField(max_length=100)'''



    
class StripeAccounts(models.Model):
    coach = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coach_stripe_account_id')
    stripe_account_id = models.CharField(max_length=255, null=True, blank=True)


class TransactionHistory(models.Model):
    player_id = models.CharField(max_length=255)
    coach_id = models.CharField(max_length=255)
    transaction_amount = models.IntegerField(null=True, blank=True)  # Adjust max_digits as needed

    def __str__(self):
        return f'{self.player_id} paid {self.coach_id} ${self.transaction_amount}'

class ReviewStatus(models.Model):
    player_id = models.CharField(max_length=255)
    coach_id = models.CharField(max_length=255)
    charge_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')

class Reviews(models.Model):
    player_id = models.CharField(max_length=255)
    coach_id = models.CharField(max_length=255)
    coach_first_name = models.CharField(max_length=100)
    coach_last_name = models.CharField(max_length=100)
    rating = models.IntegerField()
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'Review for {self.coach_first_name} {self.coach_last_name} by {self.player_id}'
    


