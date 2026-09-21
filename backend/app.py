"""WashWise / LaundryApp — Flask REST API.

Raw SQL only (mysql-connector-python), no ORM.
All queries are parameterized to prevent SQL injection.
"""

import os
from io import BytesIO
from datetime import date

from flask import Flask, g, jsonify, request, send_file
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash
from mysql.connector import Error as MySQLError

import db
import notify
from auth import (
    generate_token,
    require_self_or_manager,
    role_required,
    token_required,
)

app = Flask(__name__)

# "*" (default) allows any origin, which is fine for local dev / a demo.
# Set ALLOWED_ORIGINS to a comma-separated list of real frontend origins in production.
CORS(app, origins=os.getenv("ALLOWED_ORIGINS", "*").split(","))

DEFAULT_FEE_RATE = 0.15  # app keeps 15% of a booking as its transaction fee


@app.get("/")
def index():
    """API root — basic service info."""
    return jsonify(service="WashWise API", status="running", health="/health")


class ApiError(Exception):
    """Raised for client errors; converted to a JSON response."""

    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


@app.errorhandler(ApiError)
def _handle_api_error(exc):
    return jsonify(error=exc.message), exc.status


@app.errorhandler(MySQLError)
def _handle_db_error(exc):
    if getattr(exc, "errno", None) == 1062:
        return jsonify(error="that value already exists (duplicate)"), 409
    if getattr(exc, "errno", None) == 1452:
        return jsonify(error="referenced record does not exist"), 400
    if getattr(exc, "errno", None) == 1644:
        return jsonify(error=getattr(exc, "msg", str(exc))), 400
    return jsonify(error="database error", detail=str(exc)), 400


def get_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError(400, "request body must be a JSON object")
    return data


def require(data, *fields):
    missing = [f for f in fields if data.get(f) in (None, "")]
    if missing:
        raise ApiError(400, "missing required field(s): " + ", ".join(missing))


def serialize_booking(row):
    row = dict(row)
    if row.get("start_time") is not None:
        row["start_time"] = row["start_time"].strftime("%Y-%m-%d %H:%M:%S")
    if row.get("end_time") is not None:
        row["end_time"] = row["end_time"].strftime("%Y-%m-%d %H:%M:%S")
    return row


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    try:
        db.query("SELECT 1 AS ok", fetchone=True)
        return jsonify(status="ok", database="connected")
    except Exception as exc:  # noqa: BLE001
        return jsonify(status="error", detail=str(exc)), 500


# ---------------------------------------------------------------------------
# Buildings
# ---------------------------------------------------------------------------
@app.get("/buildings")
def list_buildings():
    return jsonify(db.query("SELECT * FROM buildings ORDER BY building_id"))


@app.post("/buildings")
def create_building():
    data = get_body()
    require(data, "name", "address")
    result = db.execute(
        "INSERT INTO buildings (name, address) VALUES (%s, %s)",
        (data["name"], data["address"]),
    )
    return jsonify(building_id=result["lastrowid"]), 201


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
@app.get("/users")
def list_users():
    return jsonify(
        db.query(
            "SELECT user_id, building_id, name, email, role, created_at "
            "FROM users ORDER BY user_id"
        )
    )


@app.post("/users")
def create_user():
    data = get_body()
    require(data, "building_id", "name", "email", "password", "role")
    password_hash = generate_password_hash(data["password"])
    result = db.execute(
        "INSERT INTO users (building_id, name, email, phone_number, password_hash, role) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (data["building_id"], data["name"], data["email"], data.get("phone_number"),
         password_hash, data["role"]),
    )
    return jsonify(user_id=result["lastrowid"]), 201


@app.post("/login")
def login():
    data = get_body()
    require(data, "email", "password")
    user = db.query(
        "SELECT user_id, building_id, name, email, role, password_hash FROM users WHERE email = %s",
        (data["email"],),
        fetchone=True,
    )
    if not user or not check_password_hash(user["password_hash"], data["password"]):
        return jsonify(error="invalid email or password"), 401
    return jsonify(
        user_id=user["user_id"], building_id=user["building_id"],
        name=user["name"], email=user["email"], role=user["role"],
        token=generate_token(user),
    )


@app.get("/me")
@token_required
def me():
    user = db.query(
        "SELECT user_id, building_id, name, email, role FROM users WHERE user_id = %s",
        (g.current_user["user_id"],),
        fetchone=True,
    )
    if not user:
        return jsonify(error="user not found"), 404
    return jsonify(user)


