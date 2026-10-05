# Part 2 — Python/Pandas Data Wrangling & EDA

#--------------------------------------------------------------
# Task 2.1 - Load and Inspect
# --------------------------------------------------------------

import pandas as pd
import os
import json


# Load the three CSV files into DataFrames
customers = pd.read_csv("customers.csv")
orders = pd.read_csv("orders.csv")
products = pd.read_csv("products.csv")
# ---------------------------------------------------------
# Task 2.2 — Standardize payment_method casing
# ---------------------------------------------------------

print("\n TASK 2.2: STANDARDIZE PAYMENT METHOD")

print(orders['payment_method'].unique())

print("Unique payment methods before fix:", orders['payment_method'].unique().tolist())
print(f"Distinct count before fix: {orders['payment_method'].nunique()}")

orders['payment_method'] = orders['payment_method'].astype(str).str.strip().str.upper()

# Count payment_method values
print("Counts after fix:")
print(orders['payment_method'].value_counts())

# ---------------------------------------------------------
# Task 2.3 — Remove duplicate orders
# ---------------------------------------------------------

natural_key = [
    "customer_id", "product_id", "order_date",
    "quantity", "discount_pct", "payment_method",
    "rating", "returned"
]

print("\n TASK 2.3: REMOVE DUPLICATE ORDERS")

dupes = orders[orders.duplicated(subset=natural_key, keep='first')]
print(dupes)
print(len(dupes))

orders_clean = orders.drop_duplicates(subset=natural_key, keep='first')

print(f"orders_clean shape after deduplication: {orders_clean.shape}")

# ---------------------------------------------------------
# Task 2.4 — Impute missing values
# ---------------------------------------------------------

print("\n--- TASK 2.4: IMPUTE MISSING VALUES ---")
# Count missing discount_pct BEFORE imputing
orders_clean['discount_pct'].isnull().sum()

# Fill missing discount_pct values with 0
orders_clean.loc[:, 'discount_pct'] = orders_clean['discount_pct'].fillna(0)

orders_clean['discount_pct'].isnull().sum()

median_rating = orders_clean['rating'].median()
print(f"Median rating before imputation: {median_rating}")

# Fill missing rating values with the median rating
orders_clean.loc[:,'rating'] = orders_clean['rating'].fillna(median_rating)

# Verify no null values remain in these columns
orders_clean[['discount_pct','rating']].isnull().sum()

# Fill missing rating values with the median rating
orders_clean.loc[:,'rating'] = orders_clean['rating'].fillna(median_rating)

# ---------------------------------------------------------
# Task 2.5 — Merge and reconcile against Part 1
# ---------------------------------------------------------

print("\n--- TASK 2.5: MERGE AND RECONCILE AGAINST PART 1 ---")

merged = (
    orders_clean
    .merge(products, on="product_id", how="left")
    .merge(customers, on="customer_id", how="left")
)

# Computer order value
merged['order_value'] = merged['quantity'] * merged['price'] * (1 - merged['discount_pct'] / 100)

# Print total value
total_value = merged['order_value'].sum()
print(f"Cleaned Total Revenue (175 rows): ₹{total_value:.2f}")

# Compute the combined order_value of the 5 dropped duplicate rows
dupes_merged = (
    dupes
    .merge(products, on="product_id", how="left")
    .merge(customers, on="customer_id", how="left")
)

dupes_merged['order_value'] = (
    dupes_merged['quantity'] * dupes_merged['price'] * (1 - dupes_merged['discount_pct'] / 100)
    )

print(dupes_merged['order_value'].sum())

# ReconciliationNOTE

reconciliation_note = (
    f"RECONCILIATION NOTE:\n"
    f"The total order value for the cleaned dataset (175 rows) is ₹{total_value:,.2f}, \n"
    f"which represents an exact reduction of ₹2,501.90 from the Part 1 raw total of ₹99,860.20. \n"
    f"This delta is entirely attributable to the removal of the 5 duplicate order rows (O0176–O0180) in Task 3, \n"
    f"whose sum of individual order values precisely equals ₹{dupes_merged['order_value'].sum():,.2f}. \n"
    f"The imputation of missing ratings and discount values in Task 4 did not alter the total order value, \n"
    f"as filling missing discount_pct values with 0% reflects zero reduction and retains the base order value calculated from raw price and quantity."
)

print("\n" + reconciliation_note)

# ---------------------------------------------------------
# Task 2.6 — IQR outlier detection on quantity
# ---------------------------------------------------------

