# File Manager API

FastAPI backend for authenticated file uploads with PostgreSQL.

## Development Setup

1. Copy `.env.example` to `.env` and fill values.
2. Set `IS_DEBUG=1` if you want FastAPI docs (`/docs`, `/redoc`) locally; leave as `0` for production.
3. Install dependencies (Pipenv): `pipenv install --dev`.
4. Run the server: `pipenv run uvicorn main:app --reload`.


## Production Setup

1. Set environment variables by following `.env.example` (set `IS_DEBUG=0` to disable API docs in production).
2. Install dependencies (Pipenv): `pipenv requirements > requirements.txt && pip install -r requirements.txt`.
3. Run the server: `uvicorn main:app --host 0.0.0.0 --port $PORT`.

## Database Migrations (Alembic)

- Apply migrations: `pipenv run alembic upgrade head`
- Roll back last migration: `pipenv run alembic downgrade -1`
- Migrations read env vars (e.g., `DATABASE_URL`), so ensure your `.env` is in place before running them.
