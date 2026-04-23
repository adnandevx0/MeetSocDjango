# MeetSoc Backend

Production-oriented Django REST API for the MeetSoc social platform: JWT auth, posts/stories, reactions, comments, real-time chat and notifications (Django Channels), WebRTC signaling, Celery tasks, Redis caching, PostgreSQL full-text search, and OpenAPI docs.

## Requirements

- Python 3.11+
- PostgreSQL 15+
- Redis 7+

## Setup (local)

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements/development.txt
```

2. Copy `.env.example` to `.env` and adjust values (database, Redis, `SECRET_KEY`).

3. **Default development settings** (`USE_SQLITE=True` in `.env`): SQLite database, in-memory cache, and in-memory Channels layer — no Docker required for `migrate`, `runserver`, or tests. Set `USE_SQLITE=False` and configure PostgreSQL + Redis for production-like local runs.

4. Run migrations:

```bash
python manage.py migrate
python manage.py createsuperuser
```

5. If `USE_SQLITE=False`, start PostgreSQL and Redis locally (or use Docker Compose).

6. Run the ASGI server (WebSockets):

```bash
daphne -b 127.0.0.1 -p 8000 config.asgi:application
```

Or for development:

```bash
python manage.py runserver
```

Note: `runserver` does not serve Channels WebSockets; use **Daphne** or **uvicorn** with `config.asgi:application` for full real-time support.

### Celery (optional)

7. Worker:

```bash
celery -A celery_tasks worker -l info
```

8. Beat (periodic tasks):

```bash
celery -A celery_tasks beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

## API documentation

- OpenAPI schema: `/api/schema/`
- Swagger UI: `/api/docs/`

## Docker

From the `docker/` directory:

```bash
docker compose up --build
```

Set `SECRET_KEY`, `DB_PASSWORD`, and `ALLOWED_HOSTS` in the environment or an `.env` file next to `docker-compose.yml`.

## Production deployment (বিস্তারিত বাংলা গাইড)

প্রোডাকশনে কী কী সেবা লাগবে, কোথা থেকে লিংক/কী নেবেন, ডাটাবেজ ও Redis কীভাবে কানেক্ট করবেন — সম্পূর্ণ ধাপ: **[docs/PRODUCTION_DEPLOYMENT_GUIDE_BN.md](docs/PRODUCTION_DEPLOYMENT_GUIDE_BN.md)**।

অতিরিক্ত:
- লোকাল টেস্ট + প্রোড + B2 + Cloudflare: **[docs/LOCAL_TESTING_AND_PRODUCTION_BN.md](docs/LOCAL_TESTING_AND_PRODUCTION_BN.md)**
- API/token testing (Google/Facebook সহ): **[docs/API_TOKEN_TESTING_GUIDE_BN.md](docs/API_TOKEN_TESTING_GUIDE_BN.md)**

## Authentication

- Obtain tokens: `POST /api/v1/auth/login/` with JSON body `{"email": "...", "password": "..."}`.
- Pass `Authorization: Bearer <access_token>` on API requests.
- WebSockets: append `?token=<access_token>` to the WebSocket URL.

## Project layout

- `config/` — settings (`base`, `development`, `production`), `urls`, `asgi`, `wsgi`
- `apps/` — domain apps (`users`, `posts`, `messages`, …)
- `core/` — shared permissions, pagination, auth, throttling, utilities
- `websocket/` — Channels routing, JWT middleware, consumers (chat, notifications, calls)
- `celery_tasks/` — Celery app and background tasks
"# OnneTime" 
"# OnneTime" 
