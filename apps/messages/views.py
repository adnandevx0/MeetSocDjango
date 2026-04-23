from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.messages.models import Conversation, ConversationParticipant, Message, MessageSeen
from apps.messages.serializers import ConversationSerializer, MessageSerializer
from core.pagination import StandardPagination


class ConversationListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    serializer_class = ConversationSerializer

    def get(self, request):
        qs = Conversation.objects.filter(participants=request.user).order_by("-created_at")
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request)
        data = []
        for c in page:
            cp = ConversationParticipant.objects.filter(conversation=c, user=request.user).first()
            data.append(
                {
                    "id": str(c.id),
                    "type": c.conversation_type,
                    "name": c.name,
                    "unread": cp.unread_count if cp else 0,
                    "last_message_id": str(c.last_message_id) if c.last_message_id else None,
                }
            )
        return paginator.get_paginated_response(data)

    def post(self, request):
        ctype = request.data.get("conversation_type", "direct")
        name = request.data.get("name")
        user_ids = request.data.get("participant_ids", [])
        conv = Conversation.objects.create(conversation_type=ctype, name=name)
        ConversationParticipant.objects.create(conversation=conv, user=request.user, role="admin")
        for uid in user_ids:
            from django.contrib.auth import get_user_model

            u = get_user_model().objects.filter(pk=uid).first()
            if u:
                ConversationParticipant.objects.get_or_create(conversation=conv, user=u)
        return Response(
            {"success": True, "data": {"id": str(conv.id)}, "message": "Created.", "meta": {}},
            status=201,
        )


class ConversationDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ConversationSerializer

    def get(self, request, conversation_id):
        conv = get_object_or_404(Conversation, pk=conversation_id, participants=request.user)
        return Response(
            {
                "success": True,
                "data": {
                    "id": str(conv.id),
                    "type": conv.conversation_type,
                    "name": conv.name,
                },
                "message": "",
                "meta": {},
            }
        )

    def put(self, request, conversation_id):
        conv = get_object_or_404(Conversation, pk=conversation_id, participants=request.user)
        conv.name = request.data.get("name", conv.name)
        if request.FILES.get("avatar"):
            conv.avatar = request.FILES["avatar"]
        conv.save()
        return Response({"success": True, "data": {"id": str(conv.id)}, "message": "Updated.", "meta": {}})

    def delete(self, request, conversation_id):
        conv = get_object_or_404(Conversation, pk=conversation_id, participants=request.user)
        ConversationParticipant.objects.filter(conversation=conv, user=request.user).delete()
        return Response({"success": True, "data": {}, "message": "Left.", "meta": {}}, status=204)


class MessageListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer
    pagination_class = StandardPagination

    def get(self, request, conversation_id):
        conv = get_object_or_404(Conversation, pk=conversation_id, participants=request.user)
        qs = Message.objects.filter(conversation=conv, is_deleted=False).order_by("-created_at")
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request)
        data = [
            {
                "id": str(m.id),
                "sender_id": str(m.sender_id),
                "message_type": m.message_type,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
            }
            for m in page
        ]
        return paginator.get_paginated_response(data)

    def post(self, request, conversation_id):
        conv = get_object_or_404(Conversation, pk=conversation_id, participants=request.user)
        m = Message.objects.create(
            conversation=conv,
            sender=request.user,
            message_type=request.data.get("message_type", "text"),
            content=request.data.get("content", ""),
            media=request.FILES.get("media"),
        )
        conv.last_message = m
        conv.save(update_fields=["last_message"])
        return Response(
            {
                "success": True,
                "data": {"id": str(m.id)},
                "message": "Sent.",
                "meta": {},
            },
            status=201,
        )


class MessageDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer

    def delete(self, request, message_id):
        m = get_object_or_404(Message, pk=message_id, sender=request.user)
        m.is_deleted = True
        m.save(update_fields=["is_deleted"])
        return Response({"success": True, "data": {}, "message": "Deleted.", "meta": {}}, status=204)

    def put(self, request, message_id):
        m = get_object_or_404(Message, pk=message_id, sender=request.user)
        m.content = request.data.get("content", m.content)
        m.is_edited = True
        m.save()
        return Response({"success": True, "data": {"id": str(m.id)}, "message": "Updated.", "meta": {}})


class MessageReactView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer

    def post(self, request, message_id):
        m = get_object_or_404(Message, pk=message_id)
        reactions = m.reactions or {}
        emoji = request.data.get("emoji", "like")
        reactions[emoji] = reactions.get(emoji, 0) + 1
        m.reactions = reactions
        m.save(update_fields=["reactions"])
        return Response({"success": True, "data": m.reactions, "message": "", "meta": {}})


class ConversationMemberView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def post(self, request, conversation_id):
        conv = get_object_or_404(Conversation, pk=conversation_id, participants=request.user)
        uid = request.data.get("user_id")
        from django.contrib.auth import get_user_model

        u = get_object_or_404(get_user_model(), pk=uid)
        ConversationParticipant.objects.get_or_create(conversation=conv, user=u)
        return Response({"success": True, "data": {}, "message": "Member added.", "meta": {}})

    def delete(self, request, conversation_id, user_id=None):
        conv = get_object_or_404(Conversation, pk=conversation_id, participants=request.user)
        uid = user_id or request.data.get("user_id")
        if not uid:
            return Response(status=400)
        ConversationParticipant.objects.filter(conversation=conv, user_id=uid).delete()
        return Response({"success": True, "data": {}, "message": "Removed.", "meta": {}}, status=204)


class OnlineStatusView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def get(self, request):
        from django.core.cache import cache

        ids = request.query_params.get("ids", "")
        out = {}
        for i in ids.split(","):
            if not i:
                continue
            out[i] = bool(cache.get(f"online:{i}"))
        return Response({"success": True, "data": out, "message": "", "meta": {}})
