from django.urls import path

from apps.memories import views as v

urlpatterns = [
    path("memories/", v.MemoriesListView.as_view(), name="memories-list"),
]
