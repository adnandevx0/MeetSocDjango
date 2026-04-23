# MeetSoc ব্যাকএন্ড — প্রোডাকশন ডিপ্লয়মেন্ট সম্পূর্ণ গাইড

এই ডকুমেন্টে বলা আছে প্রোডাকশনে আপলোড করার আগে ও পরে **কী কী করবেন**, **কোথা থেকে লিংক/ক্রেডেনশিয়াল নেবেন**, **ডাটাবেজ কীভাবে কানেক্ট করবেন**, এবং **প্রজেক্টকে production-ready করার ধাপগুলো**।

---

## ১. মোট দৃশ্যপট (আপনার সার্ভারে কী চলবে)

| কম্পোনেন্ট | কাজ |
|------------|-----|
| **Django + Daphne (ASGI)** | REST API + WebSocket (চ্যাট, নোটিফিকেশন, কল সিগন্যালিং) |
| **PostgreSQL 15+** | মূল ডাটাবেজ |
| **Redis 7+** | ক্যাশ, Celery ব্রোকার, Django Channels লেয়ার |
| **Celery Worker** | ইমেইল, পুশ, ফিড টাস্ক |
| **Celery Beat** | সময়সূচি (ক্রন) টাস্ক |
| **Nginx (ঐচ্ছিক)** | HTTPS, স্ট্যাটিক/মিডিয়া, রিভার্স প্রক্সি |
| **S3 বা Cloudinary** | প্রোডাকশনে ফাইল স্টোরেজ (সুপারিশকৃত) |

লোকাল ডেভেলপমেন্টে `USE_SQLITE=True` থাকলে SQLite ব্যবহার হয়। **প্রোডাকশনে অবশ্যই `USE_SQLITE=False` (বা সেট না করে)** এবং নিচের মতো PostgreSQL + Redis কনফিগার করতে হবে।

---

## ২. প্রোডাকশনের জন্য যা যা জোগাড় করতে হবে

### ২.১ ডোমেইন ও HTTPS

- একটি **ডোমেইন** (যেমন `api.meetsoc.com`) কিনুন (Namecheap, GoDaddy, Cloudflare Registrar ইত্যাদি)।
- **SSL সার্টিফিকেট**: Let's Encrypt (ফ্রি, Certbot) অথবা ক্লাউড প্রোভাইডারের ম্যানেজড SSL।
- প্রোডাকশনে **`SECURE_SSL_REDIRECT=True`** রাখুন (ইতিমধ্যে `config/settings/production.py` এ আছে)।

### ২.২ সিক্রেট কী (`SECRET_KEY`)

- Django এর জন্য একটি দীর্ঘ র্যান্ডম স্ট্রিং তৈরি করুন:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

- এটি **কখনো গিটে কমিট করবেন না**; শুধু সার্ভারের `.env` বা হোস্টের সিক্রেট স্টোরে রাখুন।

---

## ৩. ডাটাবেজ (PostgreSQL) — কোথা থেকে কী পাবেন

আপনি **নিজের সার্ভারে PostgreSQL ইনস্টল** করতে পারেন, অথবা **ম্যানেজড ডাটাবেজ** নিতে পারেন।

### বিকল্প A — নিজের VPS + Docker (`docker-compose.yml`)

