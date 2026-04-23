from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.posts.models import Post
from apps.recommendations.models import UserInteraction
from apps.recommendations.services import InterestService, InteractionService
from apps.recommendations.serializers import ContentCategorySerializer, UserInterestSummarySerializer, InteractionSerializer
from apps.watch.models import WatchVideo


class ContentCategoriesListView(APIView):
    """Public list of categories for upload forms (active only)."""

    permission_classes = [IsAuthenticated]
    serializer_class = ContentCategorySerializer
    serializer_class = ContentCategorySerializer

    def get(self, request):
        from apps.posts.models import ContentCategory

        qs = ContentCategory.objects.filter(is_active=True).order_by("sort_order", "name")
        data = [{"id": str(c.id), "name": c.name, "slug": c.slug} for c in qs]
        return Response({"success": True, "data": {"categories": data}, "message": "", "meta": {}})


class UserInterestSummaryView(APIView):
    """Top categories + cached snapshot from profile."""

    permission_classes = [IsAuthenticated]
    serializer_class = UserInterestSummarySerializer
    serializer_class = UserInterestSummarySerializer

    def get(self, request):
        top = InterestService.get_top_category_ids(request.user, 3)
        snapshot = request.user.profile.interest_snapshot or {}
        return Response(
            {
                "success": True,
                "data": {"top_category_ids": top, "snapshot": snapshot},
                "message": "",
                "meta": {},
            }
        )


class TrackInteractionView(APIView):
    """
    Client-side events: watch time on posts/videos, explicit views, clicks.
    Prefer batching watch_seconds from the player to reduce requests.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = InteractionSerializer

    def post(self, request):
        action = request.data.get("action", UserInteraction.ACTION_VIEW)
        watch_seconds = float(request.data.get("watch_seconds") or 0)
        post_id = request.data.get("post_id")
        video_id = request.data.get("watch_video_id")

        if post_id:
            post = get_object_or_404(Post, pk=post_id)
            if action == UserInteraction.ACTION_CLICK:
                InteractionService.record_post_click(request.user, post)
            elif action == UserInteraction.ACTION_WATCH:
                InteractionService.record_post_view(request.user, post, watch_seconds=watch_seconds)
            else:
                InteractionService.record_post_view(request.user, post, watch_seconds=watch_seconds)
            InterestService.refresh_profile_snapshot(request.user)
            return Response({"success": True, "data": {}, "message": "Recorded.", "meta": {}})

        if video_id:
            wv = get_object_or_404(WatchVideo, pk=video_id)
            if action == UserInteraction.ACTION_CLICK:
                InteractionService.record_watch_video_event(
                    request.user, wv, UserInteraction.ACTION_CLICK
                )
            else:
                InteractionService.record_watch_video_event(
                    request.user, wv, UserInteraction.ACTION_WATCH, watch_seconds=watch_seconds
                )
            InterestService.refresh_profile_snapshot(request.user)
            return Response({"success": True, "data": {}, "message": "Recorded.", "meta": {}})

        return Response(
            {
                "success": False,
                "error": {"code": "INVALID", "message": "post_id or watch_video_id required.", "details": {}},
            },
            status=400,
        )
