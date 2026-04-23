from .models import AccountBanned
from rest_framework import serializers

class AccountBannedSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountBanned
        fields = ['user', 'reason', 'banned_at', 'is_active']
        read_only_fields = ['reason', 'banned_at', 'user', 'is_active']