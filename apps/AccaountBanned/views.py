from django.shortcuts import render
from requests import Response
from .models import AccountBanned
from .serializers import AccountBannedSerializer
# Create your views here.

def banned_accountsAPi(request):
    banned_accounts = AccountBanned.objects.filter(is_active=True)
    serializer = AccountBannedSerializer(banned_accounts, many=True)
    return Response(serializer.data)

