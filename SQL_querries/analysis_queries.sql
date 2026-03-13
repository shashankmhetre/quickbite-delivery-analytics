CREATE DATABASE IF NOT EXISTS food_delivery;
USE food_delivery;


-- -------------------------------------------------------
-- SECTION 1: BUSINESS OVERVIEW
-- -------------------------------------------------------

-- total orders, revenue, and cancellation rate in one shot
select
    count(*) as total_orders,
    round(sum(order_value), 2) as total_revenue,
    round(avg(order_value), 2) as avg_order_value,
    sum(order_status = 'Cancelled') as cancelled_orders,
    round(100 * sum(order_status = 'Cancelled') / count(*), 2) as cancellation_rate_pct
from orders;


-- avg delivery time across all completed orders
select round(avg(delivery_time_minutes), 1) as avg_delivery_time_mins
from deliveries d
join orders o on d.order_id = o.order_id
where o.order_status = 'Delivered';


-- payment method breakdown
select
    payment_method,
    count(*) as total_orders,
    round(sum(order_value), 2) as total_revenue,
    round(100 * count(*) / sum(count(*)) over(), 2) as pct_of_orders
from orders
group by payment_method
order by total_orders desc;


-- -------------------------------------------------------
-- SECTION 2: RESTAURANT ANALYSIS
-- -------------------------------------------------------

-- top 10 restaurants by revenue
select
    r.restaurant_id,
    r.restaurant_name,
    r.city,
    r.cuisine,
    count(o.order_id) as total_orders,
    round(sum(o.order_value), 2) as total_revenue,
    round(avg(o.order_value), 2) as avg_order_value
from orders o
join restaurants r on o.restaurant_id = r.restaurant_id
where o.order_status = 'Delivered'
group by r.restaurant_id, r.restaurant_name, r.city, r.cuisine
order by total_revenue desc
limit 10;


-- cuisine popularity by order volume and revenue
select
    r.cuisine,
    count(o.order_id) as total_orders,
    round(sum(o.order_value), 2) as total_revenue,
    round(avg(o.order_value), 2) as avg_order_value
from orders o
join restaurants r on o.restaurant_id = r.restaurant_id
where o.order_status = 'Delivered'
group by r.cuisine
order by total_orders desc;


-- restaurant performance ranking using window functions
-- ranks each restaurant by both revenue and order volume
select
    r.restaurant_name,
    r.cuisine,
    r.city,
    r.rating,
    count(o.order_id) as total_orders,
    round(sum(o.order_value), 2) as total_revenue,
    round(avg(d.delivery_time_minutes), 1) as avg_delivery_mins,
    rank() over(order by sum(o.order_value) desc) as revenue_rank,
    rank() over(order by count(o.order_id) desc) as order_rank
from orders o
join restaurants r on o.restaurant_id = r.restaurant_id
join deliveries d on o.order_id = d.order_id
where o.order_status = 'Delivered'
group by r.restaurant_id, r.restaurant_name, r.cuisine, r.city, r.rating
order by revenue_rank;


-- -------------------------------------------------------
-- SECTION 3: CUSTOMER ANALYSIS
-- -------------------------------------------------------

-- most active customers by order count and total spend
select
    c.customer_id,
    c.customer_name,
    c.city,
    c.loyalty_tier,
    count(o.order_id) as total_orders,
    round(sum(o.order_value), 2) as total_spent,
    round(avg(o.order_value), 2) as avg_order_value
from orders o
join customers c on o.customer_id = c.customer_id
where o.order_status = 'Delivered'
group by c.customer_id, c.customer_name, c.city, c.loyalty_tier
order by total_orders desc
limit 10;


-- customer lifetime value segmentation
with customer_stats as (
    select
        c.customer_id,
        c.customer_name,
        c.city,
        c.loyalty_tier,
        count(o.order_id) as order_count,
        round(sum(o.order_value), 2) as total_spent,
        min(o.order_date) as first_order_date,
        max(o.order_date) as last_order_date,
        datediff(max(o.order_date), min(o.order_date)) as active_days
    from orders o
    join customers c on o.customer_id = c.customer_id
    where o.order_status = 'Delivered'
    group by c.customer_id, c.customer_name, c.city, c.loyalty_tier
)
select *,
    case
        when order_count >= 10 and total_spent >= 3000 then 'High Value'
        when order_count >= 5  and total_spent >= 1500 then 'Regular'
        when order_count >= 2  then 'Occasional'
        else 'At Risk'
    end as customer_segment
from customer_stats
order by total_spent desc;


