from decimal import Decimal

from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.marketplace.models import Product, ProductMedia
from apps.marketplace.serializers import ProductSerializer
from core.media_processing import optimize_image


class ProductListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer

    def get(self, request):
        qs = Product.objects.filter(status="active").order_by("-created_at")[:100]
        data = [
            {
                "id": str(p.id),
                "title": p.title,
                "price": str(p.price),
                "category": p.category,
                "status": p.status,
            }
            for p in qs
        ]
        return Response({"success": True, "data": data, "message": "", "meta": {}})

    def post(self, request):
        p = Product.objects.create(
            seller=request.user,
            title=request.data.get("title", "Item"),
            description=request.data.get("description", ""),
            price=Decimal(str(request.data.get("price", "0"))),
            category=request.data.get("category", ""),
            condition=request.data.get("condition", "good"),
            location=request.data.get("location") or {},
        )
        for i, f in enumerate(request.FILES.getlist("images")):
            ProductMedia.objects.create(product=p, file=optimize_image(f), order=i)
        return Response(
            {"success": True, "data": {"id": str(p.id)}, "message": "Listed.", "meta": {}},
            status=201,
        )


class ProductDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer

    def get(self, request, product_id):
        p = get_object_or_404(Product, pk=product_id)
        p.views_count += 1
        p.save(update_fields=["views_count"])
        return Response(
            {
                "success": True,
                "data": {
                    "id": str(p.id),
                    "title": p.title,
                    "description": p.description,
                    "price": str(p.price),
                    "condition": p.condition,
                },
                "message": "",
                "meta": {},
            }
        )