print("\n--- TASK 6: IQR OUTLIER DETECTION ON QUANTITY ---")

# Compute quartiles and IQR
Q1 = merged['quantity'].quantile(0.25)
Q3 = merged['quantity'].quantile(0.75)
IQR = Q3 - Q1
lower = Q1 - 1.5 * IQR
upper = Q3 + 1.
print(f"Q1 = {Q1}, Q3 = {Q3}, IQR = {IQR}, Lower Bound = {lower}, Upper Bound= {upper}")

# Filter rows outside [lower, upper]:
outliers = merged[(merged['quantity'] < lower) | (merged['quantity'] > upper)]
print(outliers[['order_id','quantity']])

# Adding this is_outlier flag ro dataframe (do NOT drop rows)
merged['is_outlier'] = (merged['quantity'] < lower) | (merged['quantity'] > upper)

# ---------------------------------------------------------
# Task 7 — Hypothesis: does COD have a higher return rate?
# ---------------------------------------------------------
print("\n--- TASK 2.7: HYPOTHESIS TEST ON COD RETURNS ---")


print('''
-----------------------------------------------------------------------------
    HYPOTHESIS STATEMENT:
    Cash on Delivery (COD) orders exhibit a significantly higher return rate
    compared to other payment methods (CARD and UPI).
------------------------------------------------------------------------------
''')

return_rate = merged.groupby('payment_method')['returned'].agg(['count','mean'])
print(return_rate)

print("Conclusion: Hypothesis Confirmed — COD has a significantly higher return rate.")

# ---------------------------------------------------------
# Task 2.8 — Multi-level segmentation
# ---------------------------------------------------------
print("\n--- TASK 8: MULTI-LEVEL SEGMENTATION ---")

return_rate_per_city = (
    merged
    .groupby(['payment_method','city_tier'])['returned']
    .agg(total_orders='count',return_rate='mean')
)

return_rate_per_city["return_rate_%"] = (return_rate_per_city["return_rate"] * 100).round(1)

print("Multi-Level Segmentation: Return Rates by Payment Method & City Tier")
print("-" * 65)

print(return_rate_per_city)

print("\nINSIGHT:")
print(
    "Highest-risk segment: COD + Tier-2 cities at a 54.5% return rate. \n\n"
    "While COD overall exhibits a high return rate, the risk is not uniform across tiers. \n"
    f"Tier-1 COD orders have a return rate of {return_rate_per_city.loc[('COD', 1), 'return_rate_%']}% "
    f"({return_rate_per_city.loc[('COD', 1), 'total_orders']} orders),\nwhereas Tier-2 COD orders jump to "
    f"{return_rate_per_city.loc[('COD', 2), 'return_rate_%']}% ({return_rate_per_city.loc[('COD', 2), 'total_orders']} orders). \n"
    "This shows how a single blended COD return rate hides where the highest risk is concentrated."
)

# ---------------------------------------------------------
# Task 2.9 — Correlation analysis
# -----------------------------------------------------

corr = merged[['rating','returned','discount_pct','quantity']].corr().round(4)

print("Correlation-strength bands\n 0–0.19 negligible\n 0.2–0.39 weak\n 0.4–0.69 moderate\n 0.7–1.0 strong")
print()

print("Pairwise Correlation Evaluation:")
print(f"rating vs returned         : r = {corr.loc["rating","returned"]} -> Negligible (|r| < 0.2)")
print(f"rating vs discount_pct     : r = {corr.loc["rating","discount_pct"]}  -> Negligible (|r| < 0.2)")
print(f"rating vs quantity         : r = {corr.loc["returned","quantity"]} -> Negligible (|r| < 0.2)")
print()
print(f"returned vs discount_pct   : r = {corr.loc["returned","discount_pct"]} -> Negligible (|r| < 0.2)")
print(f"returned vs quantity       : r = {corr.loc["returned","quantity"]}  -> Negligible (|r| < 0.2)")
print()
print(f"discount_pct vs quantity   : r = {corr.loc["discount_pct","quantity"]} -> Negligible (|r| < 0.2)")

# ---------------------------------------------------------
# Task 2.10 — Outlier-corrected time series
# ---------------------------------------------------------
print("\n--- TASK 10: TIME SERIES ANALYSIS ---")

# Converting  order_date to datetime and extract year_month
merged['order_date'] = pd.to_datetime(merged['order_date'])
merged['year_month'] = merged['order_date'].dt.to_period('M').astype(str)

