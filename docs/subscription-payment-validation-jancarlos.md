# Subscription Payment Validation Test Results

**Tester:** Jancarlos Jaquez  
**Role:** Testing
**Environment:** macOS, Python 3.9.13, Flask, MySQL

## Objective

The purpose of this testing was to verify that the
`POST /subscription-payments` endpoint accepts valid subscription
payments and rejects invalid financial and billing information before
it is inserted into the database.

## Endpoint Tested

```text
POST /subscription-payments
```

## Original Behavior

The endpoint checked whether the required fields were present, but it
did not fully validate the values of those fields.

The endpoint could accept:

- Negative payment amounts
- Zero payment amounts
- Nonnumeric payment amounts
- Billing periods whose end date occurred before the start date
- Unsupported payment statuses
- Incorrectly formatted billing dates

Allowing invalid subscription payment records could affect billing
history, financial reporting, and revenue calculations.

## Automated Tests Added

Automated tests were added to verify that:

1. A valid subscription payment returns HTTP 201.
2. A negative payment amount returns HTTP 400.
3. A reversed billing period returns HTTP 400.
4. An unsupported payment status returns HTTP 400.

## Automated Test Result Before Fix

```text
3 failed, 23 passed
```

The three failing tests showed that invalid subscription payment
requests were being accepted instead of returning HTTP 400.

## Validation Added

The subscription payment endpoint was updated to enforce the following
rules:

- The payment amount must be numeric.
- The payment amount must be greater than zero.
- The payment status must be one of:
  - `paid`
  - `pending`
  - `refunded`
- the billing period start date must use the `YYYY-MM-DD` format
- the billing period end date must use the `YYYY-MM-DD` format.
- the billing period end date must be on or after the start date

Invalid requests now return HTTP 400 with a clear error message.

## Manual Test Results

|           Test             |  Expected Result  | Actual Result | Status |

| Negative payment amount    |      HTTP 400     |   HTTP 400    | PASS   |
| Reversed billing period    |      HTTP 400     |   HTTP 400    | PASS   |
| Unsupported payment status |      HTTP 400     |   HTTP 400    | PASS   |
| Valid subscription payment |      HTTP 201     |   HTTP 201    | PASS   |

## Automated Test Result After Fix

```text
26 passed
```

The new subscription payment tests passed, and all previously existing
backend and database tests continued to pass.

## Conclusion

The subscription payment endpoint now validates payment and
billing period information before inserting a record into MySQL.

The changes prevent invalid financial records from affecting:

- Subscription billing history
- Building payment records
- Revenue reports
- Manager dashboard information
- Overall financial data accuracy

The final automated test suite completed successfully with all 26 tests
passing.
