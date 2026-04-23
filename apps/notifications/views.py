from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import FCMDevice, Notification, NotificationSettings
from apps.notifications.serializers import NotificationSerializer, NotificationSettingsSerializer
from core.pagination import StandardPagination


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    serializer_class = NotificationSerializer

    def get(self, request):
        qs = Notification.objects.filter(recipient=request.user).order_by("-created_at")
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request)
        data = [
            {
                "id": str(n.id),
                "verb": n.verb,
                "notification_type": n.notification_type,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat(),
                "data": n.data,
            }
            for n in page
        ]
        return paginator.get_paginated_response(data)


class NotificationMarkAllReadView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True, is_seen=True)
        cache.set(f"unread_notif:{request.user.id}", 0, timeout=None)
        return Response({"success": True, "data": {}, "message": "Marked read.", "meta": {}})


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def patch(self, request, notification_id):
        n = get_object_or_404(Notification, pk=notification_id, recipient=request.user)
        n.is_read = True
        n.is_seen = True
        n.save(update_fields=["is_read", "is_seen"])
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        cache.set(f"unread_notif:{request.user.id}", count, timeout=None)
        return Response({"success": True, "data": {}, "message": "", "meta": {}})


class NotificationDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def delete(self, request, notification_id):
        n = get_object_or_404(Notification, pk=notification_id, recipient=request.user)
        n.delete()
        return Response({"success": True, "data": {}, "message": "Deleted.", "meta": {}}, status=204)


class NotificationUnreadCountView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def get(self, request):
        c = cache.get(f"unread_notif:{request.user.id}")
        if c is None:
            c = Notification.objects.filter(recipient=request.user, is_read=False).count()
            cache.set(f"unread_notif:{request.user.id}", c, timeout=None)
        return Response({"success": True, "data": {"count": int(c)}, "message": "", "meta": {}})


class NotificationSettingsView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSettingsSerializer

    def put(self, request):
        s, _ = NotificationSettings.objects.get_or_create(user=request.user)
        for field in [
            "email_friend_requests",
            "email_messages",
            "email_posts",
            "push_friend_requests",
            "push_messages",
            "push_posts",
            "push_calls",
        ]:
            if field in request.data:
                setattr(s, field, bool(request.data[field]))
        s.save()
        return Response({"success": True, "data": {}, "message": "Settings saved.", "meta": {}})


class FCMTokenView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response({"success": False, "error": {"code": "REQUIRED", "message": "token required.", "details": {}}}, status=400)
        FCMDevice.objects.filter(token=token).delete()
        FCMDevice.objects.create(
            user=request.user,
            token=token,
            device_id=request.data.get("device_id", ""),
        )
        return Response({"success": True, "data": {}, "message": "Registered.", "meta": {}})
