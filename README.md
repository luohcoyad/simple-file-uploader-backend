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


## Architecture & Design Decisions

- FastAPI app with JWT auth (cookie and bearer) and server-side sessions stored in PostgreSQL.
- File metadata is stored in PostgreSQL; file binaries and thumbnails live in Supabase Storage with signed URLs.
- CORS is configurable; API docs (`/docs`, `/redoc`, `/openapi.json`) are enabled only when `IS_DEBUG=1`.
- Thumbnails are generated on upload for images (64px width, PNG) and stored in a dedicated bucket.

## Trade-offs / Known Limitations

- Uploads are read fully into memory; large uploads (capped at 50MB) can increase memory pressure.
- Storage keys strip original filenames to avoid invalid characters; the original name is kept only in metadata.
- No rate limiting or abuse protections are included.
- Thumbnail generation is synchronous; slow image processing slows the request.

## Future Improvements (Optional)

- Add JWT `/refresh` and `/me` APIs.
- Add Unit Test cases.
- Stream uploads to reduce memory usage.
- Implement JWT revoke with Redis rather than PostgreSQL.
- Add rate limiting, logging/metrics, and improved observability.
- Process File IO (upload, thumbnail, etc) `asynchronously`, such as using queue workers.
