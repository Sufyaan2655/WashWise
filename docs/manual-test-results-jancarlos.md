# WashWise Manual and Automated Test Results

**Tester:** Jancarlos Jaquez  
**Role:** Testing 
**Environment:** macOS, Python 3.9.13, MySQL Workbench

## Testing Objective

The purpose of this testing was to verify that a new developer could
download the current project, install the required dependencies, create
the database, load the demonstration data, start the backend, and run
the automated test suite successfully.

## Test 1: Python Dependency Installation

### Command

```bash
pip install -r requirements.txt
```

### Expected Result

All required Python packages should install successfully.

### Original Result

The installation failed because the project required:

```text
pytest==9.1.1
```

This version was not compatible with Python 3.9.13.

### Resolution

The pytest requirement was changed to:

```text
pytest==8.4.2
```

### Final Status

PASS

## Test 2: Flask Backend Startup

### Command

```bash
python3 app.py
```

### Expected Result

The Flask backend should start successfully on port 5001.

### Original Result

Python reported a syntax error inside the `create_booking()` function.
A description beginning with `A BEFORE INSERT trigger validates the
booking` was located outside the function's triple-quoted docstring.

### Resolution

The malformed multiline docstring in `backend/app.py` was corrected.

### Final Status

PASS

## Test 3: Database Objects and Views

### Command

```bash
pytest test_api.py test_db.py -v
```

### Expected Result

All automated backend and database tests should pass.

### Original Result

The first test run produced:

```text
1 failed, 21 passed
```

The failing test reported that the following database view did not
exist:

```text
washwise.v_active_subscriptions
```

### Resolution

The `backend/indexes_views.sql` file was executed in MySQL Workbench to
create the required indexes and views.

### Final Status

PASS

## Test 4: Complete Automated Test Suite

### Command

```bash
pytest test_api.py test_db.py -v
```

### Final Result

```text
22 passed
```

### Final Status

PASS

## Documentation Findings

The setup documentation contained the database name:

```text
laundry_app
```

The current SQL scripts and backend configuration use:

```text
washwise
```

The README was updated to use the correct database name and to explain
that all three SQL files must be executed:

1. `backend/schema.sql`
2. `backend/procedures.sql`
3. `backend/indexes_views.sql`

The README was also updated with the commands for seeding the database,
running the automated tests, and starting the backend.

## Conclusion

The local setup problems were identified, documented, and corrected.
After applying the fixes, the Python dependencies installed
successfully, the Flask backend started correctly, all required MySQL
objects were available, and the complete automated test suite passed
with 22 tests.
