from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('OWNER', 'Shop Owner'),
        ('STAFF', 'Staff Member'),
        ('SHOPZEN_ADMIN', 'ShopZen Admin'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    business = models.ForeignKey('businesses.Business', on_delete=models.SET_NULL, null=True, blank=True, related_name='staff_members')
    phone = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='OWNER')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"
