"""MySQL connection helper. Parameterized queries only; credentials loaded from .env."""

import os

import mysql.connector
from dotenv import load_dotenv

load_dotenv(override=True)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "washwise"),
}


def get_connection():
    """Open a new MySQL connection using the .env configuration."""
    return mysql.connector.connect(**DB_CONFIG)


def query(sql, params=None, *, fetchone=False):
    """Run a SELECT and return rows as dicts (or one row if fetchone)."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params or ())
        return cursor.fetchone() if fetchone else cursor.fetchall()
    finally:
        conn.close()


def execute(sql, params=None):
    """Run an INSERT/UPDATE/DELETE, commit, and return lastrowid + rowcount."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params or ())
        conn.commit()
        return {"lastrowid": cursor.lastrowid, "rowcount": cursor.rowcount}
    finally:
        conn.close()


def call_procedure(name, args=None):
    """Call a stored procedure and return its result rows as dicts."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.callproc(name, args or ())
        rows = []
        for result in cursor.stored_results():
            rows.extend(result.fetchall())
        conn.commit()
        return rows
    finally:
        conn.close()
