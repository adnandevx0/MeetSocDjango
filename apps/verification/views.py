from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.verification.models import BlueVerificationRequest
from apps.verification.serializers import BlueVerificationRequestSerializer


class BlueVerificationApplyView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BlueVerificationRequestSerializer

    def post(self, request):
        pending = BlueVerificationRequest.objects.filter(
            user=request.user,
            status="pending",
        ).exists()
        if pending:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "ALREADY_PENDING",
                        "message": "A verification request is already pending.",
                        "details": {},
                    },
                },
                status=400,
            )
        obj = BlueVerificationRequest.objects.create(
            user=request.user,
            note=request.data.get("note", ""),
            status="pending",
        )
        return Response(
            {
                "success": True,
                "data": BlueVerificationRequestSerializer(obj).data,
                "message": "Verification request submitted.",
                "meta": {},
            },
            status=201,
        )


class BlueVerificationMyStatusView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BlueVerificationRequestSerializer

    def get(self, request):
        latest = (
            BlueVerificationRequest.objects.filter(user=request.user)
            .order_by("-created_at")
            .first()
        )
        active = BlueVerificationRequest.get_active_for_user(request.user)
        return Response(
            {
                "success": True,
                "data": {
                    "has_blue_badge": bool(active),
                    "badge_valid_until": active.valid_until if active else None,
                    "latest_request": BlueVerificationRequestSerializer(latest).data if latest else None,
                },
                "message": "",
                "meta": {},
            }
        )
