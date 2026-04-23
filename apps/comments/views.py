from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comments.models import Comment
from apps.comments.serializers import CommentSerializer, CommentDetailSerializer
from apps.posts.models import Post
from core.pagination import StandardPagination
from core.utils import sanitize_html


class CommentListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    serializer_class = CommentSerializer

    def get(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        qs = Comment.objects.filter(post=post, parent__isnull=True).order_by("created_at")
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request)
        data = [
            {
                "id": str(c.id),
                "author_id": str(c.author_id),
                "content": c.content,
                "replies_count": c.replies_count,
                "created_at": c.created_at.isoformat(),
            }
            for c in page
        ]
        return paginator.get_paginated_response(data)

    def post(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        content = sanitize_html(request.data.get("content", ""))
        c = Comment.objects.create(post=post, author=request.user, content=content)
        post.comments_count = Comment.objects.filter(post=post, parent__isnull=True).count()
        post.save(update_fields=["comments_count"])
        return Response(
            {
                "success": True,
                "data": {"id": str(c.id), "content": c.content},
                "message": "Comment added.",
                "meta": {},
            },
            status=201,
        )


class CommentDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CommentDetailSerializer

    def put(self, request, comment_id):
        c = get_object_or_404(Comment, pk=comment_id, author=request.user)
        c.content = sanitize_html(request.data.get("content", c.content))
        c.is_edited = True
        c.save()
        return Response({"success": True, "data": {"id": str(c.id)}, "message": "Updated.", "meta": {}})

    def delete(self, request, comment_id):
        c = get_object_or_404(Comment, pk=comment_id, author=request.user)
        post = c.post
        c.delete()
        post.comments_count = Comment.objects.filter(post=post, parent__isnull=True).count()
        post.save(update_fields=["comments_count"])
        return Response({"success": True, "data": {}, "message": "Deleted.", "meta": {}}, status=204)


class CommentReplyListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CommentSerializer

    def post(self, request, comment_id):
        parent = get_object_or_404(Comment, pk=comment_id)
        content = sanitize_html(request.data.get("content", ""))
        c = Comment.objects.create(
            post=parent.post,
            author=request.user,
            parent=parent,
            content=content,
        )
        parent.replies_count = Comment.objects.filter(parent=parent).count()
        parent.save(update_fields=["replies_count"])
        return Response(
            {"success": True, "data": {"id": str(c.id)}, "message": "Reply added.", "meta": {}},
            status=201,
        )

    def get(self, request, comment_id):
        parent = get_object_or_404(Comment, pk=comment_id)
        qs = Comment.objects.filter(parent=parent).order_by("created_at")
        data = [
            {
                "id": str(c.id),
                "author_id": str(c.author_id),
                "content": c.content,
                "created_at": c.created_at.isoformat(),
            }
            for c in qs
        ]
        return Response({"success": True, "data": data, "message": "", "meta": {}})
