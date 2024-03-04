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

