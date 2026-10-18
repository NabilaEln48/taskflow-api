"""User ORM model.

Design notes for juniors:
- `hashed_password`, never a plain `password` column. The hash is one-way:
  even with full DB access you can't recover the original password.
- `unique=True` on email: the DB itself rejects duplicates, so we don't rely
  on "check then insert" (which races under concurrency).
- `index=True` on email: logins look users up by email on every request, and
  an index turns that from a full table scan into a fast lookup.
- `server_default=func.now()`: the timestamp is set by Postgres itself, so it
  stays correct even if app servers disagree about the time.
"""

from datetime import datetime

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # One user -> many tasks. `back_populates` keeps both sides in sync:
    # task.owner and user.tasks always agree. `cascade="all, delete-orphan"`
    # means deleting a user also deletes their tasks (no orphan rows).
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
