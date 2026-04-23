from django.db import models
from django.conf import settings


class AccountBanned(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='account_banned')
    reason = models.TextField()
    banned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    

    def __str__(self):
        return f"{self.user.username} - Banned for: {self.reason[:20]}..."