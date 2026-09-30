-- **************************************************************
-- (a) Order Totals
-- Expected Output:
-- total_orders | total_revenue | avg_order_value
-- 180          | 99860.20      | 554.78
-- ************************************************************** 
SELECT
    COUNT(*) AS total_orders,
    ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)),2) AS total_revenue,
    ROUND(AVG(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)),2) AS avg_order_value
FROM orders o JOIN products p
ON o.product_id = p.product_id;


-- **********************************************************
-- (b) COUNT(*) vs COUNT(column) and difference
-- Expected Output:
-- total_rows | rated_orders | unrated_orders
-- 180        | 165          | 15
-- *********************************************************
SELECT
    COUNT(*) AS total_rows,
    COUNT(rating) AS rated_orders,
    COUNT(*) - COUNT(rating) AS unrated_orders
FROM orders;

-- ************************************************************
-- (c) LEFT JOIN with a genuine zero-match row
-- Expected Output: both queries return exactly one row
-- customer_id | name
-- C045        | Vihaan
-- *************************************************************
SELECT c.customer_id, c.name, count(o.order_id)
	FROM customers c LEFT JOIN orders o
	ON c.customer_id=o.customer_id
GROUP BY c.customer_id, c.name HAVING count(o.order_id)=0;

SELECT customer_id, name FROM customers
WHERE customer_id NOT IN (
	SELECT DISTINCT customer_id FROM orders
);

-- ============================================================
-- (d) GROUP BY + HAVING
-- Expected Output:
-- Jaipur      19   8   42.1
-- Lucknow     49   15  30.6
-- Bangalore   33   8   24.2
-- ============================================================
SELECT c.city, count(order_id) as total_orders,
	sum(o.returned)  AS returned_orders,
    Round((sum(o.returned)/count(order_id)*100),1) AS return_rate_pct 
	FROM customers c  JOIN orders o
	ON c.customer_id=o.customer_id
GROUP BY c.city 
HAVING return_rate_pct > 20
ORDER BY return_rate_pct DESC;

-- ********************************************************
-- (e.i) Top 5 customers by spend
-- Tie-breaker:
-- Ordering by customer_id ensures deterministic results when
-- two customers have the same total spend.
-- Expected Output:
-- C043 Reyansh 12920.00
-- C026 Isha     8371.60
-- C008 Meera    4564.60
-- C011 Arjun    4111.00
-- C042 Sanya    3785.00
-- ************************************************************
SELECT c.customer_id, c.name, 
    sum(Round(p.price*o.quantity * (1 - COALESCE(o.discount_pct, 0) / 100.0),2)) as total_spend
FROM customers c JOIN orders o on c.customer_id =o.customer_id
	JOIN products p on p.product_id=o.product_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, customer_id ASC
LIMIT 5;

-- ************************************************************
-- (e.ii) Rank 3-5 using LIMIT/OFFSET
-- Expected Output:
-- C008 Meera	4564.60
-- C011 Arjun	4111.00
-- C042 Sanya	3785.00
-- ************************************************************
SELECT c.customer_id, c.name, 
    sum(Round(p.price*o.quantity * (1 - COALESCE(o.discount_pct, 0) / 100.0),2)) as total_spend
FROM customers c JOIN orders o on c.customer_id =o.customer_id
	JOIN products p on p.product_id=o.product_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, customer_id ASC
LIMIT 3 OFFSET 2;

-- ************************************************************
-- (f) Three-table JOIN with GROUP BY
-- Expected Output:
-- Haircare      54   44956.10
-- Skincare      60   27346.00
-- Babycare      30   16805.00
-- PersonalCare  36   10753.10
-- ************************************************************
SELECT p.category, count(o.product_id) as order_count,
    sum(Round(p.price*o.quantity * (1 - COALESCE(o.discount_pct, 0) / 100.0),2)) as category_revenue
FROM customers c JOIN orders o on c.customer_id =o.customer_id
	JOIN products p on p.product_id=o.product_id
GROUP BY p.category
ORDER BY category_revenue DESC;


-- ************************************************************
-- (g) LIKE pattern match
-- Expected Output:
-- C001	Aarav	Mumbai
-- C003	Aditi	Mumbai
-- C004	Ananya	Lucknow
-- C011	Arjun	Bangalore
-- C021	Aryan	Bangalore
-- C030	Anika	Bangalore
-- C031	Aditya	Jaipur
-- C036	Aisha	Delhi
-- C041	Ayaan	Lucknow
-- C044	Aria	Bangalore
-- ************************************************************
SELECT customer_id, name, city
FROM customers
WHERE name like 'A%';

-- ************************************************************
-- (h) DISTINCT
-- Expected Output:
-- Ad
-- Organic
-- Referral
-- Social
-- ************************************************************
SELECT DISTINCT c.acquisition_source
FROM customers c
ORDER BY c.acquisition_source;


-- ************************************************************
-- ALTER TABLE + UPDATE with CASE
-- ************************************************************

ALTER TABLE customers
ADD COLUMN `loyalty_tier` VARCHAR(10);

SET SQL_SAFE_UPDATES = 0;
UPDATE customers
SET loyalty_tier =
CASE
    WHEN city_tier = 1 THEN 'Gold'
    ELSE 'Silver'
END;
SET SQL_SAFE_UPDATES = 1;


-- ************************************************************
-- Expected Output:
-- Gold   28
-- Silver 17
-- ************************************************************

SELECT
    loyalty_tier,
    COUNT(*) AS customer_count
FROM customers
GROUP BY loyalty_tier;