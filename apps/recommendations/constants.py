# Interest points (tune without schema changes)
SCORE_VIEW = 1
SCORE_CLICK = 2
SCORE_LIKE = 5
SCORE_SHARE = 8
# Watch-time: add up to SCORE_WATCH_MAX extra per interaction (scaled by seconds)
SCORE_WATCH_PER_SECOND = 0.1
SCORE_WATCH_MAX = 10.0
# Small boost when user uploads in a category (creator affinity)
SCORE_UPLOAD_IN_CATEGORY = 0.5

# Feed personalization (explore share = 1 - PREFERRED_FEED_RATIO)
PREFERRED_FEED_RATIO = 0.7

# Cache keys
CACHE_TOP_CATEGORIES_PREFIX = "rec:top:"
CACHE_PROFILE_REFRESH_PREFIX = "rec:prof:"
