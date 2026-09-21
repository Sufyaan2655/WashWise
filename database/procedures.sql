-- =====================================================
-- LaundryApp stored procedures and booking triggers
-- =====================================================


-- =====================================================
-- PROCEDURE 1: APPLICATION REVENUE BY BUILDING
-- Returns LaundryApp's transaction-fee revenue and
-- subscription revenue associated with each building.
-- =====================================================

DROP PROCEDURE IF EXISTS sp_revenue_report;

DELIMITER //

CREATE PROCEDURE sp_revenue_report()
BEGIN
    SELECT
        bl.building_id,
        bl.name AS building,

        COALESCE((
            SELECT SUM(bp.transaction_fee)
            FROM booking_payments bp
            JOIN bookings b
                ON bp.booking_id = b.booking_id
            JOIN machines m
                ON b.machine_id = m.machine_id
            WHERE m.building_id = bl.building_id
              AND bp.payment_status = 'paid'
        ), 0) AS booking_revenue,

        COALESCE((
            SELECT SUM(sp.amount)
            FROM subscription_payments sp
            JOIN building_subscriptions bs
                ON sp.subscription_id = bs.subscription_id
            WHERE bs.building_id = bl.building_id
              AND sp.payment_status = 'paid'
        ), 0) AS subscription_revenue

    FROM buildings bl
    ORDER BY bl.building_id;
END //

DELIMITER ;


-- =====================================================
-- PROCEDURE 2: CREATE A BOOKING
-- The validation trigger below checks the booking before
-- MySQL allows the row to be inserted.
-- =====================================================

DROP PROCEDURE IF EXISTS sp_book_machine;

DELIMITER //

CREATE PROCEDURE sp_book_machine(
    IN p_user_id INT,
    IN p_machine_id INT,
    IN p_start_time DATETIME,
    IN p_end_time DATETIME,
    IN p_price DECIMAL(8, 2)
)
BEGIN
    INSERT INTO bookings (
        user_id,
        machine_id,
        start_time,
        end_time,
        price_at_booking,
        booking_status
    )
    VALUES (
        p_user_id,
        p_machine_id,
        p_start_time,
        p_end_time,
        p_price,
        'confirmed'
    );

    SELECT LAST_INSERT_ID() AS booking_id;
END //

DELIMITER ;


-- =====================================================
-- TRIGGER 1: VALIDATE NEW BOOKINGS
-- Prevents:
--   - invalid times
--   - invalid statuses
--   - negative prices
--   - booking unavailable machines
--   - booking a machine from another building
--   - overlapping reservations
-- =====================================================

DROP TRIGGER IF EXISTS trg_booking_before_insert;

DELIMITER //

CREATE TRIGGER trg_booking_before_insert
BEFORE INSERT ON bookings
FOR EACH ROW
BEGIN
    DECLARE v_user_building_id INT;
    DECLARE v_machine_building_id INT;
    DECLARE v_machine_status VARCHAR(30);
    DECLARE v_conflict_count INT DEFAULT 0;

    IF NEW.end_time <= NEW.start_time THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT =
                'The booking end time must be after the start time';
    END IF;

    IF NEW.price_at_booking < 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT =
                'The booking price cannot be negative';
    END IF;

    IF NEW.booking_status NOT IN (
        'pending',
        'confirmed',
        'completed',
        'cancelled'
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT =
                'Invalid booking status';
    END IF;

    SET v_user_building_id = (
        SELECT building_id
        FROM users
        WHERE user_id = NEW.user_id
    );

    SET v_machine_building_id = (
        SELECT building_id
        FROM machines
        WHERE machine_id = NEW.machine_id
    );

    SET v_machine_status = (
        SELECT status
        FROM machines
        WHERE machine_id = NEW.machine_id
    );

    IF v_user_building_id <> v_machine_building_id THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT =
                'The user and machine must belong to the same building';
    END IF;

    IF v_machine_status <> 'active' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT =
                'The selected machine is not operational';
    END IF;

    IF NEW.booking_status IN ('pending', 'confirmed') THEN
        SELECT COUNT(*)
        INTO v_conflict_count
        FROM bookings
        WHERE machine_id = NEW.machine_id
          AND booking_status IN ('pending', 'confirmed')
          AND start_time < NEW.end_time
          AND end_time > NEW.start_time;

        IF v_conflict_count > 0 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT =
                    'The machine is already booked during that time';
        END IF;
    END IF;
END //

DELIMITER ;


-- =====================================================
-- TRIGGER 2: VALIDATE UPDATED BOOKINGS
-- Rechecks the same rules if an existing booking is
-- changed. The current booking is excluded from the
-- overlap search.
-- =====================================================

DROP TRIGGER IF EXISTS trg_booking_before_update;

DELIMITER //

CREATE TRIGGER trg_booking_before_update
BEFORE UPDATE ON bookings
FOR EACH ROW
BEGIN
    DECLARE v_user_building_id INT;
    DECLARE v_machine_building_id INT;
    DECLARE v_machine_status VARCHAR(30);
    DECLARE v_conflict_count INT DEFAULT 0;

    IF NEW.end_time <= NEW.start_time THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT =
                'The booking end time must be after the start time';
    END IF;

    IF NEW.price_at_booking < 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT =
                'The booking price cannot be negative';
    END IF;

    IF NEW.booking_status NOT IN (
        'pending',
        'confirmed',
        'completed',
        'cancelled'
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT =
                'Invalid booking status';
    END IF;

    SET v_user_building_id = (
        SELECT building_id
        FROM users
        WHERE user_id = NEW.user_id
    );

    SET v_machine_building_id = (
        SELECT building_id
        FROM machines
        WHERE machine_id = NEW.machine_id
    );

    SET v_machine_status = (
        SELECT status
        FROM machines
        WHERE machine_id = NEW.machine_id
    );

    IF v_user_building_id <> v_machine_building_id THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT =
                'The user and machine must belong to the same building';
    END IF;

    IF v_machine_status <> 'active' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT =
                'The selected machine is not operational';
    END IF;

    IF NEW.booking_status IN ('pending', 'confirmed') THEN
        SELECT COUNT(*)
        INTO v_conflict_count
        FROM bookings
        WHERE machine_id = NEW.machine_id
          AND booking_id <> OLD.booking_id
          AND booking_status IN ('pending', 'confirmed')
          AND start_time < NEW.end_time
          AND end_time > NEW.start_time;

        IF v_conflict_count > 0 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT =
                    'The machine is already booked during that time';
        END IF;
    END IF;
END //

DELIMITER ;