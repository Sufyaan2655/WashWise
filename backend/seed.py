"""Seed the database with realistic demo data.

Idempotent: wipes the tables and re-inserts a consistent demo dataset.
All demo users share the password "demo1234" (hashed with werkzeug).

The first 3 buildings / 6 users / 6 machines / 3 plans / 3 subscriptions / 5
bookings inserted below are the original fixture data the test suite's
hardcoded IDs depend on — their order and content must not change. Everything
after that block is additional demo/history data (more tenants, more
machines per building, ~45 days of realistic booking activity, notifications,
and a waitlist entry) purely for a fuller local demo; tests never reference it.
"""

import random
from datetime import date, datetime, timedelta

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

    counts = seed_demo_history()
    return counts


# ---------------------------------------------------------------------------
# Additional demo/history data: more tenants and machines per building, plus
# ~45 days of realistic booking activity so the revenue chart, dashboard, and
# notification/waitlist views all have something to show on first login.
# ---------------------------------------------------------------------------

EXTRA_TENANTS = {
    1: [  # Maple Court Apartments
        ("Sofia Martinez", "smartinez@example.com", "+15555550201"),
        ("David Kim", "dkim@example.com", "+15555550202"),
        ("Priya Patel", "ppatel@example.com", "+15555550203"),
        ("Marcus Johnson", "mjohnson@example.com", "+15555550204"),
        ("Elena Rossi", "erossi@example.com", "+15555550205"),
    ],
    2: [  # Riverside Towers
        ("Noah Bennett", "nbennett@example.com", "+15555550206"),
        ("Aisha Rahman", "arahman@example.com", "+15555550207"),
        ("Liam O'Connor", "loconnor@example.com", "+15555550208"),
        ("Grace Liu", "gliu@example.com", "+15555550209"),
        ("Tomas Fernandez", "tfernandez@example.com", "+15555550210"),
    ],
    3: [  # Sunset Gardens
        ("Emma Wilson", "ewilson@example.com", "+15555550211"),
        ("Carlos Mendez", "cmendez@example.com", "+15555550212"),
        ("Zainab Ali", "zali@example.com", "+15555550213"),
        ("Ryan Cooper", "rcooper@example.com", "+15555550214"),
        ("Nadia Petrova", "npetrova@example.com", "+15555550215"),
    ],
}

# (machine_number, type, cost_per_cycle, duration_minutes) per building,
# on top of the original washer #1 / dryer #2 fixture machines above.
EXTRA_MACHINES = {
    1: [
        (3, "washer", 2.50, 30), (4, "dryer", 2.00, 45),
        (5, "washer", 2.75, 32), (6, "dryer", 2.25, 40),
        (7, "washer", 2.50, 30), (8, "dryer", 2.00, 45),
    ],
    2: [
        (3, "washer", 3.00, 30), (4, "dryer", 2.75, 40),
        (5, "washer", 3.25, 35), (6, "dryer", 2.75, 40),
        (7, "washer", 3.00, 30), (8, "dryer", 3.00, 45),
    ],
    3: [
        (3, "washer", 2.25, 35), (4, "dryer", 2.25, 40),
        (5, "washer", 2.50, 30), (6, "dryer", 2.00, 45),
        (7, "washer", 2.25, 35), (8, "dryer", 2.25, 40),
    ],
}

BOOKING_HOURS = range(7, 21)  # 7 AM - 8 PM


