"""Database engine, session factory and declarative base.

The three objects every SQLAlchemy app needs:

- `engine`: the actual connection pool to Postgres. Created once at import
  time and shared — creating engines per-request would leak connections.
- `SessionLocal`: a factory that produces one `Session` per request. Each
  session is a single unit of work (one request = one session = one
  transaction); it must be closed after the request, which `get_db` handles.
- `Base`: the parent class every ORM model inherits from. SQLAlchemy uses it
  to collect table metadata, which is also what Alembic reads to
  auto-generate migrations.

`get_db` is a FastAPI *dependency*: endpoints declare
`db: Session = Depends(get_db)` and FastAPI calls this generator, yields the
session into the endpoint, then runs the code after `yield` (closing the
session) when the request finishes — even if the endpoint raised.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# pool_pre_ping=True: before handing out a pooled connection, send a cheap
# "SELECT 1". Stale connections (e.g. Postgres restarted overnight) are
# transparently recycled instead of failing the first real query.
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# autocommit=False: nothing hits the DB until we call db.commit() explicitly.
# autoflush=False: queries don't implicitly flush pending changes first —
# we stay in control of exactly when SQL is emitted.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all ORM models. Subclasses become tables."""

    pass


def get_db():
    """Yield a request-scoped DB session, then always close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
