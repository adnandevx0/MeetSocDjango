from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.posts.models import ContentTag
from apps.watch.models import WatchVideo
from apps.watch.serializers import WatchVideoSerializer
from core.media_processing import optimize_image, optimize_video


def _parse_tag_ids(data):
    raw = data.get("tag_ids")
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw if x]
    if isinstance(raw, str):
        return [x.strip() for x in raw.split(",") if x.strip()]
    return []


class WatchListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WatchVideoSerializer

    def get(self, request):
        qs = WatchVideo.objects.select_related("category", "author").prefetch_related("tags").order_by(
            "-created_at"
        )[:100]
        data = [
            {
                "id": str(v.id),
                "title": v.title,
                "views_count": v.views_count,
                "created_at": v.created_at.isoformat(),
                "category": (
                    {"id": str(v.category_id), "name": v.category.name, "slug": v.category.slug}
                    if v.category_id
                    else None
                ),
            }
            for v in qs
        ]
        return Response({"success": True, "data": data, "message": "", "meta": {}})

    def post(self, request):
        video = request.FILES.get("video_file")
        thumb = request.FILES.get("thumbnail")
        if not video:
            return Response(
                {"success": False, "error": {"code": "REQUIRED", "message": "video_file required.", "details": {}}},
                status=400,
            )
        cid = request.data.get("category_id")
        if cid in ("", None):
            cid = None
        v = WatchVideo.objects.create(
            author=request.user,
            title=request.data.get("title", ""),
            description=request.data.get("description", ""),
            video_file=optimize_video(video),
            thumbnail=optimize_image(thumb) if thumb else None,
            duration=float(request.data.get("duration", 0)),
            category_id=cid,
        )
        tids = _parse_tag_ids(request.data)
        if tids:
            v.tags.set(ContentTag.objects.filter(id__in=tids))
        return Response(
            {"success": True, "data": {"id": str(v.id)}, "message": "Uploaded.", "meta": {}},
            status=201,
        )


class WatchDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WatchVideoSerializer

    def get(self, request, video_id):
        v = get_object_or_404(
            WatchVideo.objects.select_related("category", "author").prefetch_related("tags"),
            pk=video_id,
        )
        from django.core.cache import cache

        from apps.recommendations.models import UserInteraction
        from apps.recommendations.services import InterestService, InteractionService

        v.views_count += 1
        v.save(update_fields=["views_count"])
        ck = f"rec:wclick:{request.user.id}:{video_id}"
        if not cache.get(ck):
            InteractionService.record_watch_video_event(
                request.user, v, UserInteraction.ACTION_CLICK
            )
            cache.set(ck, 1, 120)
            InterestService.refresh_profile_snapshot(request.user)
        return Response(
            {
                "success": True,
                "data": {
                    "id": str(v.id),
                    "title": v.title,
                    "video_file": v.video_file.url if v.video_file else None,
                },
                "message": "",
                "meta": {},
            }
        )
