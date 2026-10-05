# ---------------------------------------------------------
# Part 2, Task 11: Two visualizations 
# File : analysis/visualize.py
# ---------------------------------------------------------


import pandas as pd
import matplotlib.pyplot as plt
import os

merged = pd.read_csv("analysis/merged_clean.csv")


# --- Visualization 1: Return rate by payment method ---
os.makedirs("visualizations", exist_ok=True)

return_stats = merged.groupby('payment_method')['returned'].mean().sort_values(ascending=False)

plt.figure(figsize=(8,6))
bars = plt.bar(return_stats.index, return_stats.values, color=['red','orange','green'])

# Label exact percentages
for bar, val in zip(bars, return_stats.values):
    plt.text(
        bar.get_x() + bar.get_width()/2,
        bar.get_height(),
        f"{val*100:.1f}%",
        ha='center', va='bottom', fontsize=12
    )

plt.title("COD Returns at 44.4% — 3x Card", fontsize=14)
plt.ylabel("Return Rate")
plt.savefig("visualizations/return_rate_by_payment.png", dpi=300)
plt.close()


# --- Visualization 2: Outlier-corrected monthly revenue ---
ts_excluding = (
    merged[~merged['is_outlier']]
    .groupby('year_month')['order_value'].sum()
)

plt.figure(figsize=(10,6))
plt.plot(ts_excluding.index, ts_excluding.values, marker='o', linewidth=2)

plt.title("Monthly Revenue Trend — March is the True Peak Month", fontsize=14)
plt.xlabel("Month")
plt.ylabel("Revenue (₹)")
plt.grid(True)

plt.savefig("visualizations/monthly_revenue_trend.png", dpi=300)
plt.close()
print("Visualizations successfully created in 'visualizations/' directory")
