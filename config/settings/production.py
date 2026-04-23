import dj_database_url  # এটি অবশ্যই উপরে ইম্পোর্ট করবেন
from decouple import config
from .base import * # noqa: F403, F401

DEBUG = False

# ডাটাবেস সেটিংস - এটিই আসল সমাধান
# এটি DATABASE_URL এনভায়রনমেন্ট ভেরিয়েবল থেকে তথ্য নিয়ে ডাটাবেস সেটআপ করবে
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=False # কুলিফাই ইন্টারনাল নেটওয়ার্কে SSL সাধারণত লাগে না
    )
}

# সিকিউরিটি সেটিংস
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# হোয়াইট-নয়েজ (Static files) এর জন্য এটি প্রয়োজন হতে পারে
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
