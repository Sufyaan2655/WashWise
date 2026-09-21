# WashWise — Backend (Flask + MySQL)

REST API for the WashWise laundry reservation system, written in Python with Flask.
It uses raw parameterized SQL through mysql-connector-python (no ORM).

The database has 8 tables normalized to at least 2NF and models two revenue streams:
booking transaction fees and building subscription fees.

## Files

- `app.py` — Flask application and all API routes
- `db.py` — MySQL connection helper (parameterized queries)
- `schema.sql` — creates the 8 tables
- `procedures.sql` — 2 stored procedures and 2 triggers
- `indexes_views.sql` — indexes and views
- `seed.py` — loads demo data
- `test_api.py` — automated tests (pytest)
- `requirements.txt` — Python dependencies
- `.env.example` — database credential template
- `requests.http` — sample requests for the REST Client extension
- `Dockerfile`, `docker-compose.yml` — containerized backend and MySQL

## Setup

    cd LaundryApp/backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env

Then set your MySQL password in the `.env` file.

## Database

    mysql -u root -p < schema.sql
    mysql -u root -p washwise < procedures.sql
    mysql -u root -p washwise < indexes_views.sql
    python seed.py

Ownership note: the database team owns the authoritative schema in
`/database/schema.sql`. The `schema.sql` here is a local copy so the backend
can run and be tested on its own. `procedures.sql` (stored procedures +
triggers) and `indexes_views.sql` (indexes + views) are part of the backend's
work — the API calls these procedures, so they must also be loaded into the
shared database for those endpoints to work.

## Run

    python app.py

The API runs at http://localhost:5001. Open `/health` to confirm the database
connection. (Port 5001 is used because macOS AirPlay occupies 5000.)

## Tests

    pytest -v

## Docker

    docker compose up --build
    docker compose exec backend python seed.py

## Endpoints

Health

- `GET /health`

Buildings

- `GET /buildings`
- `POST /buildings`

Users

- `GET /users`
- `POST /users`
- `POST /login`
- `GET /users/<id>/bookings`

Machines

- `GET /machines` (filters: `building_id`, `status`)
- `POST /machines`
- `PATCH /machines/<id>`

Subscription plans

- `GET /plans`
- `POST /plans`

Building subscriptions

- `GET /subscriptions`
- `POST /subscriptions`

Bookings

- `GET /bookings`
- `POST /bookings`
- `GET /bookings/<id>`
- `DELETE /bookings/<id>`

Payments

- `POST /booking-payments`
- `POST /subscription-payments`

Reports

- `GET /reports/revenue`
- `GET /reports/revenue/export`
