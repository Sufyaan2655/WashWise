-- LaundryApp database schema
-- Final team-approved data model


-- =====================================================
-- BUILDINGS
-- Stores the apartment buildings that use LaundryApp.
-- =====================================================

CREATE TABLE buildings (
    building_id INT AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (building_id)
);


-- =====================================================
-- USERS
-- Stores tenants and building managers.
-- password_hash stores the encrypted/hashed password,
-- not the user's real password.
-- =====================================================

CREATE TABLE users (
    user_id INT AUTO_INCREMENT,
    building_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone_number VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id),

    FOREIGN KEY (building_id) REFERENCES buildings(building_id)
);


-- =====================================================
-- MACHINES
-- Stores the washers and dryers in each building.
-- =====================================================

CREATE TABLE machines (
    machine_id INT AUTO_INCREMENT,
    building_id INT NOT NULL,
    machine_number INT NOT NULL,
    machine_type VARCHAR(20) NOT NULL,
    cost_per_cycle DECIMAL(8, 2) NOT NULL,
    duration_minutes INT NOT NULL,
    status VARCHAR(30) NOT NULL,

    PRIMARY KEY (machine_id),

    FOREIGN KEY (building_id)
        REFERENCES buildings(building_id)
);


-- =====================================================
-- SUBSCRIPTION PLANS
-- Stores the SaaS plans offered by LaundryApp.
-- =====================================================

CREATE TABLE subscription_plans (
    plan_id INT AUTO_INCREMENT,
    plan_name VARCHAR(100) NOT NULL,
    billing_period VARCHAR(20) NOT NULL,
    subscription_price DECIMAL(10, 2) NOT NULL,
    max_machines INT NOT NULL,
    analytics_level VARCHAR(20) NOT NULL,

    PRIMARY KEY (plan_id)
);


-- =====================================================
-- BOOKINGS
-- Stores reservations made by users.
-- The machine and reservation times are stored directly
-- here, so a TIME_SLOTS table is not needed.
-- =====================================================

CREATE TABLE bookings (
    booking_id INT AUTO_INCREMENT,
    user_id INT NOT NULL,
    machine_id INT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    price_at_booking DECIMAL(8, 2) NOT NULL,
    booking_status VARCHAR(20) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (booking_id),

    FOREIGN KEY (user_id)
        REFERENCES users(user_id),

    FOREIGN KEY (machine_id)
        REFERENCES machines(machine_id)
);


-- =====================================================
-- BUILDING SUBSCRIPTIONS
-- Connects each building to the subscription plan
-- selected by that building.
-- =====================================================

CREATE TABLE building_subscriptions (
    subscription_id INT AUTO_INCREMENT,
    building_id INT NOT NULL,
    plan_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    subscription_status VARCHAR(20) NOT NULL,

    PRIMARY KEY (subscription_id),

    FOREIGN KEY (building_id)
        REFERENCES buildings(building_id),

    FOREIGN KEY (plan_id)
        REFERENCES subscription_plans(plan_id)
);


-- =====================================================
-- BOOKING PAYMENTS
-- Stores tenant payments for laundry cycles.
-- gross_amount is divided between LaundryApp's fee
-- and the amount credited to the building.
-- =====================================================

CREATE TABLE booking_payments (
    payment_id INT AUTO_INCREMENT,
    booking_id INT NOT NULL,
    gross_amount DECIMAL(10, 2) NOT NULL,
    transaction_fee_rate DECIMAL(5, 2) NOT NULL,
    transaction_fee DECIMAL(10, 2) NOT NULL,
    building_amount DECIMAL(10, 2) NOT NULL,
    payment_status VARCHAR(20) NOT NULL,
    payment_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (payment_id),

    FOREIGN KEY (booking_id)
        REFERENCES bookings(booking_id)
);


-- =====================================================
-- SUBSCRIPTION PAYMENTS
-- Stores monthly or annual subscription payments
-- made by buildings to LaundryApp.
-- =====================================================

CREATE TABLE subscription_payments (
    subscription_payment_id INT AUTO_INCREMENT,
    subscription_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_status VARCHAR(20) NOT NULL,
    payment_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    billing_period_start DATE NOT NULL,
    billing_period_end DATE NOT NULL,

    PRIMARY KEY (subscription_payment_id),

    FOREIGN KEY (subscription_id)
        REFERENCES building_subscriptions(subscription_id)
);


-- =====================================================
-- NOTIFICATIONS
-- In-app notifications for tenants and managers.
-- Email/SMS delivery (when configured) mirrors these rows.
-- =====================================================

CREATE TABLE notifications (
    notification_id INT AUTO_INCREMENT,
    user_id INT NOT NULL,
    category VARCHAR(40) NOT NULL,
    message VARCHAR(255) NOT NULL,
    is_read TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (notification_id),

    FOREIGN KEY (user_id) REFERENCES users(user_id)
);


-- =====================================================
-- WAITLIST
-- Tenants waiting for a machine that is currently busy.
-- =====================================================

CREATE TABLE waitlist (
    waitlist_id INT AUTO_INCREMENT,
    machine_id INT NOT NULL,
    user_id INT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'waiting',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (waitlist_id),

    FOREIGN KEY (machine_id) REFERENCES machines(machine_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);