@app.get("/users/<int:user_id>/bookings")
@token_required
def user_bookings(user_id):
    denied = require_self_or_manager(user_id)
    if denied:
        return denied
    rows = db.query(
        "SELECT b.booking_id, m.machine_id, m.machine_number, m.machine_type, "
        "b.start_time, b.end_time, b.price_at_booking, b.booking_status "
        "FROM bookings b "
        "JOIN machines m ON b.machine_id = m.machine_id "
        "WHERE b.user_id = %s "
        "ORDER BY b.start_time DESC",
        (user_id,),
    )
    return jsonify([serialize_booking(r) for r in rows])

# ---------------------------------------------------------------------------
# Machines
# ---------------------------------------------------------------------------
@app.get("/machines")
def list_machines():
    clauses = []
    params = []
    building_id = request.args.get("building_id")
    status = request.args.get("status")
    if building_id:
        clauses.append("building_id = %s")
        params.append(building_id)
    if status:
        clauses.append("status = %s")
        params.append(status)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return jsonify(
        db.query(f"SELECT * FROM machines {where} ORDER BY machine_id", params)
    )


@app.post("/machines")
def create_machine():
    data = get_body()
    require(data, "building_id", "machine_number", "machine_type",
            "cost_per_cycle", "duration_minutes")
    result = db.execute(
        "INSERT INTO machines "
        "(building_id, machine_number, machine_type, cost_per_cycle, "
        "duration_minutes, status) VALUES (%s, %s, %s, %s, %s, %s)",
        (
            data["building_id"], data["machine_number"], data["machine_type"],
            data["cost_per_cycle"], data["duration_minutes"],
            data.get("status", "active"),
        ),
    )
    return jsonify(machine_id=result["lastrowid"]), 201


@app.patch("/machines/<int:machine_id>")
@token_required
@role_required("manager")
def update_machine_status(machine_id):
    data = get_body()
    require(data, "status")
    allowed = {"active", "maintenance"}
    if data["status"] not in allowed:
        raise ApiError(400, "status must be one of: " + ", ".join(sorted(allowed)))
    result = db.execute(
        "UPDATE machines SET status = %s WHERE machine_id = %s",
        (data["status"], machine_id),
    )
    if result["rowcount"] == 0:
        exists = db.query("SELECT 1 FROM machines WHERE machine_id = %s",
                          (machine_id,), fetchone=True)
        if not exists:
            return jsonify(error="machine not found"), 404
    return jsonify(machine_id=machine_id, status=data["status"])


# ---------------------------------------------------------------------------
# Subscription plans
# ---------------------------------------------------------------------------
@app.get("/plans")
def list_plans():
    return jsonify(db.query("SELECT * FROM subscription_plans ORDER BY plan_id"))


@app.post("/plans")
def create_plan():
    data = get_body()
    require(data, "plan_name", "billing_period", "subscription_price",
            "max_machines", "analytics_level")
    result = db.execute(
        "INSERT INTO subscription_plans "
        "(plan_name, billing_period, subscription_price, max_machines, analytics_level) "
        "VALUES (%s, %s, %s, %s, %s)",
        (
            data["plan_name"], data["billing_period"], data["subscription_price"],
            data["max_machines"], data["analytics_level"],
        ),
    )
    return jsonify(plan_id=result["lastrowid"]), 201


# ---------------------------------------------------------------------------
# Building subscriptions
# ---------------------------------------------------------------------------
@app.get("/subscriptions")
def list_subscriptions():
    return jsonify(
        db.query(
            "SELECT bs.subscription_id, bs.building_id, bl.name AS building, "
            "p.plan_name, p.billing_period, p.subscription_price, "
            "p.analytics_level, bs.start_date, bs.end_date, "
            "bs.subscription_status "
            "FROM building_subscriptions bs "
            "JOIN buildings bl ON bs.building_id = bl.building_id "
            "JOIN subscription_plans p ON bs.plan_id = p.plan_id "
            "ORDER BY bs.subscription_id"
        )
    )


@app.post("/subscriptions")
@token_required
@role_required("manager")
def create_subscription():
    data = get_body()
    require(data, "building_id", "plan_id", "start_date")
    result = db.execute(
        "INSERT INTO building_subscriptions "
        "(building_id, plan_id, start_date, end_date, subscription_status) "
        "VALUES (%s, %s, %s, %s, %s)",
        (
            data["building_id"], data["plan_id"], data["start_date"],
            data.get("end_date"), data.get("subscription_status", "active"),
        ),
    )
    return jsonify(subscription_id=result["lastrowid"]), 201


