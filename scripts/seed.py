"""Seed the database with a demo user and sample tasks.

Run:  python scripts/seed.py
Requires: DATABASE_URL pointing at a migrated database
          (docker compose up -d && alembic upgrade head)

Why a seed script instead of manual /docs clicking?
- One command rebuilds a realistic dev state after `alembic downgrade base`.
- New contributors (or future-you) get productive in seconds.
- It's also a smoke test: if seeding works, the models + DB agree.

Idempotent: re-running won't duplicate anything (checks by email first).
"""

from sqlalchemy import select

from app.core.security import hash_password
from app.database import SessionLocal
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User

DEMO_EMAIL = "demo@taskflow.dev"
DEMO_PASSWORD = "demo1234"

SAMPLE_TASKS = [
    ("Set up the repo", "Clone, venv, docker compose up", TaskStatus.DONE, TaskPriority.HIGH),
    ("Write the Task model", "fields, enums, owner FK", TaskStatus.DONE, TaskPriority.HIGH),
    ("Add JWT auth", "python-jose + passlib, 30-min tokens", TaskStatus.IN_PROGRESS, TaskPriority.HIGH),
    ("Write tests", "pytest + httpx, ownership edge cases", TaskStatus.TODO, TaskPriority.MEDIUM),
    ("Deploy someday", "Docker, CI, the works", TaskStatus.TODO, TaskPriority.LOW),
]


def main() -> None:
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == DEMO_EMAIL))
        if user is None:
            user = User(email=DEMO_EMAIL, hashed_password=hash_password(DEMO_PASSWORD))
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"created user {DEMO_EMAIL}")
        else:
            print(f"user {DEMO_EMAIL} already exists")

        existing = db.scalar(
            select(Task).where(Task.owner_id == user.id).limit(1)
        )
        if existing is None:
            for title, desc, status_, priority in SAMPLE_TASKS:
                db.add(
                    Task(
                        title=title,
                        description=desc,
                        status=status_.value,
                        priority=priority.value,
                        owner_id=user.id,
                    )
                )
            db.commit()
            print(f"seeded {len(SAMPLE_TASKS)} tasks")
        else:
            print("tasks already seeded")
    finally:
        db.close()


if __name__ == "__main__":
    main()
