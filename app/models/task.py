"""Task ORM model.

Key modeling choices:

- `status` and `priority` are plain strings with server defaults, not
  Postgres ENUMs. ENUMs are painful to change later (adding a value needs a
  migration that rewrites the type); strings validated by Pydantic give the
  same safety with zero migration pain. This is a deliberate, common
  production trade-off.
- `owner_id` FK with `ondelete="CASCADE"`: the database itself guarantees
  no task survives its owner, even if someone deletes the user via raw SQL
  bypassing our ORM cascade.
- `due_date` is nullable: a task without a deadline is valid, and NULL is
  the honest representation (vs. a magic far-future date).
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TaskStatus(str, enum.Enum):
    """Allowed status values. str-enum so JSON renders as plain strings."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), server_default=TaskStatus.TODO.value
    )
    priority: Mapped[str] = mapped_column(
        String(20), server_default=TaskPriority.MEDIUM.value
    )
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # index=True: "all tasks for user X" is our hottest query (every list
    # call), so the FK gets its own index.

    owner: Mapped["User"] = relationship(back_populates="tasks")
