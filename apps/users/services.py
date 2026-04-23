"""
Friend suggestion algorithm (2nd degree + scoring).
"""
from collections import defaultdict

from django.db.models import Q

from apps.groups.models import GroupMembership
from apps.users.models import BlockList, Friendship, User, UserProfile


def _friend_ids(user):
    accepted = Friendship.objects.filter(
        Q(sender=user, status="accepted") | Q(receiver=user, status="accepted")
    )
    ids = set()
    for f in accepted:
        other = f.receiver_id if f.sender_id == user.id else f.sender_id
        ids.add(str(other))
    return ids


def get_friend_suggestions(user: User, limit: int = 20):
    """
    1. 2nd-degree connections (friends of friends)
    2. Exclude friends, blocked, self
    3. Score: mutual*3 + shared_groups*2 + same_location*1
    """
    my_id = user.id
    friends = _friend_ids(user)
    blocked_ids = set(
        BlockList.objects.filter(blocker=user).values_list("blocked_id", flat=True)
    ) | set(BlockList.objects.filter(blocked=user).values_list("blocker_id", flat=True))
    blocked_ids = {str(x) for x in blocked_ids}

    candidates = defaultdict(lambda: {"mutual": 0, "shared_groups": 0, "same_location": 0})

    for fid in friends:
        fof = _friend_ids(User.objects.get(pk=fid))
        for cand in fof:
            if cand == str(my_id) or cand in friends or cand in blocked_ids:
                continue
            candidates[cand]["mutual"] += 1

    my_groups = set(
        GroupMembership.objects.filter(user=user, status="active").values_list(
            "group_id", flat=True
        )
    )
    try:
        my_loc = (user.profile.city or "").strip().lower()
    except UserProfile.DoesNotExist:
        my_loc = ""

    scores = []
    for cand_id, data in candidates.items():
        if not data["mutual"]:
            continue
        cand_user = User.objects.filter(pk=cand_id).select_related("profile").first()
        if not cand_user:
            continue
        cand_groups = set(
            GroupMembership.objects.filter(user=cand_user, status="active").values_list(
                "group_id", flat=True
            )
        )
        shared_groups = len(my_groups & cand_groups)
        try:
            cand_loc = (cand_user.profile.country or "").strip().lower()
        except UserProfile.DoesNotExist:
            cand_loc = ""
        same_location = 1 if my_loc and cand_loc and my_loc == cand_loc else 0
        score = data["mutual"] * 3 + shared_groups * 2 + same_location * 1
        scores.append((score, cand_user))

    scores.sort(key=lambda x: -x[0])
    return [u for _, u in scores[:limit]]
