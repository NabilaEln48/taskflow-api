# taskflow-api

Task management REST API built with FastAPI, PostgreSQL, SQLAlchemy 2.0 and JWT authentication.

> Project 1 of a 15-project backend series.

## Quickstart

```bash
docker compose up -d          # start Postgres
pip install -e ".[dev]"
alembic upgrade head          # run migrations
uvicorn app.main:app --reload
```

Docs: http://localhost:8000/docs

Full documentation below (work in progress).
