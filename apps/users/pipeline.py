"""
Social auth pipeline: create profile and defaults for new OAuth users.
"""
from datetime import date

from django.utils.text import slugify


def social_user_setup(backend, user, response, *args, **kwargs):
    if not user.username or user.username.startswith("user_"):
        base = user.email.split("@")[0] if user.email else "user"
        from apps.users.models import User

        uname = slugify(base) or "user"
        if User.objects.filter(username=uname).exclude(pk=user.pk).exists():
            uname = f"{uname}_{str(user.id)[:8]}"
        user.username = uname[:150]
    if not user.full_name:
        user.full_name = response.get("name") or user.email.split("@")[0]
    if not user.date_of_birth:
        user.date_of_birth = date(1990, 1, 1)
    user.is_verified = True
    user.save()
    return {"user": user}