# ---------------------------------------------------------------------------
# Bookings (junction table)
# ---------------------------------------------------------------------------
@app.get("/bookings")
def list_bookings():
    rows = db.query(
        "SELECT b.booking_id, u.name AS tenant, m.machine_type, "
        "b.start_time, b.end_time, b.price_at_booking, b.booking_status "
        "FROM bookings b "
        "JOIN users u ON b.user_id = u.user_id "
        "JOIN machines m ON b.machine_id = m.machine_id "
        "ORDER BY b.booking_id"
    )
    return jsonify([serialize_booking(r) for r in rows])


@app.post("/bookings")
@token_required
def create_booking():
    """Create a booking using the sp_book_machine stored procedure.

    A BEFORE INSERT trigger validates the booking: the user and machine
    must belong to the same building, the machine must be operational,
    and the reservation must not overlap an existing booking.
    """
    data = get_body()

    require(
        data,
        "user_id",
        "machine_id",
        "start_time",
        "end_time",
        "price_at_booking",
    )

    denied = require_self_or_manager(data["user_id"])
    if denied:
        return denied

    conflict = db.query(
        "SELECT booking_id FROM bookings "
        "WHERE machine_id = %s "
        "AND booking_status = 'confirmed' "
        "AND start_time < %s "
        "AND end_time > %s",
        (
            data["machine_id"],
            data["end_time"],
            data["start_time"],
        ),
        fetchone=True,
    )

    if conflict:
        raise ApiError(
            409,
            "machine already booked for that time",
        )

    try:
        rows = db.call_procedure(
            "sp_book_machine",
            (
                data["user_id"],
                data["machine_id"],
                data["start_time"],
                data["end_time"],
                data["price_at_booking"],
            ),
        )

        booking_id = rows[0]["booking_id"] if rows else None

        if booking_id:
            notify.notify_user(
                data["user_id"], "booking_confirmed",
                f"Your booking (#{booking_id}) is confirmed for {data['start_time']}.",
            )

        return jsonify(booking_id=booking_id), 201

    except Exception as error:
        print("BOOKING ERROR:", repr(error))
        return jsonify(error=str(error)), 400


@app.delete("/bookings/<int:booking_id>")
@token_required
def cancel_booking(booking_id):
    booking = db.query(
        "SELECT user_id, machine_id FROM bookings WHERE booking_id = %s",
        (booking_id,),
        fetchone=True,
    )

    if not booking:
        return jsonify(error="booking not found"), 404

    denied = require_self_or_manager(booking["user_id"])
    if denied:
        return denied

    db.execute(
        "UPDATE bookings SET booking_status = 'cancelled' WHERE booking_id = %s",
        (booking_id,),
    )

    db.execute(
        "UPDATE machines SET status = 'active' WHERE machine_id = %s",
        (booking["machine_id"],),
    )

    notify.notify_user(
        booking["user_id"], "booking_cancelled",
        f"Your booking (#{booking_id}) has been cancelled.",
    )
    _notify_next_waitlisted(booking["machine_id"])

    return jsonify(
        booking_id=booking_id,
        booking_status="cancelled",
        machine_status="active",
    )

@app.get("/bookings/<int:booking_id>")
def get_booking(booking_id):
    row = db.query(
        "SELECT b.booking_id, u.name AS tenant, u.email AS tenant_email, "
        "bl.name AS building, m.machine_id, m.machine_number, m.machine_type, "
        "b.start_time, b.end_time, b.price_at_booking, b.booking_status "
        "FROM bookings b "
        "JOIN users u ON b.user_id = u.user_id "
        "JOIN machines m ON b.machine_id = m.machine_id "
        "JOIN buildings bl ON m.building_id = bl.building_id "
        "WHERE b.booking_id = %s",
        (booking_id,),
        fetchone=True,
    )
    if not row:
        return jsonify(error="booking not found"), 404
    return jsonify(serialize_booking(row))


