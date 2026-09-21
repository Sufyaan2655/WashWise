# Data Model Changes

The final data model was updated to better support the complete LaundryApp software and its revenue model.

The TIME_SLOTS table was removed because storing predefined time slots and availability statuses could create redundant or inconsistent data. Instead, machine_id, start_time, and end_time are stored directly in the BOOKINGS table. Machine availability can be determined by checking existing bookings.

The USERS table was updated with password_hash so the backend can support secure login without storing plain-text passwords.

The payment structure was also updated to represent the revenue model from the mid-pitch presentation. BOOKING_PAYMENTS stores the total tenant payment, LaundryApp's transaction fee, and the amount credited to the building. SUBSCRIPTION_PLANS, BUILDING_SUBSCRIPTIONS, and SUBSCRIPTION_PAYMENTS represent the monthly or annual SaaS fees that buildings pay LaundryApp.

These changes make the database more consistent with the reservation workflow, authentication requirements, and application revenue streams. The final design complies with at least Second Normal Form because each table uses a primary key and its non-key attributes depend on the complete primary key.