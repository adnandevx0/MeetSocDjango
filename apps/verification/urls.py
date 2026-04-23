from django.urls import path

from apps.verification import views as v

urlpatterns = [
    path("verification/blue/apply/", v.BlueVerificationApplyView.as_view(), name="verification-blue-apply"),
    path("verification/blue/my-status/", v.BlueVerificationMyStatusView.as_view(), name="verification-blue-status"),
]
