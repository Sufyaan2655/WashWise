"""Authentication and role/ownership access-control tests."""

import pytest

import app as app_module
import seed
from test_api import auth_headers


@pytest.fixture(scope="module")
def client():
    seed.reset()
    seed.seed()
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def test_protected_route_without_token_is_401(client):
    res = client.get("/users/1/bookings")
    assert res.status_code == 401


def test_protected_route_with_garbage_token_is_401(client):
    res = client.get("/users/1/bookings", headers={"Authorization": "Bearer not-a-real-token"})
    assert res.status_code == 401


def test_protected_route_with_malformed_header_is_401(client):
    res = client.get("/users/1/bookings", headers={"Authorization": "not-even-bearer"})
    assert res.status_code == 401


def test_tenant_cannot_read_another_tenants_bookings(client):
    # user 1 (adiallo, tenant) trying to read user 2's (mlopez) bookings
    res = client.get("/users/2/bookings", headers=auth_headers(client, "adiallo@citymail.cuny.edu"))
    assert res.status_code == 403


def test_tenant_can_read_their_own_bookings(client):
    res = client.get("/users/1/bookings", headers=auth_headers(client, "adiallo@citymail.cuny.edu"))
    assert res.status_code == 200


def test_manager_can_read_any_tenants_bookings(client):
    res = client.get("/users/1/bookings", headers=auth_headers(client, "maplemanager@example.com"))
    assert res.status_code == 200


def test_tenant_cannot_update_machine_status(client):
    res = client.patch("/machines/1", json={"status": "maintenance"},
                        headers=auth_headers(client, "adiallo@citymail.cuny.edu"))
    assert res.status_code == 403


def test_manager_can_update_machine_status(client):
    res = client.patch("/machines/1", json={"status": "active"},
                        headers=auth_headers(client, "maplemanager@example.com"))
    assert res.status_code == 200


def test_tenant_cannot_create_subscription(client):
    res = client.post("/subscriptions", json={
        "building_id": 1, "plan_id": 1, "start_date": "2026-08-01",
    }, headers=auth_headers(client, "adiallo@citymail.cuny.edu"))
    assert res.status_code == 403


def test_tenant_cannot_view_revenue_report(client):
    res = client.get("/reports/revenue", headers=auth_headers(client, "adiallo@citymail.cuny.edu"))
    assert res.status_code == 403


def test_manager_can_view_revenue_report(client):
    res = client.get("/reports/revenue", headers=auth_headers(client, "maplemanager@example.com"))
    assert res.status_code == 200


def test_tenant_cannot_book_on_behalf_of_another_tenant(client):
    res = client.post("/bookings", json={
        "user_id": 2, "machine_id": 1,
        "start_time": "2026-07-12 09:00:00", "end_time": "2026-07-12 09:30:00",
        "price_at_booking": 2.50,
    }, headers=auth_headers(client, "adiallo@citymail.cuny.edu"))
    assert res.status_code == 403


def test_login_returns_a_usable_token(client):
    res = client.post("/login", json={"email": "adiallo@citymail.cuny.edu", "password": seed.DEMO_PASSWORD})
    assert res.status_code == 200
    token = res.get_json()["token"]
    assert token

    me = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.get_json()["email"] == "adiallo@citymail.cuny.edu"
