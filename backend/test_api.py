"""Automated API tests for the WashWise backend.

The suite re-seeds the database first, so it always runs against known data.
"""

import pytest

import app as app_module
import seed


@pytest.fixture(scope="module")
def client():
    seed.reset()
    seed.seed()
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def auth_headers(client, email, password=seed.DEMO_PASSWORD):
    """Log in as a demo user and return an Authorization header dict."""
    res = client.post("/login", json={"email": email, "password": password})
    token = res.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["database"] == "connected"


def test_list_buildings(client):
    res = client.get("/buildings")
    assert res.status_code == 200
    assert len(res.get_json()) == 3


def test_users_never_expose_password(client):
    users = client.get("/users").get_json()
    assert users
    assert all("password_hash" not in u for u in users)


def test_create_user_and_login(client):
    created = client.post("/users", json={
        "building_id": 1, "name": "Pytest User", "email": "pytest@test.com",
        "password": "pw123456", "role": "tenant",
    })
    assert created.status_code == 201
    ok = client.post("/login", json={"email": "pytest@test.com", "password": "pw123456"})
    assert ok.status_code == 200
    assert ok.get_json()["role"] == "tenant"


def test_login_wrong_password(client):
    res = client.post("/login", json={"email": "pytest@test.com", "password": "nope"})
    assert res.status_code == 401


def test_missing_fields_returns_400(client):
    res = client.post("/users", json={"name": "no other fields"})
    assert res.status_code == 400
    assert "missing" in res.get_json()["error"]


def test_duplicate_email_returns_409(client):
    res = client.post("/users", json={
        "building_id": 1, "name": "Dupe", "email": "adiallo@citymail.cuny.edu",
        "password": "x", "role": "tenant",
    })
    assert res.status_code == 409


def test_booking_respects_machine_operational_status(client):
    # A booking on an operational ('active') machine succeeds. Machine status is
    # operational state, not availability, so it stays 'active' after booking.
    created = client.post("/bookings", json={
        "user_id": 1, "machine_id": 2,
        "start_time": "2026-07-09 08:00:00", "end_time": "2026-07-09 08:30:00",
        "price_at_booking": 2.00,
    }, headers=auth_headers(client, "adiallo@citymail.cuny.edu"))
    assert created.status_code == 201

    machines = client.get("/machines?building_id=1").get_json()
    m2 = next(m for m in machines if m["machine_id"] == 2)
    assert m2["status"] == "active"

    # A booking on a machine under maintenance is rejected by the DB trigger.
    # Put machine 6 under maintenance first so the test does not depend on seed data.
    client.patch("/machines/6", json={"status": "maintenance"},
                 headers=auth_headers(client, "fnoor@example.com"))
    rejected = client.post("/bookings", json={
        "user_id": 5, "machine_id": 6,
        "start_time": "2026-07-09 10:00:00", "end_time": "2026-07-09 10:30:00",
        "price_at_booking": 2.00,
    }, headers=auth_headers(client, "wchen@example.com"))
    assert rejected.status_code == 400


def test_booking_payment_splits_fee(client):
    res = client.post("/booking-payments", json={
        "booking_id": 1, "gross_amount": 2.50,
    })
    assert res.status_code == 201
    body = res.get_json()
    # 15% of 2.50 = 0.375 -> 0.38 fee, 2.12 to building
    assert body["transaction_fee"] == 0.38
    assert body["building_amount"] == 2.12


def test_plans_and_subscriptions(client):
    plans = client.get("/plans").get_json()
    assert len(plans) == 3
    subs = client.get("/subscriptions").get_json()
    assert len(subs) == 3


def test_revenue_report_has_both_streams(client):
    rows = client.get("/reports/revenue",
                       headers=auth_headers(client, "jcarter@example.com")).get_json()
    assert len(rows) == 3
    assert "booking_revenue" in rows[0]
    assert "subscription_revenue" in rows[0]


def test_excel_export(client):
    res = client.get("/reports/revenue/export",
                      headers=auth_headers(client, "jcarter@example.com"))
    assert res.status_code == 200
    assert "spreadsheet" in res.headers["Content-Type"]


def test_double_booking_same_machine_overlap(client):
    """Two overlapping bookings on the same machine must be rejected."""
    first = client.post("/bookings", json={
        "user_id": 4, "machine_id": 3,
        "start_time": "2026-07-10 09:00:00", "end_time": "2026-07-10 09:30:00",
        "price_at_booking": 2.00,
    }, headers=auth_headers(client, "jcarter@example.com"))
    assert first.status_code == 201

    second = client.post("/bookings", json={
        "user_id": 3, "machine_id": 3,
        "start_time": "2026-07-10 09:10:00", "end_time": "2026-07-10 09:40:00",
        "price_at_booking": 2.00,
    }, headers=auth_headers(client, "maplemanager@example.com"))
    assert second.status_code == 409


def test_cancel_nonexistent_booking_returns_404(client):
    res = client.delete("/bookings/999999",
                         headers=auth_headers(client, "adiallo@citymail.cuny.edu"))
    assert res.status_code == 404


def test_invalid_machine_status_rejected(client):
    res = client.patch("/machines/1", json={"status": "not_a_real_status"},
                        headers=auth_headers(client, "jcarter@example.com"))
    assert res.status_code == 400


def test_negative_payment_amount_rejected(client):
    res = client.post("/booking-payments", json={
        "booking_id": 2, "gross_amount": -5.00,
    })
    assert res.status_code == 400


def test_booking_missing_machine_id_returns_400(client):
    res = client.post("/bookings", json={
        "user_id": 1,
        "start_time": "2026-07-11 09:00:00", "end_time": "2026-07-11 09:30:00",
        "price_at_booking": 2.00,
    }, headers=auth_headers(client, "adiallo@citymail.cuny.edu"))
    assert res.status_code == 400

def test_valid_subscription_payment_created(client):
    """A valid subscription payment should be accepted."""
    res = client.post("/subscription-payments", json={
        "subscription_id": 1,
        "amount": 49.00,
        "payment_status": "pending",
        "billing_period_start": "2026-08-01",
        "billing_period_end": "2026-08-31",
    })

    assert res.status_code == 201
    assert "subscription_payment_id" in res.get_json()


@pytest.mark.parametrize(
    ("payload", "expected_error"),
    [
        (
            {
                "subscription_id": 1,
                "amount": -99.00,
                "payment_status": "paid",
                "billing_period_start": "2026-08-01",
                "billing_period_end": "2026-08-31",
            },
            "amount must be positive",
        ),
        (
            {
                "subscription_id": 1,
                "amount": 49.00,
                "payment_status": "paid",
                "billing_period_start": "2026-08-31",
                "billing_period_end": "2026-08-01",
            },
            "billing_period_end must be on or after billing_period_start",
        ),
        (
            {
                "subscription_id": 1,
                "amount": 49.00,
                "payment_status": "declined",
                "billing_period_start": "2026-08-01",
                "billing_period_end": "2026-08-31",
            },
            "payment_status must be one of: paid, pending, refunded",
        ),
    ],
)
def test_invalid_subscription_payment_rejected(
    client,
    payload,
    expected_error,
):
    """Invalid subscription payment data should return HTTP 400."""
    res = client.post("/subscription-payments", json=payload)

    assert res.status_code == 400
    assert expected_error in res.get_json()["error"]
