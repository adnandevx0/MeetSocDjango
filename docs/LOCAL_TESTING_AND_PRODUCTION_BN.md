# MeetSoc Backend: লোকাল টেস্টিং + Production Deployment গাইড (বাংলা)

## 1) লোকাল মেশিনে সম্পূর্ণ সেটআপ

### প্রি-রিকুইজিট
- Python 3.11+
- (ঐচ্ছিক) PostgreSQL 15+, Redis 7+ (production-like রান করার জন্য)
- `ffmpeg` (ভিডিও কম্প্রেশন চালু রাখতে)

### দ্রুত রান (SQLite mode)
1. Virtualenv:
   - `python -m venv .venv`
   - `.venv\Scripts\activate`
2. Dependency install:
   - `pip install -r requirements/development.txt`
3. Env:
   - `.env.example` কপি করে `.env` বানান
   - `USE_SQLITE=True` রাখুন
4. DB migrate:
   - `python manage.py migrate`
5. সুপার ইউজার:
   - `python manage.py createsuperuser`
6. সার্ভার:
   - `python manage.py runserver 6060`
7. API docs:
   - `http://127.0.0.1:6060/api/docs/`

### Production-like local run (PostgreSQL + Redis)
`.env` এ:
- `USE_SQLITE=False`
- `DB_*` + `REDIS_URL` সেট করুন
- `CELERY_BROKER_URL` + `CELERY_RESULT_BACKEND` সেট করুন

তারপর:
- `python manage.py migrate`
- `daphne -b 127.0.0.1 -p 6060 config.asgi:application` or " $env:DJANGO_SETTINGS_MODULE="config.settings.development"; daphne -b 127.0.0.1 -p 6060 config.asgi:application"
- `celery -A celery_tasks worker -l info`
- `celery -A celery_tasks beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler`

## 2) পূর্ণ টেস্টিং চেকলিস্ট

- `python manage.py check`
- `pytest -q`
- API smoke (manual): Swagger থেকে auth + protected endpoint কল করুন
- Media upload টেস্ট:
  - avatar upload
  - পোস্টে image/video upload
  - watch video upload
  - marketplace images upload
- নিশ্চিত করুন output media size কমেছে (image/video compression)

## 3) Production-এ publish করার স্টেপ

## Recommended stack
- **App host**: Render / Railway / Hetzner VPS (Docker হলে VPS flexible)
- **Database**: Managed PostgreSQL
- **Cache/Queue**: Managed Redis
- **Storage**: Backblaze B2 (S3-compatible)
- **CDN/DNS/WAF**: Cloudflare

### `.env` production baseline
- `DEBUG=False`
- `SECRET_KEY=<strong secret>`
- `ALLOWED_HOSTS=api.yourdomain.com`
- `CSRF_TRUSTED_ORIGINS=https://api.yourdomain.com,https://yourdomain.com`
- `SECURE_SSL_REDIRECT=True`
- `STORAGE_BACKEND=s3`

### Deploy command flow
1. Build/install:
   - `pip install -r requirements/base.txt`
2. Migration:
   - `python manage.py migrate --noinput`
3. Static:
   - `python manage.py collectstatic --noinput`
4. Run:
   - `daphne -b 0.0.0.0 -p 8000 config.asgi:application`
5. Worker:
   - `celery -A celery_tasks worker -l info`
6. Beat:
   - `celery -A celery_tasks beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler`

## 4) Backblaze B2 + Cloudflare CDN

### Backblaze B2 থেকে কীভাবে কিনবেন
1. Backblaze account খুলুন
2. B2 Cloud Storage plan select করুন (pay-as-you-go)
3. Bucket তৈরি করুন (private/public প্রয়োজন অনুযায়ী)
4. Application Key তৈরি করুন (bucket-level access best)
5. S3 endpoint/domain নোট করুন

### Project `.env` values
- `STORAGE_BACKEND=s3`
- `AWS_ACCESS_KEY_ID=<B2 key id>`
- `AWS_SECRET_ACCESS_KEY=<B2 app key>`
- `AWS_STORAGE_BUCKET_NAME=<bucket name>`
- `AWS_S3_REGION_NAME=us-east-005` (বা আপনার B2 region)
- `AWS_S3_ENDPOINT_URL=https://s3.<region>.backblazeb2.com`
- `AWS_S3_CUSTOM_DOMAIN=<your Cloudflare CDN domain>` (optional, recommended)

### Cloudflare setup
1. Domain add করুন Cloudflare-এ
2. DNS CNAME দিন B2 bucket endpoint/custom domain-এ
3. SSL/TLS full(strict) দিন
4. Caching rule: media path (`/posts/*`, `/watch/*`, `/avatars/*`) cache করুন
5. Hotlink protection + WAF rules enable করুন

## 5) Compression setup (already integrated)

এই backend এখন:
- Image upload -> JPEG optimize + resize (`max 1920`)
- Video upload -> `ffmpeg` দিয়ে H.264/AAC compress (CRF ভিত্তিক)
- Affected modules:
  - users avatar/cover
  - posts media + stories media
  - watch video/thumbnail
  - marketplace images

**Note:** Production server-এ অবশ্যই `ffmpeg` install থাকতে হবে, না থাকলে video fallback original file থাকবে।

## 6) Security baseline

প্রজেক্টে hardening enabled:
- `X_FRAME_OPTIONS=DENY`
- `SECURE_CONTENT_TYPE_NOSNIFF=True`
- `SESSION_COOKIE_HTTPONLY=True`
- `CSRF_COOKIE_HTTPONLY=True`
- `SECURE_REFERRER_POLICY=strict-origin-when-cross-origin`
- `CSRF_TRUSTED_ORIGINS` env-driven

Production-এ আরও:
- Cloudflare WAF + rate limit rules
- DB backup schedule
- rotate secrets every 60-90 days
