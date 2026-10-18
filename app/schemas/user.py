"""Pydantic schemas for users.

Why separate schemas instead of reusing the ORM model?
- The ORM model has `hashed_password` — it must NEVER be serialized to a
  client. Separate response schemas make leaking it structurally impossible.
- Requests and responses have different shapes: registration takes a plain
  `password`, but responses must not echo it back.
- `from_attributes=True` (Pydantic v2's name for orm_mode) lets us build a
  response schema directly from a SQLAlchemy object: `UserOut.model_validate(user)`.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    """What a client sends to register. Plain password — hashed before storage."""

    email: EmailStr  # validates format AND normalizes; garbage in -> 422 out
    password: str  # plain text on the wire (use HTTPS in production!)


class UserOut(BaseModel):
    """What the API returns about a user. Note: no password field at all."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    created_at: datetime
