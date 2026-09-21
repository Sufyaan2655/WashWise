-- =====================================================================
-- WashWise / LaundryApp — Indexes + Views
-- =====================================================================

USE washwise;

-- Indexes on the columns we filter by (FKs are auto-indexed by InnoDB)
CREATE INDEX idx_machines_status  ON machines (status);
CREATE INDEX idx_bookings_status  ON bookings (booking_status);
CREATE INDEX idx_bookings_date    ON bookings (start_time);
CREATE INDEX idx_bpay_status      ON booking_payments (payment_status);
CREATE INDEX idx_spay_status      ON subscription_payments (payment_status);
CREATE INDEX idx_notifications_user ON notifications (user_id, is_read);
CREATE INDEX idx_waitlist_machine    ON waitlist (machine_id, status);

-- View: revenue per building, both streams combined
CREATE OR REPLACE VIEW v_revenue_by_building AS
SELECT
    bl.building_id,
    bl.name AS building,
    COALESCE((
        SELECT SUM(bp.transaction_fee)
        FROM booking_payments bp
        JOIN bookings b ON bp.booking_id = b.booking_id
        JOIN machines m ON b.machine_id = m.machine_id
        WHERE m.building_id = bl.building_id AND bp.payment_status = 'paid'
    ), 0) AS booking_revenue,
    COALESCE((
        SELECT SUM(sp.amount)
        FROM subscription_payments sp
        JOIN building_subscriptions bs ON sp.subscription_id = bs.subscription_id
        WHERE bs.building_id = bl.building_id AND sp.payment_status = 'paid'
    ), 0) AS subscription_revenue
FROM buildings bl;

-- View: full booking detail (tenant + machine + building)
CREATE OR REPLACE VIEW v_booking_details AS
SELECT
    b.booking_id,
    u.name  AS tenant,
    bl.name AS building,
    m.machine_number,
    m.machine_type,
    b.start_time,
    b.end_time,
    b.price_at_booking,
    b.booking_status
FROM bookings b
JOIN users u      ON b.user_id = u.user_id
JOIN machines m   ON b.machine_id = m.machine_id
JOIN buildings bl ON m.building_id = bl.building_id;

-- View: active building subscriptions with plan detail
CREATE OR REPLACE VIEW v_active_subscriptions AS
SELECT
    bs.subscription_id,
    bl.name AS building,
    p.plan_name,
    p.subscription_price,
    p.billing_period,
    bs.start_date,
    bs.subscription_status
FROM building_subscriptions bs
JOIN buildings bl        ON bs.building_id = bl.building_id
JOIN subscription_plans p ON bs.plan_id = p.plan_id
WHERE bs.subscription_status = 'active';
