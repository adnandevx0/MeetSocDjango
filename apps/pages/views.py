from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.pages.models import Page, PageAdmin, PageFollower
from apps.pages.serializers import PageSerializer, PageAdminSerializer, PageFollowerSerializer
from apps.posts.models import Post
from apps.posts.serializers import PostListSerializer
from core.utils import sanitize_html


class PageListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PageSerializer

    def get(self, request):
        qs = Page.objects.all().order_by("-created_at")[:100]
        data = [{"id": str(p.id), "name": p.name, "slug": p.slug} for p in qs]
        return Response({"success": True, "data": data, "message": "", "meta": {}})

    def post(self, request):
        name = request.data.get("name", "Page")
        slug = slugify(name)[:250]
        base = slug
        n = 0
        while Page.objects.filter(slug=slug).exists():
            n += 1
            slug = f"{base}-{n}"[:250]
        p = Page.objects.create(
            name=name,
            slug=slug,
            category=request.data.get("category", ""),
            description=request.data.get("description", ""),
            created_by=request.user,
        )
        PageAdmin.objects.create(page=p, user=request.user, role="owner")
        return Response(
            {"success": True, "data": {"id": str(p.id), "slug": p.slug}, "message": "Created.", "meta": {}},
            status=201,
        )


class PageMyView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PageSerializer

    def get(self, request):
        ids = PageAdmin.objects.filter(user=request.user).values_list("page_id", flat=True)
        qs = Page.objects.filter(id__in=ids)
        data = [{"id": str(p.id), "name": p.name, "slug": p.slug} for p in qs]
        return Response({"success": True, "data": data, "message": "", "meta": {}})


class PageDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PageSerializer

    def get(self, request, slug):
        p = get_object_or_404(Page, slug=slug)
        return Response(
            {
                "success": True,
                "data": {
                    "id": str(p.id),
                    "name": p.name,
                    "slug": p.slug,
                    "description": p.description,
                    "followers_count": p.followers_count,
                },
                "message": "",
                "meta": {},
            }
        )

    def put(self, request, slug):
        p = get_object_or_404(Page, slug=slug)
        if not PageAdmin.objects.filter(page=p, user=request.user, role__in=["owner", "admin", "editor"]).exists():
            return Response({"success": False, "error": {"code": "FORBIDDEN", "message": "Admin only.", "details": {}}}, status=403)
        p.name = request.data.get("name", p.name)
        p.description = request.data.get("description", p.description)
        p.save()
        return Response({"success": True, "data": {}, "message": "Updated.", "meta": {}})


class PageLikeView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def post(self, request, slug):
        p = get_object_or_404(Page, slug=slug)
        PageFollower.objects.update_or_create(page=p, user=request.user, defaults={"is_liked": True})
        p.likes_count = PageFollower.objects.filter(page=p, is_liked=True).count()
        p.save(update_fields=["likes_count"])
        return Response({"success": True, "data": {}, "message": "Liked.", "meta": {}})


class PageFollowView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PageFollowerSerializer

    def post(self, request, slug):
        p = get_object_or_404(Page, slug=slug)
        PageFollower.objects.update_or_create(page=p, user=request.user, defaults={"is_liked": True})
        p.followers_count = PageFollower.objects.filter(page=p).count()
        p.save(update_fields=["followers_count"])
        return Response({"success": True, "data": {}, "message": "Followed.", "meta": {}})


class PageUnfollowView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def delete(self, request, slug):
        p = get_object_or_404(Page, slug=slug)
        PageFollower.objects.filter(page=p, user=request.user).delete()
        return Response({"success": True, "data": {}, "message": "Unfollowed.", "meta": {}}, status=204)


class PagePostsView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PostListSerializer

    def get(self, request, slug):
        p = get_object_or_404(Page, slug=slug)
        qs = Post.objects.filter(page=p).order_by("-created_at")[:50]
        return Response(
            {
                "success": True,
                "data": PostListSerializer(qs, many=True, context={"request": request}).data,
                "message": "",
                "meta": {},
            }
        )

    def post(self, request, slug):
        p = get_object_or_404(Page, slug=slug)
        if not PageAdmin.objects.filter(page=p, user=request.user, role__in=["owner", "admin", "editor"]).exists():
            return Response({"success": False, "error": {"code": "FORBIDDEN", "message": "Editor only.", "details": {}}}, status=403)
        post = Post.objects.create(
            author=request.user,
            content=sanitize_html(request.data.get("content", "")),
            post_type=request.data.get("post_type", "text"),
            privacy="public",
            page=p,
        )
        return Response(
            {"success": True, "data": {"id": str(post.id)}, "message": "Posted.", "meta": {}},
            status=201,
        )


class PageFollowersView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PageFollowerSerializer

    def get(self, request, slug):
        p = get_object_or_404(Page, slug=slug)
        qs = PageFollower.objects.filter(page=p)
        from apps.users.serializers import UserPublicSerializer

        users = [f.user for f in qs]
        return Response(
            {
                "success": True,
                "data": UserPublicSerializer(users, many=True, context={"request": request}).data,
                "message": "",
                "meta": {},
            }
        )


class PageAdminsView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PageAdminSerializer

    def post(self, request, slug):
        p = get_object_or_404(Page, slug=slug)
        if not PageAdmin.objects.filter(page=p, user=request.user, role="owner").exists():
            return Response({"success": False, "error": {"code": "FORBIDDEN", "message": "Owner only.", "details": {}}}, status=403)
        uid = request.data.get("user_id")
        role = request.data.get("role", "editor")
        from django.contrib.auth import get_user_model

        u = get_object_or_404(get_user_model(), pk=uid)
        PageAdmin.objects.get_or_create(page=p, user=u, defaults={"role": role})
        return Response({"success": True, "data": {}, "message": "Admin added.", "meta": {}})


class PageInsightsView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def get(self, request, slug):
        p = get_object_or_404(Page, slug=slug)
        if not PageAdmin.objects.filter(page=p, user=request.user, role__in=["owner", "admin", "analyst"]).exists():
            return Response({"success": False, "error": {"code": "FORBIDDEN", "message": "Admin/analyst only.", "details": {}}}, status=403)
        return Response(
            {
                "success": True,
                "data": {
                    "followers": p.followers_count,
                    "likes": p.likes_count,
                    "posts": Post.objects.filter(page=p).count(),
                },
                "message": "",
                "meta": {},
            }
        )
