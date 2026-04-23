"""
Recommendation & interest scoring. Uses incremental DB updates (F()) + Redis cache for hot reads.
"""
from __future__ import annotations

import json
import math
import random
from typing import Iterable, List, Optional, Sequence, Tuple
from uuid import UUID

from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models import F
from django.utils import timezone

from apps.posts.models import Post
from apps.recommendations.constants import (
    CACHE_PROFILE_REFRESH_PREFIX,
    CACHE_TOP_CATEGORIES_PREFIX,
    PREFERRED_FEED_RATIO,
    SCORE_CLICK,
    SCORE_LIKE,
    SCORE_SHARE,
    SCORE_UPLOAD_IN_CATEGORY,
    SCORE_VIEW,
    SCORE_WATCH_MAX,
    SCORE_WATCH_PER_SECOND,
)
from apps.recommendations.models import UserCategoryScore, UserInteraction


def _resolve_category_from_post(post: Post):
    if post.category_id:
        return post.category_id
    sid = post.shared_post_id
    if sid:
        return Post.objects.filter(pk=sid).values_list("category_id", flat=True).first()
    return None


class InterestService:
    """Scores + top categories; profile snapshot JSON on UserProfile."""

    @staticmethod
    def add_score(user_id, category_id: Optional[UUID], delta: float) -> None:
        if not category_id or delta == 0:
            return
        obj, created = UserCategoryScore.objects.get_or_create(
            user_id=user_id,
            category_id=category_id,
            defaults={"score": delta},
        )
        if not created:
            UserCategoryScore.objects.filter(pk=obj.pk).update(score=F("score") + delta)
        cache.delete(f"{CACHE_TOP_CATEGORIES_PREFIX}{user_id}")

    @staticmethod
    def get_top_category_ids(user, limit: int = 3) -> List[str]:
        key = f"{CACHE_TOP_CATEGORIES_PREFIX}{user.id}"
        cached = cache.get(key)
        if cached is not None:
            return json.loads(cached)[:limit]
        rows = (
            UserCategoryScore.objects.filter(user=user)
            .order_by("-score", "-updated_at")
            .values_list("category_id", flat=True)[:limit]
        )
        out = [str(x) for x in rows if x]
        cache.set(key, json.dumps(out), timeout=300)
        return out[:limit]

    @staticmethod
    def refresh_profile_snapshot(user, throttle_seconds: int = 30) -> None:
        lock = f"{CACHE_PROFILE_REFRESH_PREFIX}{user.id}"
        if cache.get(lock):
            return
        cache.set(lock, 1, throttle_seconds)
        profile = user.profile
        top = list(
            UserCategoryScore.objects.filter(user=user)
            .order_by("-score", "-updated_at")
            .select_related("category")[:3]
        )
        snapshot = {
            "top_categories": [
                {"id": str(r.category_id), "name": r.category.name, "score": float(r.score)}
                for r in top
            ],
            "updated_at": timezone.now().isoformat(),
        }
        profile.interest_snapshot = snapshot
        profile.save(update_fields=["interest_snapshot"])


