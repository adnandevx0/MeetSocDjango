from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.groups.models import Group, GroupInvite, GroupMembership
from apps.groups.serializers import GroupSerializer, GroupMembershipSerializer, GroupInviteSerializer
from apps.posts.models import Post
from apps.posts.serializers import PostListSerializer
from core.utils import sanitize_html


class GroupListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GroupSerializer

    def get(self, request):
        qs = Group.objects.filter(privacy="public").order_by("-created_at")[:100]
        data = [{"id": str(g.id), "name": g.name, "slug": g.slug} for g in qs]
        return Response({"success": True, "data": data, "message": "", "meta": {}})

    def post(self, request):
        name = request.data.get("name", "Group")
        slug = slugify(name)[:250]
        base = slug
        n = 0
        while Group.objects.filter(slug=slug).exists():
            n += 1
            slug = f"{base}-{n}"[:250]
        g = Group.objects.create(
            name=name,
            slug=slug,
            description=request.data.get("description", ""),
            privacy=request.data.get("privacy", "public"),
            category=request.data.get("category", ""),
            created_by=request.user,
        )
        GroupMembership.objects.create(group=g, user=request.user, role="admin", status="active")
        g.members_count = 1
        g.save(update_fields=["members_count"])
        return Response(
            {"success": True, "data": {"id": str(g.id), "slug": g.slug}, "message": "Created.", "meta": {}},
            status=201,
        )


class GroupMyView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GroupSerializer

    def get(self, request):
        ids = GroupMembership.objects.filter(user=request.user, status="active").values_list("group_id", flat=True)
        qs = Group.objects.filter(id__in=ids)
        data = [{"id": str(g.id), "name": g.name, "slug": g.slug} for g in qs]
        return Response({"success": True, "data": data, "message": "", "meta": {}})


class GroupDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GroupSerializer

    def get(self, request, slug):
        g = get_object_or_404(Group, slug=slug)
        return Response(
            {
                "success": True,
                "data": {
                    "id": str(g.id),
                    "name": g.name,
                    "slug": g.slug,
                    "description": g.description,
                    "privacy": g.privacy,
                    "members_count": g.members_count,
                },
                "message": "",
                "meta": {},
            }
        )

    def put(self, request, slug):
        g = get_object_or_404(Group, slug=slug)
        if not GroupMembership.objects.filter(group=g, user=request.user, role="admin", status="active").exists():
            return Response({"success": False, "error": {"code": "FORBIDDEN", "message": "Admin only.", "details": {}}}, status=403)
        g.name = request.data.get("name", g.name)
        g.description = request.data.get("description", g.description)
        g.save()
        return Response({"success": True, "data": {"slug": g.slug}, "message": "Updated.", "meta": {}})

    def delete(self, request, slug):
        g = get_object_or_404(Group, slug=slug)
        if not GroupMembership.objects.filter(group=g, user=request.user, role="admin", status="active").exists():
            return Response({"success": False, "error": {"code": "FORBIDDEN", "message": "Admin only.", "details": {}}}, status=403)
        g.delete()
        return Response({"success": True, "data": {}, "message": "Deleted.", "meta": {}}, status=204)


class GroupJoinView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GroupSerializer

    def post(self, request, slug):
        g = get_object_or_404(Group, slug=slug)
        status_val = "active" if g.privacy == "public" else "pending"
        GroupMembership.objects.get_or_create(
            group=g,
            user=request.user,
            defaults={"role": "member", "status": status_val},
        )
        return Response({"success": True, "data": {}, "message": "Joined.", "meta": {}})


class GroupLeaveView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def post(self, request, slug):
        g = get_object_or_404(Group, slug=slug)
        GroupMembership.objects.filter(group=g, user=request.user).delete()
        return Response({"success": True, "data": {}, "message": "Left.", "meta": {}})


class GroupMembersView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GroupMembershipSerializer

    def get(self, request, slug):
        g = get_object_or_404(Group, slug=slug)
        qs = GroupMembership.objects.filter(group=g, status="active")
        from apps.users.serializers import UserPublicSerializer

        users = [m.user for m in qs]
        return Response(
            {
                "success": True,
                "data": UserPublicSerializer(users, many=True, context={"request": request}).data,
                "message": "",
                "meta": {},
            }
        )


