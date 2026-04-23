from datetime import timedelta

from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.feed.models import FeedHide, FeedSnooze, RecentSearch, SavedPost
from apps.feed.services import FeedService
from apps.posts.models import Post
from apps.posts.serializers import FeedPostListSerializer
from apps.posts.views import StoriesFeedView

class FeedView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FeedPostListSerializer

    def get(self, request):
        page = int(request.query_params.get("page", 1))
        svc = FeedService(request.user)
        ranked = svc.get_feed(page=page)
        ids = [r["id"] for r in ranked]
        posts = Post.objects.filter(id__in=ids).select_related("category", "author").prefetch_related(
            "tags", "media_items"
        )
        order = {str(i): idx for idx, i in enumerate(ids)}
        posts = sorted(posts, key=lambda p: order.get(str(p.id), 999))
        return Response(
            {
                "success": True,
                "data": FeedPostListSerializer(posts, many=True, context={"request": request}).data,
                "message": "",
                "meta": {"page": page},
            }
        )


class FeedStoriesView(StoriesFeedView):
    """Same as posts stories feed; exposed under /feed/stories/."""

    pass


class FeedHideView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def post(self, request, post_id):
        FeedHide.objects.get_or_create(user=request.user, post_id=post_id)
        FeedService(request.user).invalidate_feed_cache(str(request.user.id))
        return Response({"success": True, "data": {}, "message": "Hidden.", "meta": {}})


class FeedSnoozeView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def post(self, request, user_id):
        until = timezone.now() + timedelta(days=30)
        FeedSnooze.objects.update_or_create(
            user=request.user,
            snoozed_user_id=user_id,
            defaults={"until": until},
        )
        FeedService(request.user).invalidate_feed_cache(str(request.user.id))
        return Response({"success": True, "data": {}, "message": "Snoozed.", "meta": {}})


class SavedPostsView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FeedPostListSerializer

    def get(self, request):
        ids = SavedPost.objects.filter(user=request.user).values_list("post_id", flat=True)
        qs = Post.objects.filter(id__in=ids).order_by("-created_at")
        return Response(
            {
                "success": True,
                "data": PostListSerializer(qs, many=True, context={"request": request}).data,
                "message": "",
                "meta": {},
            }
        )


class SavePostView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def post(self, request, post_id):
        SavedPost.objects.get_or_create(user=request.user, post_id=post_id)
        return Response({"success": True, "data": {}, "message": "Saved.", "meta": {}})

    def delete(self, request, post_id):
        SavedPost.objects.filter(user=request.user, post_id=post_id).delete()
        return Response({"success": True, "data": {}, "message": "Removed.", "meta": {}}, status=204)