- `docker/docker-compose.yml` এ `db` সার্ভিস আছে।
- কানেকশন (কন্টেইনারের ভিতর থেকে):  
  `DB_HOST=db`, `DB_PORT=5432`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` = কম্পোজ ফাইলের মতো।

### বিকল্প B — ম্যানেজড PostgreSQL (সুপারিশকৃত প্রোডাকশনের জন্য)

নিচের যেকোনো প্রোভাইডার থেকে **PostgreSQL** ক্লাস্টার তৈরি করলে ড্যাশবোর্ডে সাধারণত পাবেন:

| যা চাই | কোথায় দেখবেন |
|--------|----------------|
| **Host** | `xxxx.region.rds.amazonaws.com` (AWS RDS), অথবা অনুরূপ হোস্ট স্ট্রিং |
| **Port** | সাধারণত `5432` |
| **Database name** | আপনি যে নাম দিয়েছেন (যেমন `meetsoc`) |
| **User / Password** | আপনি সেট করেছেন বা জেনারেট করা |

**উদাহরণ প্রোভাইডার (লিংক — অ্যাকাউন্ট খুলে সেখান থেকে ক্রেডেনশিয়াল নিন):**

- **AWS RDS PostgreSQL**: [AWS RDS Console](https://console.aws.amazon.com/rds/) — Create database → Engine PostgreSQL।
- **DigitalOcean Managed Databases**: [Databases](https://cloud.digitalocean.com/databases)।
- **Supabase** (PostgreSQL + extras): [supabase.com](https://supabase.com) — Project Settings → Database।
- **Neon**: [neon.tech](https://neon.tech) — connection string।
- **Azure Database for PostgreSQL**, **Google Cloud SQL** — নিজ নিজ কনসোল।

**`.env` এ কীভাবে বসাবেন (ম্যানেজড DB):**

```env
USE_SQLITE=False
DB_HOST=আপনার-হোস্ট.rds.amazonaws.com
DB_PORT=5432
DB_NAME=meetsoc
DB_USER=meetsoc_user
DB_PASSWORD=শক্তিশালী-পাসওয়ার্ড
```

**সংযোগ টেস্ট (লোকাল থেকে, যদি ফায়ারওয়াল অনুমতি দেয়):**

```bash
# psql ইনস্টল থাকলে
psql "postgresql://DB_USER:DB_PASSWORD@DB_HOST:5432/DB_NAME"
```

ডিপ্লয়ের পর সার্ভার থেকে একই হোস্ট/পোর্ট দিয়ে Django কানেক্ট করবে।

---

## ৪. Redis — কোথা থেকে কী পাবেন

Redis লাগবে: **ক্যাশ**, **Celery**, **Channels**।

### বিকল্প A — Docker Compose

- `REDIS_URL=redis://redis:6379/0` (কন্টেইনার নাম `redis`)।

### বিকল্প B — ম্যানেজড Redis

