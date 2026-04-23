from django.urls import path

from apps.feed.views import SavePostView
from apps.posts import views as v

urlpatterns = [
    path("posts/", v.PostListCreateView.as_view(), name="posts-list-create"),
    path("posts/<uuid:post_id>/", v.PostDetailView.as_view(), name="posts-detail"),
    path("posts/<uuid:post_id>/share/", v.PostShareView.as_view(), name="posts-share"),
    path("posts/<uuid:post_id>/shares/", v.PostSharesListView.as_view(), name="posts-shares"),
    path("posts/<uuid:post_id>/view/", v.PostViewRegisterView.as_view(), name="posts-view"),
    path("stories/", v.StoriesFeedView.as_view(), name="stories-feed"),
    path("stories/<uuid:story_id>/", v.StoryDetailView.as_view(), name="stories-detail"),
    path("stories/<uuid:story_id>/view/", v.StoryViewView.as_view(), name="stories-view"),
    path("stories/<uuid:story_id>/viewers/", v.StoryViewersView.as_view(), name="stories-viewers"),
    path("stories/archive/", v.StoryArchiveView.as_view(), name="stories-archive"),
    path("posts/<uuid:post_id>/save/", SavePostView.as_view(), name="post-save"),
]
