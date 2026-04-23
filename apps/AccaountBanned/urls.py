from .views import banned_accountsAPi
from django.urls import path

urlpatterns = [
    path('banned-accounts/', banned_accountsAPi, name='banned_accounts_api'),
]