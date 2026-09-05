from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    extension = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.username

    # Create your models here.