- **Redis Cloud**: [redis.com/try-free](https://redis.com/try-free/) — Dashboard এ **Public endpoint** + **password**।
- **AWS ElastiCache**, **DigitalOcean Managed Redis** ইত্যাদি।

**`.env` উদাহরণ:**

```env
REDIS_URL=redis://:PASSWORD@your-redis-host:6379/0
CELERY_BROKER_URL=redis://:PASSWORD@your-redis-host:6379/2
CELERY_RESULT_BACKEND=redis://:PASSWORD@your-redis-host:6379/2
```

(পাসওয়ার্ড থাকলে URL ফরম্যাট প্রোভাইডারের ডকুমেন্ট অনুযায়ী হবে।)

---

## ৫. মিডিয়া স্টোরেজ (S3 বা Cloudinary)

লোকালে `STORAGE_BACKEND=local`। প্রোডাকশনে **অবজেক্ট স্টোরেজ** সুপারিশ।

### AWS S3

1. [AWS Console](https://console.aws.amazon.com/) → **IAM** → User তৈরি → **Programmatic access** → Policy: `AmazonS3FullAccess` (বা ন্যূনতম S3 বাকেট পলিসি)।
2. **Access Key ID** + **Secret Access Key** সংরক্ষণ করুন।
3. **S3** → বাকেট তৈরি → রিজিয়ন নোট করুন (`us-east-1` ইত্যাদি)।

```env
STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=meetsoc-media
AWS_S3_REGION_NAME=us-east-1
```

(কাস্টম ডোমেইন CDN থাকলে `AWS_S3_CUSTOM_DOMAIN` সেট করুন।)

### Cloudinary

1. [cloudinary.com](https://cloudinary.com) — Sign up → Dashboard এ **Cloud name**, **API Key**, **API Secret**।

```env
STORAGE_BACKEND=cloudinary
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
```

---

## ৬. ইমেইল (SMTP)

প্রোডাকশনে `EMAIL_BACKEND` সেট করুন SMTP এ (যেমন SendGrid, Mailgun, বা Gmail App Password)।

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=SendGrid-API-key
DEFAULT_FROM_EMAIL=MeetSoc <noreply@yourdomain.com>
```

- **SendGrid**: [sendgrid.com](https://sendgrid.com) — API Keys।
- **Gmail**: Google Account → Security → **App passwords** (সাধারণ পাসওয়ার্ড নয়)।

---

## ৭. OAuth (Google / Facebook লগইন API)

### Google

1. [Google Cloud Console](https://console.cloud.google.com/) → প্রজেক্ট → **APIs & Services** → **Credentials** → **OAuth 2.0 Client IDs**।
2. Application type: **Web application** (বা আপনার ফ্লাটার/ওয়েবের জন্য যা লাগে)।
3. **Client ID** ও **Client Secret** `.env` এ:

```env
GOOGLE_OAUTH2_KEY=xxx.apps.googleusercontent.com
GOOGLE_OAUTH2_SECRET=...
```

### Facebook

1. [Meta for Developers](https://developers.facebook.com/) → অ্যাপ তৈরি → **Facebook Login** প্রোডাক্ট।
2. **App ID** ও **App Secret**:

```env
FACEBOOK_APP_ID=...
FACEBOOK_APP_SECRET=...
```

---

## ৮. Firebase Cloud Messaging (পুশ নোটিফিকেশন)

1. [Firebase Console](https://console.firebase.google.com/) → প্রজেক্ট → **Project settings** → **Cloud Messaging**।
2. পুরনো সার্ভার কী বা HTTP v1 — `pyfcm` সাধারণত **Legacy server key** বা সেটআপ অনুযায়ী। প্রোভাইডার ডক চেক করুন।

```env
FCM_SERVER_KEY=...
```

---

## ৯. WebRTC (TURN) — ভিডিও/অডিও কল

স্ট্যাটিক **STUN** কোডে আছে; **TURN** প্রোডাকশনে প্রায়ই লাগে।

- সেবা: [Twilio Network Traversal](https://www.twilio.com/stun-turn), [Metered TURN](https://www.metered.ca/tools/openrelay/), বা নিজের coturn সার্ভার।

```env
TURN_SERVER_URL=turn:your-server.com:3478
TURN_USERNAME=...
TURN_CREDENTIAL=...
```

API: `GET /api/v1/calls/ice-servers/` — ক্লায়েন্ট এগুলো ব্যবহার করে।

---

## ১০. CORS (Flutter / ফ্রন্টএন্ড)

আপনার অ্যাপের **ঠিক URL** দিন:

```env
CORS_ALLOWED_ORIGINS=https://app.meetsoc.com,https://www.meetsoc.com
```

কমা দিয়ে আলাদা, স্পেস নয়।

---

## ১১. প্রোডাকশন `.env` চেকলিস্ট

প্রজেক্ট রুটে `.env` কপি করুন `.env.example` থেকে এবং নিচেরগুলো **অবশ্যই** প্রোডাকশন মান দিন:

| ভেরিয়েবল | মান |
|-----------|-----|
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` |
| `DEBUG` | `False` |
| `SECRET_KEY` | দীর্ঘ র্যান্ডম স্ট্রিং |
| `ALLOWED_HOSTS` | `api.yourdomain.com` (কমা পৃথক) |
| `USE_SQLITE` | `False` |
| `DB_*` | PostgreSQL কানেকশন |
| `REDIS_URL`, `CELERY_*` | Redis |
| `CORS_ALLOWED_ORIGORS` | ফ্রন্টএন্ড URL |
| `STORAGE_BACKEND` + ক্লাউড কী | S3 বা Cloudinary |
| `EMAIL_*` | SMTP |
| `SECURE_SSL_REDIRECT` | `True` |

---

## ১২. ডিপ্লয় করার ধাপ (সংক্ষেপ)

### ধাপ ১: কোড সার্ভারে আনুন

```bash
git clone <your-repo> && cd metsoc
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements/production.txt
```

### ধাপ ২: এনভায়রনমেন্ট

- সার্ভারে `.env` তৈরি করুন (উপরের চেকলিস্ট)।
- `production.txt` এ `gunicorn`/`sentry` থাকতে পারে — ASGI এর জন্য **Daphne** ব্যবহার করছেন WebSocket এর জন্য।

### ধাপ ৩: মাইগ্রেশন

```bash
export DJANGO_SETTINGS_MODULE=config.settings.production   # Linux/Mac
set DJANGO_SETTINGS_MODULE=config.settings.production      # Windows CMD
python manage.py migrate
python manage.py collectstatic --noinput
```

### ধাপ ৪: প্রসেস চালু (উদাহরণ)

- **Web + WebSocket**: `daphne -b 0.0.0.0 -p 8000 config.asgi:application`
- **Celery worker**: `celery -A celery_tasks worker -l info`
- **Celery beat**: `celery -A celery_tasks beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler`

### ধাপ ৫: Nginx

- `docker/nginx.conf` এর মতো রিভার্স প্রক্সি: `proxy_pass` → `127.0.0.1:8000`
- WebSocket এর জন্য `Upgrade` ও `Connection` হেডার (ফাইলে আছে)।
- বাইরে থেকে URL: `https://api.yourdomain.com`

### ধাপ ৬: WebSocket URL (ক্লায়েন্ট)

- REST: `https://api.yourdomain.com/api/v1/...`
- WebSocket: `wss://api.yourdomain.com/ws/chat/<uuid>/` ইত্যাদি (`http` নয়, **`wss`**)।

---

## ১৩. ডাটাবেজ “কানেক্ট” হচ্ছে কিনা যাচাই

```bash
python manage.py dbshell
# অথবা
python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('OK')"
```

---

## ১৪. প্রোডাকশনে নিরাপত্তা (সংক্ষেপ)

- `DEBUG=False`
- `SECRET_KEY` গোপন
- ফায়ারওয়াল: শুধু 80/443 পাবলিক; PostgreSQL/Redis শুধু প্রাইভেট নেটওয়ার্ক বা IP allowlist
- নিয়মিত ব্যাকআপ (PostgreSQL dump, S3 versioning)
- `ALLOWED_HOSTS` সঠিক ডোমেইন

---

## ১৫. দ্রুত রেফারেন্স — কোন সেবা কোন লিংক

| সেবা | কোথায় অ্যাকাউন্ট / কী নেবেন |
|------|-------------------------------|
| PostgreSQL (ম্যানেজড) | AWS RDS, DigitalOcean, Supabase, Neon ইত্যাদি ড্যাশবোর্ড |
| Redis | Redis Cloud, AWS ElastiCache, DO |
| ফাইল স্টোরেজ | AWS S3 Console, Cloudinary Dashboard |
| ইমেইল | SendGrid, Mailgun, Gmail App Password |
| Google OAuth | Google Cloud Console → Credentials |
| Facebook OAuth | developers.facebook.com |
| FCM | Firebase Console → Project settings |
| SSL | Let's Encrypt / হোস্টিং প্যানেল |

---

## ১৬. সমস্যা হলে

- `python manage.py check --deploy` (প্রোডাকশন সেটিংসে কিছু সতর্কতা দেখায়)
- লগ: অ্যাপ লগ, Nginx `error.log`, Celery worker লগ

---

**সংক্ষেপে:** প্রোডাকশনে **PostgreSQL + Redis + গোপন SECRET_KEY + বন্ধ DEBUG + সঠিক ALLOWED_HOSTS/CORS + ক্লাউড স্টোরেজ + SMTP + (ঐচ্ছিক) OAuth/FCM/TURN** দিয়ে `.env` ভরে, `migrate` + `collectstatic` চালিয়ে Daphne + Celery + Nginx দিয়ে সার্ভ করুন। এই ফাইলটি সেই ক্রম ধরে অনুসরণ করলে production-ready ডিপ্লয় সম্ভব।
