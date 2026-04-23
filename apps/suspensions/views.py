from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.suspensions.models import AccountSuspension
from apps.suspensions.serializers import AccountSuspensionSerializer


class MySuspensionStatusView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AccountSuspensionSerializer

    def get(self, request):
        active = AccountSuspension.get_active_for_user(request.user)
        return Response(
            {
                "success": True,
                "data": {
                    "is_suspended": bool(active),
                    "suspension": AccountSuspensionSerializer(active).data if active else None,
                },
                "message": "",
                "meta": {},
            }
        )


class AdminSuspensionListCreateView(APIView):
    permission_classes = [IsAdminUser]
    serializer_class = AccountSuspensionSerializer

    def get(self, request):
        qs = AccountSuspension.objects.select_related("user", "created_by").order_by("-created_at")[:200]
        return Response(
            {
                "success": True,
                "data": AccountSuspensionSerializer(qs, many=True).data,
                "message": "",
                "meta": {},
            }
        )

    def post(self, request):
        ser = AccountSuspensionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        obj = ser.save(created_by=request.user, status="active")
        return Response(
            {
                "success": True,
                "data": AccountSuspensionSerializer(obj).data,
                "message": "Suspension created.",
                "meta": {},
            },
            status=201,
        )


class AdminSuspensionLiftView(APIView):
    permission_classes = [IsAdminUser]
    serializer_class = AccountSuspensionSerializer

    def post(self, request, suspension_id):
        obj = get_object_or_404(AccountSuspension, pk=suspension_id)
        obj.status = "lifted"
        obj.save(update_fields=["status", "updated_at"])
        return Response({"success": True, "data": {}, "message": "Suspension lifted.", "meta": {}})
