"""Direct database-level tests: constraints, foreign keys, and views.

These bypass Flask entirely and hit MySQL directly via db.py,
to confirm the database itself enforces its own rules.
"""
import pytest
import mysql.connector
import seed
import db


@pytest.fixture(autouse=True)
def reset_db():
    seed.reset()
    seed.seed()


def test_duplicate_email_rejected_at_db_level():
    """The UNIQUE constraint on users.email should block duplicates
    even if Flask's own check were ever removed or buggy."""
    with pytest.raises(mysql.connector.errors.IntegrityError):
        db.execute(
            "INSERT INTO users (building_id, name, email, password_hash, role) "
            "VALUES (%s, %s, %s, %s, %s)",
            (1, "Dup Test", "adiallo@citymail.cuny.edu", "hash", "tenant"),
        )


def test_booking_with_invalid_user_id_rejected():
    """Foreign key on bookings.user_id should reject a non-existent user."""
    with pytest.raises(mysql.connector.errors.IntegrityError):
        db.execute(
            "INSERT INTO bookings (user_id, machine_id, start_time, end_time, "
            "price_at_booking, booking_status) VALUES (%s, %s, %s, %s, %s, %s)",
            (999999, 1, "2026-08-01 09:00:00", "2026-08-01 09:30:00", 2.00, "confirmed"),
        )


def test_booking_with_invalid_machine_id_rejected():
    """Foreign key on bookings.machine_id should reject a non-existent machine."""
    with pytest.raises(mysql.connector.errors.IntegrityError):
        db.execute(
            "INSERT INTO bookings (user_id, machine_id, start_time, end_time, "
            "price_at_booking, booking_status) VALUES (%s, %s, %s, %s, %s, %s)",
            (1, 999999, "2026-08-01 09:00:00", "2026-08-01 09:30:00", 2.00, "confirmed"),
        )


def test_cannot_delete_building_with_dependent_machines():
    """No ON DELETE CASCADE is defined, so deleting a building that still
    has machines attached should be blocked, not silently cascade."""
    with pytest.raises(mysql.connector.errors.IntegrityError):
        db.execute("DELETE FROM buildings WHERE building_id = %s", (1,))


def test_view_active_subscriptions_only_shows_active():
    """v_active_subscriptions should never include cancelled/expired rows."""
    rows = db.query("SELECT * FROM v_active_subscriptions")
    assert len(rows) > 0
    for r in rows:
        assert r["subscription_status"] == "active"
