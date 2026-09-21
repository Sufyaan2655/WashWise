# LaundryApp Database

This folder contains the MySQL database implementation for LaundryApp.

## Files

- `schema.sql` creates the eight database tables and their relationships.
- `sample_data.sql` inserts development sample records for testing.
- `queries.sql` contains tested SQL queries used by the application.
- `procedures.sql` creates stored procedures and booking validation triggers.
- `indexes_views.sql` creates performance indexes and reusable views.

## Requirements

Install and start Docker Desktop before running the database.

## Environment setup

From the root of the repository, create a local `.env` file from the example:

```powershell
Copy-Item .env.example .env