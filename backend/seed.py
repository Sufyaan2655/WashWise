"""Seed the database with realistic demo data.

Idempotent: wipes the tables and re-inserts a consistent demo dataset.
All demo users share the password "demo1234" (hashed with werkzeug).
"""

from werkzeug.security import generate_password_hash

import db

DEMO_PASSWORD = "password123"
FEE_RATE = 0.15  # app keeps 15% of each booking as a transaction fee

TABLES = (
    "waitlist",
    "notifications",
    "subscription_payments",
    "booking_payments",
    "bookings",
    "building_subscriptions",
    "subscription_plans",
    "machines",
    "users",
    "buildings",
)


def reset():
    """Empty all tables and reset auto-increment counters."""
    conn = db.get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")
        for table in TABLES:
            cur.execute(f"TRUNCATE TABLE {table}")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1")
        conn.commit()
    finally:
        conn.close()


def seed():
    pw = generate_password_hash(DEMO_PASSWORD)

    # Buildings -> ids 1..3
    for name, address in [
        ("Maple Court Apartments", "120 Maple St, Bronx, NY 10453"),
        ("Riverside Towers", "88 Riverside Dr, New York, NY 10024"),
        ("Sunset Gardens", "450 Sunset Blvd, Brooklyn, NY 11220"),
    ]:
        db.execute("INSERT INTO buildings (name, address) VALUES (%s, %s)",
                   (name, address))

    # Users -> ids 1..6
    for building_id, name, email, phone, role in [
        (1, "Alhassana Diallo", "adiallo@citymail.cuny.edu", "+15555550101", "tenant"),
        (1, "Maria Lopez", "mlopez@example.com", "+15555550102", "tenant"),
        (1, "Maple Manager", "maplemanager@example.com", "+15555550103", "manager"),
        (2, "James Carter", "jcarter@example.com", "+15555550104", "manager"),
        (2, "Wei Chen", "wchen@example.com", "+15555550105", "tenant"),
        (3, "Fatima Noor", "fnoor@example.com", "+15555550106", "manager"),
    ]:
        db.execute(
            "INSERT INTO users (building_id, name, email, phone_number, password_hash, role) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (building_id, name, email, phone, pw, role),
        )

    # Machines -> ids 1..6 (status is operational state: 'active' | 'maintenance')
    for building_id, num, mtype, cost, duration, status in [
        (1, 1, "washer", 2.50, 30, "active"),
        (1, 2, "dryer", 2.00, 45, "active"),
        (2, 1, "washer", 3.00, 30, "active"),
        (2, 2, "dryer", 2.75, 40, "active"),
        (3, 1, "washer", 2.25, 35, "active"),
        (3, 2, "dryer", 2.25, 40, "active"),
    ]:
        db.execute(
            "INSERT INTO machines "
            "(building_id, machine_number, machine_type, cost_per_cycle, "
            "duration_minutes, status) VALUES (%s, %s, %s, %s, %s, %s)",
            (building_id, num, mtype, cost, duration, status),
        )

    # Subscription plans -> ids 1..3
    for name, period, price, max_machines, analytics in [
        ("Basic", "monthly", 49.00, 5, "basic"),
        ("Pro", "monthly", 99.00, 15, "advanced"),
        ("Enterprise", "monthly", 199.00, 50, "advanced"),
    ]:
        db.execute(
            "INSERT INTO subscription_plans "
            "(plan_name, billing_period, subscription_price, max_machines, analytics_level) "
            "VALUES (%s, %s, %s, %s, %s)",
            (name, period, price, max_machines, analytics),
        )

    # Building subscriptions -> ids 1..3 (each building on a plan)
    for building_id, plan_id, start, end, status in [
        (1, 1, "2026-07-01", None, "active"),
        (2, 2, "2026-07-01", None, "active"),
        (3, 1, "2026-07-01", None, "active"),
    ]:
        db.execute(
            "INSERT INTO building_subscriptions "
            "(building_id, plan_id, start_date, end_date, subscription_status) "
            "VALUES (%s, %s, %s, %s, %s)",
            (building_id, plan_id, start, end, status),
        )

    # Bookings -> ids 1..5 (before-insert trigger checks same building,
    # machine 'active', valid status, and no overlap)
    for user_id, machine_id, start, end, price, status in [
        (1, 1, "2026-07-07 08:00:00", "2026-07-07 08:30:00", 2.50, "confirmed"),
        (2, 2, "2026-07-07 09:00:00", "2026-07-07 09:45:00", 2.00, "completed"),
        (4, 3, "2026-07-07 10:00:00", "2026-07-07 10:30:00", 3.00, "confirmed"),
        (6, 5, "2026-07-08 11:00:00", "2026-07-08 11:35:00", 2.25, "completed"),
        (2, 1, "2026-07-08 12:00:00", "2026-07-08 12:30:00", 2.50, "cancelled"),
    ]:
        db.execute(
            "INSERT INTO bookings "
            "(user_id, machine_id, start_time, end_time, price_at_booking, booking_status) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, machine_id, start, end, price, status),
        )

    # Booking payments -> split each into transaction_fee (app) + building_amount
    for booking_id, gross, status, pdate in [
        (1, 2.50, "paid", "2026-07-07 08:05:00"),
        (2, 2.00, "paid", "2026-07-07 09:05:00"),
        (3, 3.00, "paid", "2026-07-07 10:05:00"),
        (4, 2.25, "paid", "2026-07-08 11:05:00"),
        (5, 2.50, "refunded", "2026-07-08 12:05:00"),
    ]:
        fee = round(gross * FEE_RATE, 2)
        building_amount = round(gross - fee, 2)
        db.execute(
            "INSERT INTO booking_payments "
            "(booking_id, gross_amount, transaction_fee_rate, transaction_fee, "
            "building_amount, payment_status, payment_date) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (booking_id, gross, FEE_RATE, fee, building_amount, status, pdate),
        )

    # Subscription payments -> one for each active subscription
    for sub_id, amount, status, pdate, pstart, pend in [
        (1, 49.00, "paid", "2026-07-01 00:00:00", "2026-07-01", "2026-07-31"),
        (2, 99.00, "paid", "2026-07-01 00:00:00", "2026-07-01", "2026-07-31"),
        (3, 49.00, "paid", "2026-07-01 00:00:00", "2026-07-01", "2026-07-31"),
    ]:
        db.execute(
            "INSERT INTO subscription_payments "
            "(subscription_id, amount, payment_status, payment_date, "
            "billing_period_start, billing_period_end) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (sub_id, amount, status, pdate, pstart, pend),
        )


if __name__ == "__main__":
    reset()
    seed()
    print("Seeded: 3 buildings, 6 users, 6 machines, 3 plans, 3 subscriptions, "
          "5 bookings, 5 booking payments, 3 subscription payments.")
    print(f'All demo users log in with password: "{DEMO_PASSWORD}"')
