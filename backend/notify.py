"""User notifications: always stored in-app; email/SMS are best-effort extras.

Email and SMS only fire when their env vars are configured (see .env.example).
Without them, notify_user still records the in-app notification and just logs
that email/SMS were skipped, so the app works fully with zero external setup.
"""

import os
import smtplib
from email.mime.text import MIMEText

import db

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM") or SMTP_USER

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")


def _send_email(to_email, subject, body):
    if not (SMTP_HOST and SMTP_USER and SMTP_PASSWORD and to_email):
        print(f"[notify] email skipped (SMTP not configured): {subject!r} -> {to_email}")
        return
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM
        msg["To"] = to_email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as exc:  # noqa: BLE001 - notifications must never break the request
        print(f"[notify] email failed: {exc!r}")


def _send_sms(to_number, body):
    if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_FROM_NUMBER and to_number):
        print(f"[notify] sms skipped (Twilio not configured): {body!r} -> {to_number}")
        return
    try:
        from twilio.rest import Client

        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(to=to_number, from_=TWILIO_FROM_NUMBER, body=body)
    except Exception as exc:  # noqa: BLE001
        print(f"[notify] sms failed: {exc!r}")


def notify_user(user_id, category, message):
    """Record an in-app notification and best-effort email/SMS the user."""
    db.execute(
        "INSERT INTO notifications (user_id, category, message) VALUES (%s, %s, %s)",
        (user_id, category, message),
    )

    user = db.query(
        "SELECT email, phone_number, name FROM users WHERE user_id = %s",
        (user_id,),
        fetchone=True,
    )
    if not user:
        return

    _send_email(user.get("email"), f"WashWise: {category}", message)
    _send_sms(user.get("phone_number"), message)
