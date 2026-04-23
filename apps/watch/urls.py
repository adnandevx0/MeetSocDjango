from django.urls import path

from apps.watch import views as v

urlpatterns = [
    path("watch/videos/", v.WatchListCreateView.as_view(), name="watch-videos"),
    path("watch/videos/<uuid:video_id>/", v.WatchDetailView.as_view(), name="watch-video-detail"),
]
