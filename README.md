# LaundryApp

[![Backend tests](https://github.com/Sufyaan2655/WashWise/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/Sufyaan2655/WashWise/actions/workflows/backend-tests.yml)

CSC336 Group Project

# Team Members

1. Alhassana Diallo
2. Benny
3. Sufyaan
4. Pedro
5. Yeasin Riyad
6. Sangita Shrestha
7. Jancarlos Jaquez


# Project Description

A SaaS platform that allows apartment tenants to reserve and pay for laundry machines while providing building managers with real-time machine availability and revenue tracking.

# Repository Structure

1. backend/ → Backend application code
2. frontend/ → User interface code
3. database/ → Database schema, SQL scripts, and ER diagrams
4. docs/ → Project documentation and reports

# WashWise Laundry Reservation System

WashWise is a full-stack laundry reservation application for apartment buildings.

Tenants can log in, view available washers and dryers, reserve a machine, view their bookings, and cancel reservations.

Building managers can log in to a manager dashboard to monitor machines, view live revenue information, and see the building subscription plan.

## Demo

<video src="https://github.com/Sufyaan2655/WashWise/raw/main/docs/washwise-demo.mp4" controls width="720">
  Your browser can't play this video inline —
  <a href="docs/washwise-demo.mp4">open it directly</a>.
</video>

A captioned walkthrough recorded against the running app: a resident reserving a
machine and getting an instant notification, then a property manager's revenue
dashboard. If the video above doesn't play inline, [open it directly](docs/washwise-demo.mp4).

## Team Project

Course: CSC336 – Introduction to Database Systems

Project type: Full-stack relational database application

## Technology Stack

### Frontend

- SvelteKit
- HTML
- CSS
- JavaScript

### Backend

- Python
- Flask
- mysql-connector-python

### Database

- MySQL
- Stored procedures
- Triggers
- Views
- Indexes

## Main Features

- JWT-authenticated login for tenants and managers, with role- and ownership-based
  access control on every protected route
- Role-based tenant and manager dashboards
- Live washer and dryer availability
- Machine duration and price information
- Tenant machine reservations
- Tenant booking history
- Booking cancellation
- Waitlist for a busy machine, with automatic notification when it frees up
- In-app, email, and SMS notifications (email/SMS are optional — see Local Setup)
- Stored procedure for booking creation
- Booking overlap prevention
- Trigger-based machine status updates
- Manager machine inventory
- Live booking-fee revenue from MySQL
- Live subscription revenue from MySQL
- Daily revenue trend chart (booking fees + subscription revenue)
- Live building subscription plan information
- Transaction-fee revenue model
- Building SaaS subscription model
- CI: the backend test suite runs on every push via GitHub Actions

## Revenue Model

WashWise uses two revenue streams:

1. A transaction fee from every laundry booking
2. A recurring SaaS subscription paid by each apartment building

Example for a $3.00 laundry cycle:

- Building share: $2.55
- Application developer fee: $0.45
- Transaction fee rate: 15%

The database stores the revenue split in the `booking_payments` table.

Building subscriptions are stored using:

- `subscription_plans`
- `building_subscriptions`
- `subscription_payments`

## Database Tables

The final database contains these main tables:

1. `buildings`
2. `users`
3. `machines`
4. `bookings`
5. `booking_payments`
6. `subscription_plans`
7. `building_subscriptions`
8. `subscription_payments`
9. `notifications`
10. `waitlist`

The data model is normalized to at least Second Normal Form.

## Demo Login Accounts

### Manager Account

Email:

```text
jcarter@example.com
```

Password:

```text
password123
```

### Tenant Account

Email:

```text
wchen@example.com
```

Password:

```text
password123
```

## Repository Structure

```text
LaundryApp/
├── .github/workflows/
│   └── backend-tests.yml
├── backend/
│   ├── app.py
│   ├── auth.py
│   ├── notify.py
│   ├── db.py
│   ├── schema.sql
│   ├── procedures.sql
│   ├── indexes_views.sql
│   ├── seed.py
│   ├── test_api.py
│   ├── test_db.py
│   ├── test_auth.py
│   ├── requirements.txt
│   └── .env.example
├── database/
├── docs/
├── frontend/
│   ├── src/
│   │   ├── app.css
│   │   ├── lib/
│   │   │   ├── api.js
│   │   │   ├── config.js
│   │   │   ├── stores/         # auth, machines, bookings, waitlist, notifications, notice
│   │   │   └── components/     # Header, AuthModal, MachineCard, RevenueChart, ...
│   │   └── routes/
│   │       ├── +layout.svelte
│   │       ├── +page.svelte        # landing
│   │       ├── machines/+page.svelte
│   │       ├── bookings/+page.svelte
│   │       ├── pricing/+page.svelte
│   │       └── dashboard/+page.svelte
│   ├── package.json
│   └── vite.config.js
├── compose.yaml
├── Midpitch.pdf
└── README.md
```

## Local Setup

GitHub contains the source code, but the application must be run locally unless the frontend, backend, and database are deployed online.

The application requires:

- MySQL
- Python 3
- Node.js
- npm

## Step 1: Create the MySQL Database

Open MySQL Workbench.

The database name is:

```sql
washwise
```

Run the SQL files in this order:

```text
1. backend/schema.sql
2. backend/procedures.sql
3. backend/indexes_views.sql
```

All three SQL files are required. The automated tests depend on the
stored procedures, triggers, indexes, and views created by these files.


## Step 2: Configure the Backend

Open a terminal in the project folder:

```bash
cd ~/Desktop/LaundryApp-main/backend
```

Create and activate the Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the Python requirements:

```bash
pip install -r requirements.txt
```

Create the local environment file:

```bash
cp .env.example .env
```

Update `backend/.env` with the local MySQL credentials.

Example:

```text
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=washwise
SECRET_KEY=change_this_to_a_random_secret
ALLOWED_ORIGINS=*
```

`SECRET_KEY` signs login tokens — use any random string locally. `ALLOWED_ORIGINS`
controls CORS; `*` is fine for local dev and a demo.

Email and SMS notifications are optional. Leaving `SMTP_*` and `TWILIO_*` blank in
`.env` is fine — the app still records every notification in-app, it just logs
instead of sending. To turn them on:

- **Email**: create a Google account app password at
  [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
  and set `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, `SMTP_USER`, `SMTP_PASSWORD`.
- **SMS**: create a free trial account at [twilio.com/try-twilio](https://www.twilio.com/try-twilio)
  and set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`.

Do not upload the `.env` file to GitHub.

Load the demonstration data:

```bash
python3 seed.py
```

Run the automated backend and database tests:

```bash
pytest test_api.py test_db.py test_auth.py -v
```

A successful setup should report:

```text
39 passed
```

After the tests pass, start the Flask backend:

```bash
python3 app.py
```

The backend should run at:

```text
http://127.0.0.1:5001
```

## Step 3: Load the Demo Data

From the backend folder, run:

```bash
python3 seed.py
```

This creates the demo users, machines, bookings, payments, and subscription information.

## Step 4: Start the Flask Backend

From the backend folder, run:

```bash
source venv/bin/activate
python3 app.py
```

The backend should run at:

```text
http://127.0.0.1:5001
```

Keep the backend terminal open.

## Step 5: Start the SvelteKit Frontend

Open another terminal:

```bash
cd ~/Desktop/LaundryApp/frontend
```

Install the frontend packages:

```bash
npm install
```

Copy the environment file (the default already points at the local backend, so
this step is optional unless the backend runs somewhere else):

```bash
cp .env.example .env
```

Start the development server:

```bash
npm run dev
```

Open the local address shown by Vite, such as:

```text
http://localhost:5173
```

The port number may be different if another port is already being used.

### Deploying

The frontend deploys to Vercel as-is (it already uses `@sveltejs/adapter-auto`,
which detects Vercel at build time). Set `VITE_API_URL` in the Vercel project's
environment variables to point at the deployed backend, and set `ALLOWED_ORIGINS`
on the backend to the deployed frontend's URL so CORS allows it.

## Application Flow

### Tenant Flow

1. Tenant logs in
2. Tenant views available washers and dryers
3. Tenant selects a machine
4. Tenant chooses a date and time
5. The booking is created through the Flask backend
6. The booking is stored in MySQL
7. The machine becomes unavailable
8. The tenant can view the booking
9. The tenant can cancel the booking
10. The machine becomes available again

### Manager Flow

1. Manager logs in
2. Manager opens the Manager Dashboard
3. Manager views machine totals and machine status
4. Manager views live transaction-fee revenue
5. Manager views live subscription revenue
6. Manager views the building subscription plan

## API Examples

Important backend routes include:

```text
POST /login
GET /me
GET /machines
POST /bookings
GET /users/<user_id>/bookings
DELETE /bookings/<booking_id>
POST /machines/<machine_id>/waitlist
GET /users/<user_id>/waitlist
GET /users/<user_id>/notifications
GET /subscriptions
GET /reports/revenue
GET /reports/revenue/timeseries
```

Every route above except `/login`, `/me`'s prerequisite `/users` (signup), and the
public `GET /machines` / `GET /plans` requires an `Authorization: Bearer <token>`
header from `/login`. Ownership and role checks (tenant vs. manager) are enforced
server-side, not just hidden in the UI — see `backend/test_auth.py`.

## Database Logic

The project uses:

- Parameterized SQL queries
- Foreign keys
- Stored procedures
- Triggers
- Indexes
- Views
- Booking conflict prevention
- Role-based frontend behavior
- Revenue calculations
- Subscription tracking

The `sp_book_machine` stored procedure creates bookings.

Database triggers validate bookings and update machine status when bookings are created, cancelled, or completed.

## Testing Completed

The following application flow was tested successfully:

- Tenant login
- Manager login
- Role-based navigation
- Machine availability
- Machine reservation
- Booking creation
- Booking history
- Booking cancellation
- Machine availability after cancellation
- Manager machine dashboard
- Live revenue report and 30-day revenue trend chart
- Live subscription information
- Waitlist join/leave and the notify-on-cancellation flow
- In-app notifications
- Role- and ownership-based access control (tenant vs. manager, own data vs. others')
- Session persistence across a page refresh
- Frontend-to-backend connection
- Backend-to-MySQL connection

## Important Security Note

The `.env` files are excluded from GitHub because they contain local database credentials.

Each person running the application must create their own local `.env` file.

## Current Deployment Status

The application currently runs locally.

GitHub stores the project source code and documentation, but GitHub does not automatically run:

- The MySQL database
- The Flask backend
- The SvelteKit frontend

For a classroom demonstration, start MySQL, the Flask backend, and the frontend locally.
