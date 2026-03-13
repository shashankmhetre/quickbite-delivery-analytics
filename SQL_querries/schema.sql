-- QuickBite Delivery Analytics — MySQL Schema
-- Import order must be followed: customers → restaurants → delivery_partners → orders → deliveries

CREATE DATABASE IF NOT EXISTS quickbite;
USE quickbite;

-- 1. Customers
CREATE TABLE customers (
    customer_id         VARCHAR(20) PRIMARY KEY,
    customer_name       VARCHAR(100),
    city                VARCHAR(50),
    signup_date         DATE,
    loyalty_tier        VARCHAR(20),
    avg_order_value     DECIMAL(10, 2),
    preferred_payment_method VARCHAR(50)
);

-- 2. Restaurants
CREATE TABLE restaurants (
    restaurant_id       VARCHAR(20) PRIMARY KEY,
    restaurant_name     VARCHAR(100),
    city                VARCHAR(50),
    cuisine             VARCHAR(50),
    avg_prep_time_minutes INT,
    rating              DECIMAL(3, 1),
    price_category      VARCHAR(20)
);

-- 3. Delivery Partners
CREATE TABLE delivery_partners (
    partner_id          VARCHAR(20) PRIMARY KEY,
    partner_name        VARCHAR(100),
    city                VARCHAR(50),
    experience_years    DECIMAL(4, 1),
    vehicle_type        VARCHAR(20),
    join_date           DATE,
    avg_rating          DECIMAL(3, 1)
);

-- 4. Orders (depends on customers, restaurants)
CREATE TABLE orders (
    order_id            VARCHAR(20) PRIMARY KEY,
    customer_id         VARCHAR(20),
    restaurant_id       VARCHAR(20),
    order_date          DATE,
    order_time          TIME,
    order_value         DECIMAL(10, 2),
    payment_method      VARCHAR(50),
    order_status        VARCHAR(20),
    FOREIGN KEY (customer_id)   REFERENCES customers(customer_id),
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(restaurant_id)
);

-- 5. Deliveries (depends on orders, delivery_partners)
CREATE TABLE deliveries (
    delivery_id         VARCHAR(20) PRIMARY KEY,
    order_id            VARCHAR(20),
    partner_id          VARCHAR(20),
    distance_km         DECIMAL(5, 2),
    delivery_time_minutes DECIMAL(5, 1),
    delivery_rating     DECIMAL(3, 1),
    restaurant_rating   DECIMAL(3, 1),
    FOREIGN KEY (order_id)   REFERENCES orders(order_id),
    FOREIGN KEY (partner_id) REFERENCES delivery_partners(partner_id)
);
