from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.calls.models import Call, CallParticipant
from apps.calls.serializers import CallSerializer
from apps.messages.models import Conversation, ConversationParticipant


class CallInitiateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CallSerializer

    def post(self, request):
        conv_id = request.data.get("conversation_id")
        call_type = request.data.get("call_type", "video")
        conv = get_object_or_404(Conversation, pk=conv_id, participants=request.user)
        c = Call.objects.create(
            call_type=call_type,
            caller=request.user,
            conversation=conv,
            status="ringing",
        )
        for p in conv.participants.all():
            CallParticipant.objects.get_or_create(call=c, user=p)
        return Response(
            {
                "success": True,
                "data": {"id": str(c.id), "status": c.status},
                "message": "Call created.",
                "meta": {},
            },
            status=201,
        )


class CallAcceptView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CallSerializer

    def post(self, request, call_id):
        c = get_object_or_404(Call, pk=call_id)
        c.status = "active"
        c.started_at = timezone.now()
        c.save(update_fields=["status", "started_at"])
        CallParticipant.objects.filter(call=c, user=request.user).update(joined_at=timezone.now())
        return Response({"success": True, "data": {"id": str(c.id)}, "message": "Accepted.", "meta": {}})


class CallDeclineView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CallSerializer

    def post(self, request, call_id):
        c = get_object_or_404(Call, pk=call_id)
        c.status = "declined"
        c.save(update_fields=["status"])
        return Response({"success": True, "data": {}, "message": "Declined.", "meta": {}})


class CallEndView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CallSerializer

    def post(self, request, call_id):
        c = get_object_or_404(Call, pk=call_id)
        end = timezone.now()
        c.status = "ended"
        c.ended_at = end
        if c.started_at:
            c.duration = int((end - c.started_at).total_seconds())
        c.save(update_fields=["status", "ended_at", "duration"])
        return Response({"success": True, "data": {}, "message": "Ended.", "meta": {}})


class CallHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CallSerializer

    def get(self, request):
        qs = Call.objects.filter(
            conversation__participants=request.user
        ).order_by("-created_at")[:100]
        data = [
            {
                "id": str(c.id),
                "call_type": c.call_type,
                "status": c.status,
                "duration": c.duration,
                "created_at": c.created_at.isoformat(),
            }
            for c in qs
        ]
        return Response({"success": True, "data": data, "message": "", "meta": {}})


class IceServersView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def get(self, request):
        from django.conf import settings

        ice = [
            {"urls": "stun:stun.l.google.com:19302"},
            {"urls": "stun:stun1.l.google.com:19302"},
        ]
        if settings.TURN_SERVER_URL:
            ice.append(
                {
                    "urls": settings.TURN_SERVER_URL,
                    "username": settings.TURN_USERNAME,
                    "credential": settings.TURN_CREDENTIAL,
                }
            )
        return Response({"success": True, "data": {"ice_servers": ice}, "message": "", "meta": {}})
