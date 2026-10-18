"""FastAPI application entry point.

Run with:  uvicorn app.main:app --reload
Docs at:   http://localhost:8000/docs  (interactive Swagger UI)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, tasks

app = FastAPI(
    title="taskflow-api",
    description="Task management REST API — project 1 of a 15-project backend series.",
    version="0.1.0",
)

# CORS: browsers block cross-origin requests by default. Our frontend (when we
# build one) will run on a different origin, so we allow it explicitly.
# allow_origins=["*"] is fine for local dev; in production, list the exact
# frontend domain(s) — "*" with credentials is a security hole.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tasks.router)


@app.get("/health", tags=["ops"])
def healthcheck() -> dict:
    """Liveness probe: load balancers / Docker / uptime monitors hit this.

    It does NOT touch the database on purpose — a healthcheck should answer
    "is the process alive", not "is everything perfect". (A separate
    /ready endpoint that pings the DB is the next step in real systems.)
    """
    return {"status": "ok"}
