"""API tests. Each test gets a fresh in-memory database."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def auth_header(client, email="dinesh@example.com", password="secret123"):
    client.post("/auth/register", json={"email": email, "password": password})
    r = client.post("/auth/login", data={"username": email, "password": password})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_register_and_login(client):
    r = client.post("/auth/register", json={"email": "a@b.com", "password": "secret123"})
    assert r.status_code == 201
    assert r.json()["email"] == "a@b.com"

    r = client.post("/auth/login", data={"username": "a@b.com", "password": "secret123"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_duplicate_email_rejected(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "secret123"})
    r = client.post("/auth/register", json={"email": "a@b.com", "password": "secret123"})
    assert r.status_code == 409


def test_wrong_password(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "secret123"})
    r = client.post("/auth/login", data={"username": "a@b.com", "password": "wrong!!"})
    assert r.status_code == 401


def test_protected_route_needs_token(client):
    assert client.get("/expenses").status_code == 401


def test_crud_flow(client):
    h = auth_header(client)
    r = client.post(
        "/expenses",
        json={"title": "Lunch", "amount": 180, "category": "food", "spent_on": "2026-11-01"},
        headers=h,
    )
    assert r.status_code == 201
    eid = r.json()["id"]

    assert client.get(f"/expenses/{eid}", headers=h).json()["title"] == "Lunch"

    r = client.patch(f"/expenses/{eid}", json={"amount": 200}, headers=h)
    assert r.json()["amount"] == 200
    assert r.json()["title"] == "Lunch"  # untouched fields stay the same

    assert client.delete(f"/expenses/{eid}", headers=h).status_code == 204
    assert client.get(f"/expenses/{eid}", headers=h).status_code == 404


def test_validation_rejects_bad_input(client):
    h = auth_header(client)
    r = client.post("/expenses", json={"title": "X", "amount": -5}, headers=h)
    assert r.status_code == 422
    r = client.post("/expenses", json={"title": "X", "amount": 5, "category": "party"}, headers=h)
    assert r.status_code == 422


def test_filters_and_summary(client):
    h = auth_header(client)
    items = [
        ("Bus", 50, "travel", "2026-10-05"),
        ("Dinner", 400, "food", "2026-10-20"),
        ("Snacks", 100, "food", "2026-11-02"),
    ]
    for title, amt, cat, d in items:
        client.post(
            "/expenses",
            json={"title": title, "amount": amt, "category": cat, "spent_on": d},
            headers=h,
        )

    food = client.get("/expenses?category=food", headers=h).json()
    assert len(food) == 2

    october = client.get("/expenses?start=2026-10-01&end=2026-10-31", headers=h).json()
    assert {e["title"] for e in october} == {"Bus", "Dinner"}

    s = client.get("/expenses/summary", headers=h).json()
    assert s["total"] == 550
    assert s["count"] == 3
    assert s["by_category"] == {"food": 500, "travel": 50}


def test_users_cannot_see_each_others_expenses(client):
    h1 = auth_header(client, "one@x.com")
    h2 = auth_header(client, "two@x.com")
    eid = client.post("/expenses", json={"title": "Rent", "amount": 9000, "category": "rent"}, headers=h1).json()["id"]

    assert client.get(f"/expenses/{eid}", headers=h2).status_code == 404
    assert client.delete(f"/expenses/{eid}", headers=h2).status_code == 404
    assert client.get("/expenses", headers=h2).json() == []
