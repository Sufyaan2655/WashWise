-- =====================================================================
-- WashWise / LaundryApp — Database schema (8 tables)
--
-- Local development copy so the backend can run and be tested on its own.
-- The database team owns the authoritative schema (see /database/schema.sql);
-- the two are column-compatible.
-- =====================================================================

CREATE DATABASE IF NOT EXISTS washwise;
USE washwise;

-- Drop children first so this file is re-runnable
DROP TABLE IF EXISTS waitlist;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS subscription_payments;
DROP TABLE IF EXISTS booking_payments;
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS building_subscriptions;
DROP TABLE IF EXISTS subscription_plans;
DROP TABLE IF EXISTS machines;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS buildings;

-- 1) BUILDINGS
CREATE TABLE buildings (
    building_id INT NOT NULL AUTO_INCREMENT,
    name        VARCHAR(100) NOT NULL,
    address     VARCHAR(255) NOT NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (building_id)
);

-- 2) USERS (tenant or manager)
CREATE TABLE users (
    user_id       INT NOT NULL AUTO_INCREMENT,
    building_id   INT NOT NULL,
    name          VARCHAR(100) NOT NULL,
    email         VARCHAR(255) NOT NULL,
    phone_number  VARCHAR(20),                    -- optional, used for SMS notifications
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(20)  NOT NULL,          -- 'tenant' | 'manager'
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    UNIQUE KEY uq_users_email (email),
    CONSTRAINT fk_users_building
        FOREIGN KEY (building_id) REFERENCES buildings (building_id)
);

-- 3) MACHINES (washers/dryers)
CREATE TABLE machines (
    machine_id       INT NOT NULL AUTO_INCREMENT,
    building_id      INT NOT NULL,
    machine_number   INT NOT NULL,
    machine_type     VARCHAR(20)  NOT NULL,       -- 'washer' | 'dryer'
    cost_per_cycle   DECIMAL(8,2) NOT NULL,
    duration_minutes INT NOT NULL,
    status           VARCHAR(30)  NOT NULL,       -- 'active' | 'maintenance'
    PRIMARY KEY (machine_id),
    CONSTRAINT fk_machines_building
        FOREIGN KEY (building_id) REFERENCES buildings (building_id)
);

-- 4) SUBSCRIPTION_PLANS (SaaS tiers buildings can buy)
CREATE TABLE subscription_plans (
    plan_id            INT NOT NULL AUTO_INCREMENT,
    plan_name          VARCHAR(100) NOT NULL,
    billing_period     VARCHAR(20)  NOT NULL,     -- 'monthly' | 'yearly'
    subscription_price DECIMAL(10,2) NOT NULL,
    max_machines       INT NOT NULL,
    analytics_level    VARCHAR(20)  NOT NULL,     -- 'basic' | 'advanced'
    PRIMARY KEY (plan_id)
);

-- 5) BUILDING_SUBSCRIPTIONS (which building is on which plan)
CREATE TABLE building_subscriptions (
    subscription_id     INT NOT NULL AUTO_INCREMENT,
    building_id         INT NOT NULL,
    plan_id             INT NOT NULL,
    start_date          DATE NOT NULL,
    end_date            DATE,
    subscription_status VARCHAR(20) NOT NULL,     -- 'active' | 'cancelled' | 'expired'
    PRIMARY KEY (subscription_id),
    CONSTRAINT fk_bsub_building
        FOREIGN KEY (building_id) REFERENCES buildings (building_id),
    CONSTRAINT fk_bsub_plan
        FOREIGN KEY (plan_id) REFERENCES subscription_plans (plan_id)
);

-- 6) BOOKINGS (junction: users <-> machines)
CREATE TABLE bookings (
    booking_id       INT NOT NULL AUTO_INCREMENT,
    user_id          INT NOT NULL,
    machine_id       INT NOT NULL,
    start_time       DATETIME NOT NULL,
    end_time         DATETIME NOT NULL,
    price_at_booking DECIMAL(10,2) NOT NULL,
    booking_status   VARCHAR(20) NOT NULL,        -- 'pending' | 'confirmed' | 'completed' | 'cancelled'
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (booking_id),
    CONSTRAINT fk_bookings_user
        FOREIGN KEY (user_id) REFERENCES users (user_id),
    CONSTRAINT fk_bookings_machine
        FOREIGN KEY (machine_id) REFERENCES machines (machine_id)
);

-- 7) BOOKING_PAYMENTS (tenant pays for a booking; app keeps a transaction fee)
CREATE TABLE booking_payments (
    payment_id           INT NOT NULL AUTO_INCREMENT,
    booking_id           INT NOT NULL,
    gross_amount         DECIMAL(10,2) NOT NULL,  -- total the tenant paid
    transaction_fee_rate DECIMAL(5,2) NOT NULL,   -- e.g. 0.1500 = 15%
    transaction_fee      DECIMAL(10,2) NOT NULL,  -- app revenue
    building_amount      DECIMAL(10,2) NOT NULL,  -- paid to the building
    payment_status       VARCHAR(20)  NOT NULL,   -- 'paid' | 'pending' | 'refunded'
    payment_date         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (payment_id),
    CONSTRAINT fk_bpay_booking
        FOREIGN KEY (booking_id) REFERENCES bookings (booking_id)
);

-- 8) SUBSCRIPTION_PAYMENTS (recurring SaaS fee a building pays the app)
CREATE TABLE subscription_payments (
    subscription_payment_id INT NOT NULL AUTO_INCREMENT,
    subscription_id         INT NOT NULL,
    amount                  DECIMAL(10,2) NOT NULL,
    payment_status          VARCHAR(20)  NOT NULL,
    payment_date            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    billing_period_start    DATE NOT NULL,
    billing_period_end      DATE NOT NULL,
    PRIMARY KEY (subscription_payment_id),
    CONSTRAINT fk_spay_subscription
        FOREIGN KEY (subscription_id) REFERENCES building_subscriptions (subscription_id)
);

-- 9) NOTIFICATIONS (in-app notifications; email/SMS are sent alongside these)
CREATE TABLE notifications (
    notification_id INT NOT NULL AUTO_INCREMENT,
    user_id          INT NOT NULL,
    category         VARCHAR(40)  NOT NULL,        -- e.g. 'booking_confirmed', 'waitlist_available'
    message          VARCHAR(255) NOT NULL,
    is_read          TINYINT(1)   NOT NULL DEFAULT 0,
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (notification_id),
    CONSTRAINT fk_notifications_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
);

-- 10) WAITLIST (tenants waiting on a machine that is currently unavailable)
CREATE TABLE waitlist (
    waitlist_id INT NOT NULL AUTO_INCREMENT,
    machine_id  INT NOT NULL,
    user_id     INT NOT NULL,
    status      VARCHAR(20) NOT NULL DEFAULT 'waiting', -- 'waiting' | 'notified'
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (waitlist_id),
    CONSTRAINT fk_waitlist_machine
        FOREIGN KEY (machine_id) REFERENCES machines (machine_id),
    CONSTRAINT fk_waitlist_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
);
