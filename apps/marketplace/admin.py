from django.contrib import admin
from .models import Product, ProductMedia


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'seller', 'price', 'condition', 'status', 'created_at']
    list_filter = ['condition', 'status', 'created_at', 'price']
    search_fields = ['title', 'description', 'seller__username']
    readonly_fields = ['id', 'views_count', 'created_at']
    fieldsets = (
        ('Product Details', {
            'fields': ('id', 'title', 'description', 'seller')
        }),
        ('Pricing & Condition', {
            'fields': ('price', 'condition', 'status')
        }),
        ('Location', {
            'fields': ('location',)
        }),
        ('Category', {
            'fields': ('category',)
        }),
        ('Statistics', {
            'fields': ('views_count',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


@admin.register(ProductMedia)
class ProductMediaAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'file', 'order']
    list_filter = ['order']
    search_fields = ['product__title']
    readonly_fields = ['id']
