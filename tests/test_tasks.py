"""Tests for /tasks CRUD + ownership + pagination/filter.

The ownership tests are the most important in this file: they prove the
security boundary from the "enforce task ownership" commit actually holds —
user B gets 404 (not 403, not the task) for user A's tasks.
"""

from fastapi import status


def _register_and_login(client, email):
    client.post("/auth/register", json={"email": email, "password": "secret123"})
    response = client.post(
        "/auth/login", data={"username": email, "password": "secret123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_task(client, auth_headers):
    response = client.post(
        "/tasks",
        json={"title": "Buy milk", "priority": "high"},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["title"] == "Buy milk"
    assert body["status"] == "todo"  # server default
    assert body["priority"] == "high"
    assert "owner_id" in body


def test_create_task_rejects_empty_title(client, auth_headers):
    response = client.post("/tasks", json={"title": ""}, headers=auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_list_tasks_returns_only_own_tasks(client, auth_headers):
    other = _register_and_login(client, "other@example.com")
    client.post("/tasks", json={"title": "mine"}, headers=auth_headers)
    client.post("/tasks", json={"title": "theirs"}, headers=other)

    response = client.get("/tasks", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    titles = [t["title"] for t in response.json()]
    assert titles == ["mine"]


def test_list_tasks_pagination(client, auth_headers):
    for i in range(5):
        client.post("/tasks", json={"title": f"task {i}"}, headers=auth_headers)

    page1 = client.get("/tasks?skip=0&limit=2", headers=auth_headers).json()
    page2 = client.get("/tasks?skip=2&limit=2", headers=auth_headers).json()
    assert len(page1) == 2
    assert len(page2) == 2
    assert {t["id"] for t in page1}.isdisjoint({t["id"] for t in page2})


def test_list_tasks_status_filter(client, auth_headers):
    task_id = client.post(
        "/tasks", json={"title": "finish me"}, headers=auth_headers
    ).json()["id"]
    client.post("/tasks", json={"title": "later"}, headers=auth_headers)
    client.patch(
        f"/tasks/{task_id}", json={"status": "done"}, headers=auth_headers
    )

    done = client.get("/tasks?status=done", headers=auth_headers).json()
    assert [t["id"] for t in done] == [task_id]


def test_get_task(client, auth_headers):
    task_id = client.post(
        "/tasks", json={"title": "read me"}, headers=auth_headers
    ).json()["id"]
    response = client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["title"] == "read me"


def test_get_missing_task_returns_404(client, auth_headers):
    response = client.get("/tasks/999999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_cannot_read_other_users_task(client, auth_headers):
    other = _register_and_login(client, "victim@example.com")
    task_id = client.post(
        "/tasks", json={"title": "secret"}, headers=other
    ).json()["id"]
    # 404, not 403 — we reveal nothing about the task's existence.
    response = client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_cannot_update_other_users_task(client, auth_headers):
    other = _register_and_login(client, "victim2@example.com")
    task_id = client.post(
        "/tasks", json={"title": "secret"}, headers=other
    ).json()["id"]
    response = client.patch(
        f"/tasks/{task_id}", json={"title": "hacked"}, headers=auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_cannot_delete_other_users_task(client, auth_headers):
    other = _register_and_login(client, "victim3@example.com")
    task_id = client.post(
        "/tasks", json={"title": "secret"}, headers=other
    ).json()["id"]
    response = client.delete(f"/tasks/{task_id}", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    # And the task still exists for its owner.
    assert (
        client.get(f"/tasks/{task_id}", headers=other).status_code
        == status.HTTP_200_OK
    )


def test_update_task_partial(client, auth_headers):
    task_id = client.post(
        "/tasks",
        json={"title": "original", "description": "keep me"},
        headers=auth_headers,
    ).json()["id"]
    response = client.patch(
        f"/tasks/{task_id}", json={"status": "in_progress"}, headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["status"] == "in_progress"
    assert body["title"] == "original"  # untouched fields survive
    assert body["description"] == "keep me"


def test_delete_task(client, auth_headers):
    task_id = client.post(
        "/tasks", json={"title": "bye"}, headers=auth_headers
    ).json()["id"]
    response = client.delete(f"/tasks/{task_id}", headers=auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert (
        client.get(f"/tasks/{task_id}", headers=auth_headers).status_code
        == status.HTTP_404_NOT_FOUND
    )
