"""Pytest fixtures: isolated test database + authenticated clients.

The key pattern: `app.dependency_overrides`.

In production, `get_db` yields a Postgres session. In tests we swap it for
an in-memory SQLite session — same Session interface, zero Postgres needed.
This is WHY we wrote `get_db` as a dependency instead of importing
SessionLocal directly in routers: dependencies are swappable seams.

Isolation: the DB is created fresh per TEST FUNCTION (function-scoped
fixtures). Each test starts with empty tables, so tests can't pollute each
other no matter what order they run in. SQLite in-memory is fast enough
that this costs milliseconds.

Note: SQLite can't run our Postgres migrations, so tests create tables via
`Base.metadata.create_all` — good enough, because migration correctness is
verified separately (we did the upgrade/downgrade cycle by hand).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# StaticPool + in-memory: a single shared connection, so the tables created
# in the fixture are visible to the sessions the app opens per request.
# (Without it, each connection would get its own EMPTY in-memory DB.)
TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # closed by the db_session fixture itself

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client):
    """Register a user and return headers with a valid Bearer token."""
    client.post(
        "/auth/register",
        json={"email": "tester@example.com", "password": "secret123"},
    )
    response = client.post(
        "/auth/login",
        data={"username": "tester@example.com", "password": "secret123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