class InteractionService:
    """Records UserInteraction rows + applies category scores."""

    @staticmethod
    def _record(
        user,
        action: str,
        content_object,
        points: float,
        category_id: Optional[UUID],
        watch_seconds: float = 0,
    ) -> None:
        ct = ContentType.objects.get_for_model(content_object.__class__)
        UserInteraction.objects.create(
            user=user,
            action=action,
            content_type=ct,
            object_id=content_object.pk,
            category_id=category_id,
            watch_seconds=watch_seconds,
            points_applied=points,
        )
        InterestService.add_score(user.id, category_id, points)

    @classmethod
    def record_post_view(cls, user, post: Post, watch_seconds: float = 0) -> None:
        cid = _resolve_category_from_post(post)
        pts = SCORE_VIEW
        if watch_seconds > 0:
            pts += min(SCORE_WATCH_MAX, watch_seconds * SCORE_WATCH_PER_SECOND)
        cls._record(user, UserInteraction.ACTION_VIEW, post, pts, cid, watch_seconds=watch_seconds)

    @classmethod
    def record_post_click(cls, user, post: Post) -> None:
        cid = _resolve_category_from_post(post)
        cls._record(user, UserInteraction.ACTION_CLICK, post, SCORE_CLICK, cid)

    @classmethod
    def record_post_like(cls, user, post: Post) -> None:
        cid = _resolve_category_from_post(post)
        cls._record(user, UserInteraction.ACTION_LIKE, post, SCORE_LIKE, cid)

    @classmethod
    def record_post_share(cls, user, original: Post) -> None:
        cid = _resolve_category_from_post(original)
        cls._record(user, UserInteraction.ACTION_SHARE, original, SCORE_SHARE, cid)

    @classmethod
    def record_watch_video_event(cls, user, watch_video, action: str, watch_seconds: float = 0) -> None:
        from apps.watch.models import WatchVideo

        if not isinstance(watch_video, WatchVideo):
            return
        cid = watch_video.category_id
        if action == UserInteraction.ACTION_VIEW:
            pts = SCORE_VIEW + min(SCORE_WATCH_MAX, watch_seconds * SCORE_WATCH_PER_SECOND)
        elif action == UserInteraction.ACTION_CLICK:
            pts = SCORE_CLICK
        else:
            pts = SCORE_VIEW
        cls._record(user, action, watch_video, pts, cid, watch_seconds=watch_seconds)

    @classmethod
    def record_upload_in_category(cls, user, category_id: Optional[UUID]) -> None:
        InterestService.add_score(user.id, category_id, SCORE_UPLOAD_IN_CATEGORY)


def blend_feed_ids(
    preferred_ordered: Sequence[Tuple[float, "Post"]],
    explore_ordered: Sequence[Tuple[float, "Post"]],
) -> List[UUID]:
    """
    Merge two ranked lists: ~70% from preferred bucket, ~30% exploration (diversity).
    Returns all blended IDs without pagination limit.
    """
    pref_posts = [p[1] for p in preferred_ordered]
    exp_posts = [p[1] for p in explore_ordered]
    random.shuffle(exp_posts)

    seen: set = set()
    out: List[UUID] = []

    # Interleave: preferred first, then explore, then repeat
    for p in pref_posts:
        if p.id not in seen:
            seen.add(p.id)
            out.append(p.id)

    for p in exp_posts:
        if p.id not in seen:
            seen.add(p.id)
            out.append(p.id)

    return out


def rank_posts_for_user(user, posts: Iterable[Post]) -> Tuple[List[Tuple[float, Post]], List[Tuple[float, Post]]]:
    """
    Returns (preferred_scored, explore_scored) using category boost vs rest.
    """
    from django.db.models import Q

    from apps.users.models import Follow, Friendship

    preferred_ids = set(InterestService.get_top_category_ids(user, 3))
    now = timezone.now()
    friends = set()

    for f in Friendship.objects.filter(
        Q(sender=user, status="accepted") | Q(receiver=user, status="accepted")
    ):
        friends.add(f.receiver_id if f.sender_id == user.id else f.sender_id)

    follow_ids = set(Follow.objects.filter(follower=user).values_list("following_id", flat=True))

    preferred_scored: List[Tuple[float, Post]] = []
    explore_scored: List[Tuple[float, Post]] = []
    seen_authors: List = []

    for p in posts:
        age = (now - p.created_at).total_seconds() / 3600.0
        recency = math.exp(-age / 12.0) * 2.0
        reactions = sum((p.reactions_count or {}).values())
        content = (
            recency + reactions * 0.3 + p.comments_count * 0.5 + p.shares_count * 0.7 + p.views_count * 0.1
        )
        rel = 1.0
        if p.author_id in friends:
            rel = 1.5
        if p.author_id in follow_ids:
            rel = max(rel, 1.2)
        base = content * rel + (3.0 if p.author_id in friends else 0)

        same_author = sum(1 for _ in seen_authors[-3:] if _ == p.author_id)
        if same_author >= 3:
            base *= 0.5
        seen_authors.append(p.author_id)

        cat_str = str(p.category_id) if p.category_id else None
        in_pref = cat_str and cat_str in preferred_ids
        cat_boost = 1.85 if in_pref else 1.0
        score = base * cat_boost

        if in_pref:
            preferred_scored.append((score, p))
        else:
            explore_scored.append((score, p))

    preferred_scored.sort(key=lambda x: -x[0])
    explore_scored.sort(key=lambda x: -x[0])
    return preferred_scored, explore_scored
