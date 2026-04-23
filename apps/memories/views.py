from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.memories.models import Memory
from apps.memories.serializers import MemorySerializer


class MemoriesListView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MemorySerializer

    def get(self, request):
        qs = Memory.objects.filter(user=request.user).order_by("-year")[:50]
        data = [
            {
                "id": str(m.id),
                "year": m.year,
                "summary": m.summary,
                "post_id": str(m.post_id) if m.post_id else None,
            }
            for m in qs
        ]
        return Response({"success": True, "data": data, "message": "", "meta": {}})