-- RFM analysis — recency, frequency, monetary per customer
with rfm_base as (
    select
        c.customer_id,
        c.customer_name,
        c.city,
        datediff(max(o.order_date) over(), max(o.order_date)) as recency_days,
        count(o.order_id) as frequency,
        round(sum(o.order_value), 2) as monetary,
        max(o.order_date) as last_order_date
    from orders o
    join customers c on o.customer_id = c.customer_id
    where o.order_status = 'Delivered'
    group by c.customer_id, c.customer_name, c.city
)
select * from rfm_base
order by monetary desc;


-- customers who haven't ordered in the last 60 days (churn risk)
select
    c.customer_id,
    c.customer_name,
    c.city,
    c.loyalty_tier,
    max(o.order_date) as last_order_date,
    datediff(curdate(), max(o.order_date)) as days_since_last_order
from orders o
join customers c on o.customer_id = c.customer_id
where o.order_status = 'Delivered'
group by c.customer_id, c.customer_name, c.city, c.loyalty_tier
having days_since_last_order > 60
order by days_since_last_order desc;


-- -------------------------------------------------------
-- SECTION 4: DELIVERY ANALYSIS
-- -------------------------------------------------------

-- delivery partner efficiency — includes a derived mins_per_km score
select
    dp.partner_name,
    dp.city,
    dp.vehicle_type,
    dp.experience_years,
    count(d.delivery_id) as total_deliveries,
    round(avg(d.delivery_time_minutes), 1) as avg_delivery_time_mins,
    round(avg(d.distance_km), 1) as avg_distance_km,
    round(sum(d.distance_km), 1) as total_distance_km,
    round(avg(d.delivery_rating), 2) as avg_rating,
    round(avg(d.delivery_time_minutes) / nullif(avg(d.distance_km), 0), 2) as mins_per_km
from deliveries d
join delivery_partners dp on d.partner_id = dp.partner_id
group by dp.partner_id, dp.partner_name, dp.city, dp.vehicle_type, dp.experience_years
order by mins_per_km asc;


-- avg delivery time by vehicle type
select
    dp.vehicle_type,
    count(d.delivery_id) as total_deliveries,
    round(avg(d.delivery_time_minutes), 1) as avg_delivery_time_mins,
    round(avg(d.distance_km), 1) as avg_distance_km,
    round(avg(d.delivery_rating), 2) as avg_rating
from deliveries d
join delivery_partners dp on d.partner_id = dp.partner_id
group by dp.vehicle_type;


-- city-wise order volume, revenue, and avg delivery time
select
    c.city,
    count(o.order_id) as total_orders,
    round(sum(o.order_value), 2) as total_revenue,
    round(avg(o.order_value), 2) as avg_order_value,
    round(avg(d.delivery_time_minutes), 1) as avg_delivery_time_mins
from orders o
join customers c on o.customer_id = c.customer_id
join deliveries d on o.order_id = d.order_id
where o.order_status = 'Delivered'
group by c.city
order by total_revenue desc;


-- -------------------------------------------------------
-- SECTION 5: TIME-BASED TRENDS
-- -------------------------------------------------------

-- busiest hour of the day by order volume
select
    hour(order_time) as order_hour,
    count(*) as total_orders,
    round(sum(order_value), 2) as revenue
from orders
where order_status = 'Delivered'
group by hour(order_time)
order by total_orders desc;


-- orders by day of the week
select
    dayname(order_date) as day_of_week,
    count(*) as total_orders,
    round(sum(order_value), 2) as total_revenue
from orders
where order_status = 'Delivered'
group by dayname(order_date), dayofweek(order_date)
order by dayofweek(order_date);


-- monthly revenue with month-on-month growth rate
with monthly_revenue as (
    select
        date_format(order_date, '%Y-%m') as month,
        round(sum(order_value), 2) as revenue
    from orders
    where order_status = 'Delivered'
    group by date_format(order_date, '%Y-%m')
)
select
    month,
    revenue,
    lag(revenue) over(order by month) as prev_month_revenue,
    round(
        100 * (revenue - lag(revenue) over(order by month))
        / nullif(lag(revenue) over(order by month), 0),
    2) as mom_growth_pct
from monthly_revenue
order by month;


-- peak ordering months — ranked by total revenue
select
    date_format(order_date, '%Y-%m') as month,
    count(*) as total_orders,
    round(sum(order_value), 2) as total_revenue,
    rank() over(order by sum(order_value) desc) as revenue_rank
from orders
where order_status = 'Delivered'
group by date_format(order_date, '%Y-%m')
order by revenue_rank;
