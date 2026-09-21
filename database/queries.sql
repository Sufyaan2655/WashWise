-- LaundryApp queries


-- =====================================================
-- BOOKING DETAILS
-- Shows each booking with its user, machine, building,
-- and payment split when a payment exists.
-- =====================================================

SELECT
    b.booking_id,
    u.name AS user_name,
    m.machine_type,
    m.machine_number,
    bu.name AS building_name,
    b.price_at_booking,
    bp.transaction_fee,
    bp.building_amount,
    b.booking_status
FROM bookings b
JOIN users u
    ON b.user_id = u.user_id
JOIN machines m
    ON b.machine_id = m.machine_id
JOIN buildings bu
    ON m.building_id = bu.building_id
LEFT JOIN booking_payments bp
    ON b.booking_id = bp.booking_id;