class GroupInviteView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GroupInviteSerializer

    def post(self, request, slug):
        g = get_object_or_404(Group, slug=slug)
        uid = request.data.get("user_id")
        from django.contrib.auth import get_user_model

        u = get_object_or_404(get_user_model(), pk=uid)
        GroupInvite.objects.get_or_create(
            group=g,
            invited_by=request.user,
            invited_user=u,
            defaults={"status": "pending"},
        )
        return Response({"success": True, "data": {}, "message": "Invited.", "meta": {}})


class GroupMemberRoleView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GroupMembershipSerializer

    def patch(self, request, slug, uid):
        g = get_object_or_404(Group, slug=slug)
        if not GroupMembership.objects.filter(group=g, user=request.user, role="admin", status="active").exists():
            return Response({"success": False, "error": {"code": "FORBIDDEN", "message": "Admin only.", "details": {}}}, status=403)
        m = get_object_or_404(GroupMembership, group=g, user_id=uid)
        m.role = request.data.get("role", m.role)
        m.save(update_fields=["role"])
        return Response({"success": True, "data": {}, "message": "Updated.", "meta": {}})

    def delete(self, request, slug, uid):
        g = get_object_or_404(Group, slug=slug)
        if not GroupMembership.objects.filter(group=g, user=request.user, role__in=["admin", "moderator"], status="active").exists():
            return Response({"success": False, "error": {"code": "FORBIDDEN", "message": "Mod only.", "details": {}}}, status=403)
        GroupMembership.objects.filter(group=g, user_id=uid).delete()
        return Response({"success": True, "data": {}, "message": "Removed.", "meta": {}}, status=204)


class GroupPostsView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PostListSerializer

    def get(self, request, slug):
        g = get_object_or_404(Group, slug=slug)
        qs = Post.objects.filter(group=g).order_by("-created_at")[:50]
        return Response(
            {
                "success": True,
                "data": PostListSerializer(qs, many=True, context={"request": request}).data,
                "message": "",
                "meta": {},
            }
        )

    def post(self, request, slug):
        g = get_object_or_404(Group, slug=slug)
        if not GroupMembership.objects.filter(group=g, user=request.user, status="active").exists():
            return Response({"success": False, "error": {"code": "FORBIDDEN", "message": "Not a member.", "details": {}}}, status=403)
        p = Post.objects.create(
            author=request.user,
            content=sanitize_html(request.data.get("content", "")),
            post_type=request.data.get("post_type", "text"),
            privacy="public",
            group=g,
        )
        g.posts_count = Post.objects.filter(group=g).count()
        g.save(update_fields=["posts_count"])
        return Response(
            {"success": True, "data": {"id": str(p.id)}, "message": "Posted.", "meta": {}},
            status=201,
        )


class GroupPendingView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GroupMembershipSerializer

    def get(self, request, slug):
        g = get_object_or_404(Group, slug=slug)
        if not GroupMembership.objects.filter(group=g, user=request.user, role__in=["admin", "moderator"], status="active").exists():
            return Response({"success": False, "error": {"code": "FORBIDDEN", "message": "Mod only.", "details": {}}}, status=403)
        qs = GroupMembership.objects.filter(group=g, status="pending")
        from apps.users.serializers import UserPublicSerializer

        users = [m.user for m in qs]
        return Response(
            {
                "success": True,
                "data": UserPublicSerializer(users, many=True, context={"request": request}).data,
                "message": "",
                "meta": {},
            }
        )


class GroupApproveView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def post(self, request, slug, uid):
        g = get_object_or_404(Group, slug=slug)
        if not GroupMembership.objects.filter(group=g, user=request.user, role__in=["admin", "moderator"], status="active").exists():
            return Response({"success": False, "error": {"code": "FORBIDDEN", "message": "Mod only.", "details": {}}}, status=403)
        GroupMembership.objects.filter(group=g, user_id=uid, status="pending").update(status="active")
        return Response({"success": True, "data": {}, "message": "Approved.", "meta": {}})


class GroupBanView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def post(self, request, slug, uid):
        g = get_object_or_404(Group, slug=slug)
        if not GroupMembership.objects.filter(group=g, user=request.user, role__in=["admin", "moderator"], status="active").exists():
            return Response({"success": False, "error": {"code": "FORBIDDEN", "message": "Mod only.", "details": {}}}, status=403)
        GroupMembership.objects.filter(group=g, user_id=uid).update(status="banned")
        return Response({"success": True, "data": {}, "message": "Banned.", "meta": {}})
