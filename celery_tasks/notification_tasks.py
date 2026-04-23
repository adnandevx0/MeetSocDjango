import logging

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.core.cache import cache

from apps.notifications.models import Notification

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task
def send_fcm_push_task(device_tokens, title, body, data):
    if not device_tokens:
        return
    try:
        from pyfcm import FCMNotification
        from django.conf import settings

        api_key = getattr(settings, "FCM_SERVER_KEY", "") or ""
        if not api_key:
            logger.warning("FCM_SERVER_KEY not set; skipping push")
            return
        push_service = FCMNotification(api_key=api_key)
        for token in device_tokens:
            push_service.notify_single_device(
                registration_id=token,
                message_title=title,
                message_body=body,
                data_message=data or {},
            )
    except Exception:
        logger.exception("send_fcm_push_task failed")


@shared_task(bind=True, max_retries=3)
def send_notification_task(self, recipient_id, notif_data):
    try:
        recipient = User.objects.get(pk=recipient_id)
        n = Notification.objects.create(
            recipient=recipient,
            actor_id=notif_data.get("actor_id"),
            notification_type=notif_data.get("notification_type", "message"),
            verb=notif_data.get("verb", ""),
            data=notif_data.get("data", {}),
        )
        channel_layer = get_channel_layer()
        group = f"notification_user_{recipient_id}"
        payload = {
            "type": "notify",
            "notification": {
                "id": str(n.id),
                "verb": n.verb,
                "notification_type": n.notification_type,
                "data": n.data,
                "created_at": n.created_at.isoformat(),
            },
        }
        async_to_sync(channel_layer.group_send)(group, payload)
        count = Notification.objects.filter(recipient=recipient, is_read=False).count()
        cache.set(f"unread_notif:{recipient_id}", count, timeout=None)
        async_to_sync(channel_layer.group_send)(
            group,
            {"type": "unread_count", "count": count},
        )
        send_fcm_push_task.delay(
            list(recipient.fcm_devices.values_list("token", flat=True)),
            notif_data.get("title", "MeetSoc"),
            notif_data.get("body", n.verb),
            notif_data.get("data", {}),
        )
    except Exception as exc:
        logger.exception("send_notification_task failed")
        raise self.retry(exc=exc, countdown=30)
