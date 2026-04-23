from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

api_v1 = [
    path("", include("apps.users.urls")),
    path("", include("apps.posts.urls")),
    path("", include("apps.reactions.urls")),
    path("", include("apps.comments.urls")),
    path("", include("apps.messages.urls")),
    path("", include("apps.calls.urls")),
    path("", include("apps.notifications.urls")),
    path("", include("apps.groups.urls")),
    path("", include("apps.pages.urls")),
    path("", include("apps.marketplace.urls")),
    path("", include("apps.feed.urls")),
    path("", include("apps.search.urls")),
    path("", include("apps.watch.urls")),
    path("", include("apps.memories.urls")),
    path("", include("apps.verification.urls")),
    path("", include("apps.suspensions.urls")),
    path("", include("apps.recommendations.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
    path("api/v1/", include(api_v1)),
    path("social-auth/", include("social_django.urls", namespace="social")),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
