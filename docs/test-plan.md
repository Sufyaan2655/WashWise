# LaundryApp Test Plan

## Overview
This document describes the testing approach for the LaundryApp backend, covering API behavior, database integrity, and known issues found and fixed during testing.

## Testing Approach
Testing is split into two layers:

1. **API-level tests** (`backend/test_api.py`) — use Flask's test client to exercise every route exactly as a real client would, without needing a running frontend.
2. **Database-level tests** (`backend/test_db.py`) — connect directly to MySQL to verify that constraints (foreign keys, unique keys) and views hold up even if the API layer were bypassed or had a bug.

Both suites re-seed the database before running (`seed.reset()` + `seed.seed()`), so tests always run against known, consistent data.

## How to Run
```bash
cd backend
source venv/bin/activate
docker compose up -d
pytest test_api.py test_db.py -v
```

## Coverage

### Authentication & Users
- Signup, login, wrong password rejected
- Duplicate email rejected (enforced at both API and database level via `UNIQUE` constraint)
- Passwords never exposed in API responses

### Buildings, Machines, Plans
- Listing buildings, machines, plans, subscriptions
- Invalid machine status values rejected

### Bookings
- Creating a booking flips the machine to `in_use` (via `trg_booking_after_insert`)
- Cancelling a booking frees the machine (via `trg_booking_after_update`)
- Cancelling a non-existent booking returns 404
- Booking with a missing required field returns 400
- Foreign key constraints reject bookings referencing non-existent users/machines

### Payments & Revenue
- Booking payments correctly split gross amount into transaction fee + building amount
- Negative payment amounts are rejected
- Revenue report includes both booking and subscription revenue streams
- Excel export returns a valid spreadsheet

### Database Integrity
- Foreign keys block orphaned records (invalid user_id/machine_id on bookings)
- Deleting a building with dependent machines is blocked, not silently cascaded
- `v_active_subscriptions` view only returns subscriptions with `subscription_status = 'active'`

## Bugs Found and Fixed
1. **Negative payment amounts accepted** — `POST /booking-payments` did not validate that `gross_amount` was positive. Fixed by rejecting `gross_amount <= 0` with a 400 error.
2. **Double-booking allowed** — `POST /bookings` (via `sp_book_machine`) did not check for overlapping time slots on the same machine, allowing two users to book the same washer at the same time. Fixed by adding a conflict check before calling the stored procedure.
3. **Schema drift between `backend/schema.sql` and `database/schema.sql`** — the backend's local dev schema had diverged from the team's authoritative schema in three columns (`users.email` length, `machines.status` length, `booking_payments.transaction_fee_rate` precision). Fixed by aligning `backend/schema.sql` to match.

## Test Results
As of the latest run: **22/22 tests passing** (17 API tests, 5 database tests).
