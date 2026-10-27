import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / "test.db")) as client:
        yield client


def add_user(client, name="Alice", email="alice@example.com"):
    return client.post("/users", json={"name": name, "email": email})


def test_user_lifecycle(client):
    response = add_user(client)
    assert response.status_code == 201
    user = response.json()
    assert user["created_at"]
    url = f"/users/{user['id']}"
    assert client.get(url).json() == user
    assert client.get("/users").json() == [user]
    response = client.patch(url, json={"name": " Alice Smith "})
    assert response.status_code == 200
    assert response.json()["name"] == "Alice Smith"
    assert response.json()["email"] == user["email"]
    assert client.get(url).json()["name"] == "Alice Smith"
    response = client.delete(url)
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(url).status_code == 404
    assert client.get("/users").json() == []


def test_duplicate_email(client):
    add_user(client)
    assert add_user(client, email="ALICE@example.com").status_code == 409
    bob = add_user(client, "Bob", "bob@example.com").json()
    url = f"/users/{bob['id']}"
    assert client.patch(url, json={"email": "alice@example.com"}).status_code == 409
    assert client.get(url).json()["email"] == "bob@example.com"
    assert client.patch(url, json={"email": "new@example.com"}).status_code == 200


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_missing_user(client, method):
    kwargs = {"json": {"name": "Alice"}} if method == "patch" else {}
    assert getattr(client, method)("/users/999", **kwargs).status_code == 404


@pytest.mark.parametrize(
    "payload",
    [
        {"name": " ", "email": "alice@example.com"},
        {"name": "Alice", "email": "invalid"},
        {"name": "Alice"},
        {"name": "Alice", "email": "alice@example.com", "admin": True},
    ],
)
def test_invalid_create(client, payload):
    assert client.post("/users", json=payload).status_code == 422


@pytest.mark.parametrize("payload", [{}, {"name": None}, {"email": None}, {"name": ""}])
def test_invalid_update(client, payload):
    user = add_user(client).json()
    assert client.patch(f"/users/{user['id']}", json=payload).status_code == 422


def test_pagination(client):
    first = add_user(client).json()
    second = add_user(client, "Bob", "bob@example.com").json()
    assert client.get("/users?limit=1").json() == [first]
    assert client.get("/users?limit=1&offset=1").json() == [second]
    assert client.get("/users?limit=0").status_code == 422
    assert client.get("/users?offset=-1").status_code == 422


def test_data_survives_restart(tmp_path):
    database = tmp_path / "persistent.db"
    with TestClient(create_app(database)) as client:
        user = add_user(client).json()
    with TestClient(create_app(database)) as client:
        assert client.get(f"/users/{user['id']}").json() == user
