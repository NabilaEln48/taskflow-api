"""Pydantic schemas for tasks.

Three schemas because create, update and response are three different jobs:

- `TaskCreate`: everything required to make a task. `title` is mandatory;
  everything else has a sensible default (status=todo, priority=medium).
- `TaskUpdate`: every field optional — PATCH semantics. A client sends only
  what changed. (We implement it as PUT-replace-friendly too, but the
  schema shape is what matters.)
- `TaskOut`: what the API returns. Includes server-owned fields (id,
  owner_id, timestamps) that clients must never send.

Reusing the enums from the ORM model keeps the allowed values defined in
exactly one place — the schema and the DB can never disagree.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.task import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: datetime | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: datetime | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: datetime | None
    owner_id: int
    created_at: datetime
    updated_at: datetime
