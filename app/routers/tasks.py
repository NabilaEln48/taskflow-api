"""Task CRUD routes.

Ownership rule: a user can only ever see or touch their OWN tasks.
Enforcement points (this is the entire security boundary — 3 small changes):

1. `list_tasks` filters `WHERE owner_id == current_user.id` — you can't
   even *see* that someone else's tasks exist.
2. `_get_owned_task_or_404` replaces the old helper: fetching by
   (id, owner_id) in ONE query means "not yours" and "doesn't exist" both
   return 404. Returning 403 ("it exists but isn't yours") would leak which
   task ids are real — 404 reveals nothing.
3. Create already stamped `owner_id=current_user.id`, so new tasks are born
   owned. (The client never sends owner_id — it's derived from the token.)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.schemas.task import TaskCreate, TaskOut, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _get_owned_task_or_404(db: Session, task_id: int, user: User) -> Task:
    """Fetch one task ONLY if it belongs to `user`, else 404.

    One query with both conditions — never fetch-then-check in Python, which
    is both slower and easier to forget on a new endpoint.
    """
    task = db.scalar(
        select(Task).where(Task.id == task_id, Task.owner_id == user.id)
    )
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return task


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    task = Task(**payload.model_dump(), owner_id=current_user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("", response_model=list[TaskOut])
def list_tasks(
    # Pagination: `skip`/`limit` are the simplest scheme and fine at this
    # scale. (Cursor pagination wins for huge, fast-changing feeds — not here.)
    skip: int = 0,
    limit: int = 20,
    # Optional filter: /tasks?status=done. None means "all statuses".
    status: TaskStatus | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Task]:
    # Guardrails: negative skip is nonsense; cap limit so one request can't
    # ask for a million rows and melt the DB.
    skip = max(skip, 0)
    limit = min(max(limit, 1), 100)

    query = (
        select(Task)
        .where(Task.owner_id == current_user.id)
        .order_by(Task.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    if status is not None:
        query = query.where(Task.status == status.value)
    return list(db.scalars(query))


@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    return _get_owned_task_or_404(db, task_id, current_user)


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    task = _get_owned_task_or_404(db, task_id, current_user)
    # Only apply fields the client actually sent (PATCH semantics).
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    task = _get_owned_task_or_404(db, task_id, current_user)
    db.delete(task)
    db.commit()
    # 204 = success with empty body; returning None produces exactly that.