# ---------------------------------------------------------------------------
# Waitlist (tenants waiting on a machine that is currently unavailable)
# ---------------------------------------------------------------------------
def _notify_next_waitlisted(machine_id):
    """After a machine frees up, notify the longest-waiting person for it."""
    entry = db.query(
        "SELECT waitlist_id, user_id FROM waitlist "
        "WHERE machine_id = %s AND status = 'waiting' "
        "ORDER BY created_at ASC LIMIT 1",
        (machine_id,),
        fetchone=True,
    )
    if not entry:
        return
    db.execute(
        "UPDATE waitlist SET status = 'notified' WHERE waitlist_id = %s",
        (entry["waitlist_id"],),
    )
    notify.notify_user(
        entry["user_id"], "waitlist_available",
        "A machine you were waiting for is now free — grab it before someone else does.",
    )


@app.post("/machines/<int:machine_id>/waitlist")
@token_required
def join_waitlist(machine_id):
    data = get_body()
    require(data, "user_id")
    denied = require_self_or_manager(data["user_id"])
    if denied:
        return denied
    result = db.execute(
        "INSERT INTO waitlist (machine_id, user_id, status) VALUES (%s, %s, 'waiting')",
        (machine_id, data["user_id"]),
    )
    return jsonify(waitlist_id=result["lastrowid"]), 201


@app.get("/users/<int:user_id>/waitlist")
@token_required
def list_waitlist(user_id):
    denied = require_self_or_manager(user_id)
    if denied:
        return denied
    rows = db.query(
        "SELECT w.waitlist_id, w.machine_id, m.machine_number, m.machine_type, "
        "w.status, w.created_at "
        "FROM waitlist w JOIN machines m ON w.machine_id = m.machine_id "
        "WHERE w.user_id = %s ORDER BY w.created_at DESC",
        (user_id,),
    )
    return jsonify(rows)


@app.delete("/waitlist/<int:waitlist_id>")
@token_required
def leave_waitlist(waitlist_id):
    entry = db.query(
        "SELECT user_id FROM waitlist WHERE waitlist_id = %s",
        (waitlist_id,), fetchone=True,
    )
    if not entry:
        return jsonify(error="waitlist entry not found"), 404
    denied = require_self_or_manager(entry["user_id"])
    if denied:
        return denied
    db.execute("DELETE FROM waitlist WHERE waitlist_id = %s", (waitlist_id,))
    return jsonify(waitlist_id=waitlist_id, removed=True)


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------
@app.get("/users/<int:user_id>/notifications")
@token_required
def list_notifications(user_id):
    denied = require_self_or_manager(user_id)
    if denied:
        return denied
    rows = db.query(
        "SELECT notification_id, category, message, is_read, created_at "
        "FROM notifications WHERE user_id = %s ORDER BY created_at DESC LIMIT 50",
        (user_id,),
    )
    return jsonify(rows)


@app.post("/notifications/<int:notification_id>/read")
@token_required
def mark_notification_read(notification_id):
    notification = db.query(
        "SELECT user_id FROM notifications WHERE notification_id = %s",
        (notification_id,), fetchone=True,
    )
    if not notification:
        return jsonify(error="notification not found"), 404
    denied = require_self_or_manager(notification["user_id"])
    if denied:
        return denied
    db.execute(
        "UPDATE notifications SET is_read = 1 WHERE notification_id = %s",
        (notification_id,),
    )
    return jsonify(notification_id=notification_id, is_read=True)


# ---------------------------------------------------------------------------
# Booking payments (tenant pays; app keeps a transaction fee)
# ---------------------------------------------------------------------------
@app.post("/booking-payments")
def create_booking_payment():
    data = get_body()
    require(data, "booking_id", "gross_amount")
    gross = float(data["gross_amount"])
    if gross <= 0:
        raise ApiError(400, "gross_amount must be positive")
    rate = float(data.get("transaction_fee_rate", DEFAULT_FEE_RATE))
    fee = round(gross * rate, 2)
    building_amount = round(gross - fee, 2)
    result = db.execute(
        "INSERT INTO booking_payments "
        "(booking_id, gross_amount, transaction_fee_rate, transaction_fee, "
        "building_amount, payment_status, payment_date) "
        "VALUES (%s, %s, %s, %s, %s, %s, NOW())",
        (data["booking_id"], gross, rate, fee, building_amount,
         data.get("payment_status", "paid")),
    )
    return jsonify(payment_id=result["lastrowid"], transaction_fee=fee,
                   building_amount=building_amount), 201


