from django.db import models

class User(models.Model):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, unique=True)  
    password = models.CharField(max_length=50)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    photo = models.CharField(max_length=500, null=True, blank=True)  # Assuming this will store a URL or file path
    location = models.CharField(max_length=100, null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)

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

    def __str__(self):
        return self.email


class PlayerCategories(models.Model):
    player = models.ForeignKey(PlayerUser, on_delete=models.CASCADE, related_name='player_categories')
    category = models.CharField(max_length=100)

    def __str__(self):
        return f"Categories for {self.user.email}"

