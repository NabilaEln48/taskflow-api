from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.exceptions import register_exception_handlers
from app.routers import auth, tasks

app = FastAPI(
    title="taskflow-api",
    description="Task management REST API — project 1 of a 15-project backend series.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tasks.router)

register_exception_handlers(app)

@app.get("/health", tags=["ops"])
def healthcheck() -> dict:
    return {"status": "ok"}