def seed_demo_history(days_back=30, use_probability=0.4, rng_seed=42):
    """Populate more tenants, a full 8-machine laundry room per building,
    and realistic booking/payment/notification history for the last
    `days_back` days (ending today). Deterministic given `rng_seed`.

    Runs on a single shared connection (not db.execute()'s open-a-connection-
    per-call) since this can insert several hundred rows and re-seeding
    reopening a fresh MySQL connection per row would make the test suite,
    which re-seeds often, noticeably slow.
    """
    rng = random.Random(rng_seed)
    pw = generate_password_hash(DEMO_PASSWORD)
    conn = db.get_connection()

    def run(sql, params):
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.lastrowid

    try:
        tenant_ids_by_building = {1: [1, 2], 2: [5], 3: []}  # seed fixture tenants
        for building_id, tenants in EXTRA_TENANTS.items():
            for name, email, phone in tenants:
                user_id = run(
                    "INSERT INTO users (building_id, name, email, phone_number, password_hash, role) "
                    "VALUES (%s, %s, %s, %s, %s, 'tenant')",
                    (building_id, name, email, phone, pw),
                )
                tenant_ids_by_building[building_id].append(user_id)

        # machine_id -> (building_id, duration_minutes, cost_per_cycle)
        machine_info = {
            1: (1, 30, 2.50), 2: (1, 45, 2.00),
            3: (2, 30, 3.00), 4: (2, 40, 2.75),
            5: (3, 35, 2.25), 6: (3, 40, 2.25),
        }
        machine_ids_by_building = {1: [1, 2], 2: [3, 4], 3: [5, 6]}
        for building_id, machines in EXTRA_MACHINES.items():
            for num, mtype, cost, duration in machines:
                machine_id = run(
                    "INSERT INTO machines "
                    "(building_id, machine_number, machine_type, cost_per_cycle, "
                    "duration_minutes, status) VALUES (%s, %s, %s, %s, %s, 'active')",
                    (building_id, num, mtype, cost, duration),
                )
                machine_info[machine_id] = (building_id, duration, cost)
                machine_ids_by_building[building_id].append(machine_id)

        booking_count = 0
        payment_count = 0
        today = date.today()

        for offset in range(days_back, 0, -1):
            day = today - timedelta(days=offset)
            for building_id, machine_ids in machine_ids_by_building.items():
                tenants = tenant_ids_by_building[building_id]
                for machine_id in machine_ids:
                    if rng.random() > use_probability:  # not every machine is used every day
                        continue
                    _, duration, cost = machine_info[machine_id]
                    hour = rng.choice(list(BOOKING_HOURS))
                    start = datetime.combine(day, datetime.min.time()) + timedelta(hours=hour)
                    end = start + timedelta(minutes=duration)
                    tenant_id = rng.choice(tenants)
                    status = "cancelled" if rng.random() < 0.08 else "completed"

                    booking_id = run(
                        "INSERT INTO bookings "
                        "(user_id, machine_id, start_time, end_time, price_at_booking, booking_status) "
                        "VALUES (%s, %s, %s, %s, %s, %s)",
                        (tenant_id, machine_id, start, end, cost, status),
                    )
                    booking_count += 1

                    if status == "completed":
                        fee = round(cost * FEE_RATE, 2)
                        building_amount = round(cost - fee, 2)
                        payment_status = "refunded" if rng.random() < 0.04 else "paid"
                        payment_time = start + timedelta(minutes=duration + 5)
                        run(
                            "INSERT INTO booking_payments "
                            "(booking_id, gross_amount, transaction_fee_rate, transaction_fee, "
                            "building_amount, payment_status, payment_date) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (booking_id, cost, FEE_RATE, fee, building_amount,
                             payment_status, payment_time),
                        )
                        payment_count += 1

        # A couple of upcoming reservations so "My laundry" isn't empty on first login.
        upcoming = [
            (5, 3, 1),   # wchen (demo tenant), a Riverside washer, tomorrow
            (1, 1, 2),   # adiallo (demo tenant), a Maple Court washer, in 2 days
        ]
        for tenant_id, machine_id, days_ahead in upcoming:
            _, duration, cost = machine_info[machine_id]
            start = datetime.combine(today + timedelta(days=days_ahead), datetime.min.time()) + timedelta(hours=17)
            end = start + timedelta(minutes=duration)
            booking_id = run(
                "INSERT INTO bookings "
                "(user_id, machine_id, start_time, end_time, price_at_booking, booking_status) "
                "VALUES (%s, %s, %s, %s, %s, 'confirmed')",
                (tenant_id, machine_id, start, end, cost),
            )
            fee = round(cost * FEE_RATE, 2)
            run(
                "INSERT INTO booking_payments "
                "(booking_id, gross_amount, transaction_fee_rate, transaction_fee, "
                "building_amount, payment_status, payment_date) "
                "VALUES (%s, %s, %s, %s, %s, 'paid', NOW())",
                (booking_id, cost, FEE_RATE, fee, round(cost - fee, 2)),
            )
            booking_count += 1
            payment_count += 1
            run(
                "INSERT INTO notifications (user_id, category, message) VALUES (%s, %s, %s)",
                (tenant_id, "booking_confirmed",
                 f"Your booking is confirmed for {start.strftime('%Y-%m-%d %H:%M')}."),
            )

        # A second month of subscription revenue so the "Current plan" panel
        # reads as an established, paying account rather than a brand-new one.
        for sub_id, amount in [(1, 49.00), (2, 99.00), (3, 49.00)]:
            last_month = today.replace(day=1) - timedelta(days=1)
            period_start = last_month.replace(day=1)
            run(
                "INSERT INTO subscription_payments "
                "(subscription_id, amount, payment_status, payment_date, "
                "billing_period_start, billing_period_end) "
                "VALUES (%s, %s, 'paid', %s, %s, %s)",
                (sub_id, amount, period_start, period_start, last_month),
            )

        # Put one machine per building into maintenance, and waitlist a tenant on it
        # so the notification bell and waitlist UI have something to show.
        for building_id, machine_ids in machine_ids_by_building.items():
            maintenance_machine_id = machine_ids[-1]
            run("UPDATE machines SET status = 'maintenance' WHERE machine_id = %s",
                (maintenance_machine_id,))
            waiting_tenant = tenant_ids_by_building[building_id][0]
            run(
                "INSERT INTO waitlist (machine_id, user_id, status) VALUES (%s, %s, 'waiting')",
                (maintenance_machine_id, waiting_tenant),
            )
            run(
                "INSERT INTO notifications (user_id, category, message) VALUES (%s, %s, %s)",
                (waiting_tenant, "waitlist_joined",
                 "You're on the waitlist — we'll notify you when that machine is free."),
            )

        conn.commit()
    finally:
        conn.close()

    return {
        "extra_tenants": sum(len(v) for v in EXTRA_TENANTS.values()),
        "extra_machines": sum(len(v) for v in EXTRA_MACHINES.values()),
        "history_bookings": booking_count,
        "history_payments": payment_count,
    }


if __name__ == "__main__":
    reset()
    counts = seed()
    print("Seeded: 3 buildings, "
          f"{6 + counts['extra_tenants']} users, "
          f"{6 + counts['extra_machines']} machines, 3 plans, 3 subscriptions, "
          f"{5 + counts['history_bookings']} bookings, "
          f"{5 + counts['history_payments']} booking payments, "
          "6 subscription payments.")
    print(f'All demo users log in with password: "{DEMO_PASSWORD}"')