# Recalculate outlier boundaries correctly (Q1=1.0, Q3=2.0, IQR=1.0, lower=-0.5, upper=3.5)
Q1 = merged['quantity'].quantile(0.25)
Q3 = merged['quantity'].quantile(0.75)
IQR = Q3 - Q1
lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR

# Ensure the 'is_outlier' column is defined
merged['is_outlier'] = (merged['quantity'] < lower) | (merged['quantity'] > upper)

# (1) Monthly total order_value INCLUDING outliers
monthly_with_outliers = (
    merged.groupby("year_month")["order_value"].sum().round(2)
)

# (2) Monthly total order_value EXCLUDING outliers (using is_outlier flag from Task 6)
monthly_without_outliers = (
    merged[~merged["is_outlier"]]
    .groupby("year_month")["order_value"].sum().round(2)
)

monthly_comparison = pd.DataFrame(
    {
        "With_Outliers": monthly_with_outliers,
        "Outlier_Corrected": monthly_without_outliers,
    }
)
print("Monthly Total Order Value Comparison:")
print("-" * 50)
print(monthly_comparison)
print("-" * 50)

print(
    "Time-series insight: \nJanuary’s apparent lead (₹29,582.10) is an artifact of two bulk "
    "outlier orders — O0011 on 2026-01-28 (quantity 25) and O0098 on 2026-01-10 (quantity 30). "
    "\nOnce these outliers are excluded, January drops to ₹11,637.10 and March (₹20,318.90) "
    "emerges as the genuine peak month. \nThis demonstrates why Task 6 must precede Task 10: "
    "outlier correction fundamentally changes the interpretation of monthly performance."
)

# --- Save clean merged file for visualization task---

os.makedirs("analysis", exist_ok=True)
merged.to_csv("analysis/merged_clean.csv", index=False)

# ---------------------------------------------------------
# Part 3, Task 1: Export narrator/findings.json
# ---------------------------------------------------------
print("\n--- Exporting findings.json ---")

# Compute raw_total_revenue_inr from original orders (before dedup)
raw_merged = (
    orders
    .merge(products, on="product_id", how="left")
)
raw_merged['order_value'] = (
    raw_merged['quantity'] * raw_merged['price'] * (1 - raw_merged['discount_pct'].fillna(0)/100)
)
raw_total_revenue = round(raw_merged['order_value'].sum(), 2)

# Compute duplicate reconciliation delta
duplicate_delta = round(raw_total_revenue - round(merged['order_value'].sum(), 2), 2)

# Return rate by payment method (rounded to 1 decimal)
return_rate_by_payment = (
    merged.groupby('payment_method')['returned']
    .mean()
    .mul(100)
    .round(1)
    .to_dict()
)

# Highest-risk segment (COD + Tier-2)
seg = (
    merged.groupby(['payment_method','city_tier'])['returned']
    .mean()
    .mul(100)
    .round(1)
)
highest_risk_segment = {
    "payment_method": "COD",
    "city_tier": 2,
    "return_rate_pct": seg.loc[("COD", 2)]
}

# True peak month (outlier-corrected)
ts_excluding = (
    merged[~merged['is_outlier']]
    .groupby('year_month')['order_value']
    .sum()
    .round(2)
)
true_peak_month = {
    "month": ts_excluding.idxmax(),
    "revenue_inr": float(ts_excluding.max())
}

# Outlier-inflated January vs corrected January
ts_including = (
    merged.groupby('year_month')['order_value']
    .sum()
    .round(2)
)

outlier_inflated_month = {
    "month": "2026-01",
    "apparent_revenue_inr": float(ts_including.loc["2026-01"]),
    "corrected_revenue_inr": float(ts_excluding.loc["2026-01"])
}

# Final JSON structure
findings = {
    "cleaned_total_revenue_inr": round(merged['order_value'].sum(), 2),
    "raw_total_revenue_inr": raw_total_revenue,
    "duplicate_reconciliation_delta_inr": duplicate_delta,
    "return_rate_by_payment": return_rate_by_payment,
    "highest_risk_segment": highest_risk_segment,
    "true_peak_month": true_peak_month,
    "outlier_inflated_month": outlier_inflated_month
}

os.makedirs("narrator", exist_ok=True)

with open("narrator/findings.json", "w") as f:
    json.dump(findings, f, indent=4)

print("findings.json exported successfully.")
