import json

from django.core.cache import cache
from django.utils import timezone

from apps.feed.models import FeedHide, FeedSnooze
from apps.posts.models import Post
from apps.recommendations.services import blend_feed_ids, rank_posts_for_user
from apps.users.models import BlockList


class FeedService:
    """Ranked news feed with Redis cache and diversity rules."""

    def __init__(self, user):
        self.user = user

    def get_cached_feed(self, user_id, page=1):
        key = f"feed:{user_id}:{page}"
        raw = cache.get(key)
        if raw:
            return json.loads(raw)
        return None

    def invalidate_feed_cache(self, user_id):
        for i in range(1, 50):
            cache.delete(f"feed:{user_id}:{i}")

    def get_feed(self, page=1, page_size=20):
        """
        Composite ranking: recency, engagement, relationship weight, diversity.
        """
        uid = str(self.user.id)
        cached = self.get_cached_feed(uid, page)
        if cached:
            return cached

        blocked = set(
            BlockList.objects.filter(blocker=self.user).values_list("blocked_id", flat=True)
        ) | set(BlockList.objects.filter(blocked=self.user).values_list("blocker_id", flat=True))

        snoozed = set(
            FeedSnooze.objects.filter(user=self.user, until__gt=timezone.now()).values_list(
                "snoozed_user_id", flat=True
            )
        )

        hidden_posts = set(FeedHide.objects.filter(user=self.user).values_list("post_id", flat=True))

        qs = (
            Post.objects.filter(privacy="public")
            .select_related("category", "author")
            .exclude(author_id__in=blocked)
            .exclude(author_id__in=snoozed)
            .exclude(id__in=hidden_posts)
            .order_by("-created_at")[:500]
        )

        posts_list = list(qs)
        preferred_scored, explore_scored = rank_posts_for_user(self.user, posts_list)
        full_ids = blend_feed_ids(preferred_scored, explore_scored)
        start = (page - 1) * page_size
        slice_ids = full_ids[start : start + page_size]

        out = [{"id": str(i), "author_id": "", "score_hint": True} for i in slice_ids]
        cache.set(f"feed:{uid}:{page}", json.dumps(out), timeout=300)
        return out