# ---------------------------------------------------------------------------
# Subscription payments (building pays the app its SaaS fee)
# ---------------------------------------------------------------------------
@app.post("/subscription-payments")
def create_subscription_payment():
    data = get_body()
    require(
        data,
        "subscription_id",
        "amount",
        "billing_period_start",
        "billing_period_end",
    )

    try:
        amount = float(data["amount"])
    except (TypeError, ValueError):
        raise ApiError(400, "amount must be a number")

    if amount <= 0:
        raise ApiError(400, "amount must be positive")

    payment_status = str(
        data.get("payment_status", "paid")
    ).strip().lower()

    allowed_statuses = {"paid", "pending", "refunded"}

    if payment_status not in allowed_statuses:
        raise ApiError(
            400,
            "payment_status must be one of: paid, pending, refunded",
        )

    try:
        billing_period_start = date.fromisoformat(
            str(data["billing_period_start"])
        )
        billing_period_end = date.fromisoformat(
            str(data["billing_period_end"])
        )
    except ValueError:
        raise ApiError(
            400,
            "billing period dates must use YYYY-MM-DD",
        )

    if billing_period_end < billing_period_start:
        raise ApiError(
            400,
            "billing_period_end must be on or after "
            "billing_period_start",
        )

    result = db.execute(
        "INSERT INTO subscription_payments "
        "(subscription_id, amount, payment_status, payment_date, "
        "billing_period_start, billing_period_end) "
        "VALUES (%s, %s, %s, NOW(), %s, %s)",
        (
            data["subscription_id"],
            amount,
            payment_status,
            billing_period_start.isoformat(),
            billing_period_end.isoformat(),
        ),
    )

    return jsonify(
        subscription_payment_id=result["lastrowid"]
    ), 201

# ---------------------------------------------------------------------------
# Revenue report + Excel export (both streams)
# ---------------------------------------------------------------------------
@app.get("/reports/revenue")
@token_required
@role_required("manager")
def revenue_report():
    return jsonify(db.call_procedure("sp_revenue_report"))


@app.get("/reports/revenue/timeseries")
@token_required
@role_required("manager")
def revenue_timeseries():
    """Daily booking-fee + subscription revenue for the manager's building."""
    building_id = request.args.get("building_id", g.current_user["building_id"])
    days = min(int(request.args.get("days", 30)), 365)

    rows = db.query(
        "SELECT DATE(bp.payment_date) AS day, SUM(bp.transaction_fee) AS booking_revenue "
        "FROM booking_payments bp "
        "JOIN bookings b ON bp.booking_id = b.booking_id "
        "JOIN machines m ON b.machine_id = m.machine_id "
        "WHERE m.building_id = %s AND bp.payment_status = 'paid' "
        "AND bp.payment_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY) "
        "GROUP BY DATE(bp.payment_date) ORDER BY day",
        (building_id, days),
    )
    sub_rows = db.query(
        "SELECT DATE(sp.payment_date) AS day, SUM(sp.amount) AS subscription_revenue "
        "FROM subscription_payments sp "
        "JOIN building_subscriptions bs ON sp.subscription_id = bs.subscription_id "
        "WHERE bs.building_id = %s AND sp.payment_status = 'paid' "
        "AND sp.payment_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY) "
        "GROUP BY DATE(sp.payment_date) ORDER BY day",
        (building_id, days),
    )

    by_day = {}
    for r in rows:
        day = r["day"].isoformat()
        by_day[day] = {"day": day, "booking_revenue": float(r["booking_revenue"] or 0),
                       "subscription_revenue": 0.0}
    for r in sub_rows:
        day = r["day"].isoformat()
        by_day.setdefault(day, {"day": day, "booking_revenue": 0.0, "subscription_revenue": 0.0})
        by_day[day]["subscription_revenue"] = float(r["subscription_revenue"] or 0)

    return jsonify(sorted(by_day.values(), key=lambda row: row["day"]))


@app.get("/reports/revenue/export")
@token_required
@role_required("manager")
def revenue_export():
    """One-click Excel export of the revenue report (both streams)."""
    from openpyxl import Workbook

    rows = db.call_procedure("sp_revenue_report")

    wb = Workbook()
    ws = wb.active
    ws.title = "Revenue"
    ws.append(["Building", "Booking Fees", "Subscription Revenue", "Total"])
    for r in rows:
        booking = float(r["booking_revenue"])
        subscription = float(r["subscription_revenue"])
        ws.append([r["building"], booking, subscription, booking + subscription])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name="revenue_report.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


if __name__ == "__main__":
    # Port 5001 (macOS AirPlay Receiver occupies 5000).
    app.run(debug=True, port=5001)
