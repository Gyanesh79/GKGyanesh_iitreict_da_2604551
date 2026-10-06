# Mamaearth Returns & Growth Intelligence Pipeline

**Program:** Data Analytics with AI & Gen AI · E&ICT Academy IIT Roorkee  
**Capstone Project**

This repository implements all three layers required by the capstone brief:

1. **SQL relational/reporting layer** — SQLite schema, seed data, and reports.
2. **Python/Pandas analysis layer** — cleaning, EDA, outlier analysis, hypothesis checks, reconciliation, and visualizations.
3. **GenAI insight narrator** — Gemini-powered SCR narrative with a fully offline/keyless fallback.

The pipeline is deliberately connected while keeping Part 1 and Part 2 independent:

- SQL reads the raw CSV seed data.
- Python reads the same raw CSV files directly, independently of SQL.
- `analysis/clean_and_eda.py` computes the verified Part 2 figures and writes `narrator/findings.json`.
- `narrator/generate_narrative.py` reads only `findings.json` and turns those verified values into the SCR narrative.
- The narrator never uses raw CSVs and never invents business statistics.

> **Source-data rule:** the CSVs under `data/` are the exact seed data supplied with the capstone brief. They must not be manually edited. All cleaning is performed in Python.

---

## Repository structure

```text
Mamaearth_Returns_Growth_Intelligence_Pipeline/
├── README.md
├── requirements.txt
├── sql/
│   ├── schema.sql
│   ├── seed_data.sql
│   └── reports.sql
├── data/
│   ├── customers.csv
│   ├── products.csv
│   └── orders.csv
├── analysis/
│   ├── clean_and_eda.py
│   ├── visualize.py
|   └── merged_clean.csv
├── visualizations/
│   ├── return_rate_by_payment.png
│   └── monthly_revenue_trend.png
└── narrator/
    ├── findings.json
    ├── generate_narrative.py
    └── sample_output.txt
```

---

# 1. Prerequisites

Python 3.10+ is recommended.

Install the Python dependencies:

```bash
python -m pip install -r requirements.txt
```

The SQL layer uses **SQLite**, so no server/database account is required.

For the optional Gemini online path, obtain a free Gemini API key from Google AI Studio and set it as an environment variable. The project also works with **no API key and no network access** by using the deterministic offline fallback.

---

# 2. Exact pipeline order

Run the project in this order:

```
1. SQL schema + seed data
        ↓
2. SQL reports
        ↓
3. Python clean_and_eda.py
        ↓
   narrator/findings.json
        ↓
4. Python visualize.py
        ↓
   visualizations/*.png
        ↓
5. Python generate_narrative.py
        ↓
   narrator/sample_output.txt
```

Part 1 and Part 2 are intentionally independent: Part 2 reads the raw CSVs directly, not the SQLite database.

---

# Part 1 — SQL Relational Layer & Reporting

## Task 1 — Schema

`sql/schema.sql` creates:

- `customers`
- `products`
- `orders`

The `orders` table keeps `discount_pct` and `rating` nullable because the brief explicitly treats their missing values as genuine NULLs.

Run:

```bash
sqlite3 mamaearth.db < sql/schema.sql
```

On Windows PowerShell, the same command works when `sqlite3.exe` is on PATH.

---

## Task 2 — Load seed data

`sql/seed_data.sql` contains INSERT statements generated from the exact CSV seed data.

Run:

```bash
sqlite3 mamaearth.db < sql/seed_data.sql
```

Verify:

```sql
SELECT COUNT(*) FROM customers;
SELECT COUNT(*) FROM products;
SELECT COUNT(*) FROM orders;
```

Expected:

```text
45
16
180
```

The seed SQL inserts blank `discount_pct` and `rating` cells as SQL `NULL`, so no `.import` cleanup is required.

---

## Task 3 — Reports

Run:

```bash
sqlite3 mamaearth.db < sql/reports.sql
```

Or open the database in DB Browser for SQLite and execute `sql/reports.sql`.

The report file contains:

- (a) order totals
- (b) `COUNT(*)` vs `COUNT(rating)`
- (c) LEFT JOIN zero-order customer + independent `NOT IN` check
- (d) city return-rate grouping with `HAVING`
- (e) customer ranking with `LIMIT` and `OFFSET`
- (f) three-table category revenue join
- (g) `LIKE 'A%'`
- (h) `DISTINCT` acquisition sources
- (i) `ALTER TABLE` + `UPDATE ... CASE`

### Important

`reports.sql` adds `loyalty_tier` to `customers`. If you want to run the entire SQL layer again from a clean state, rerun:

```bash
sqlite3 mamaearth.db < sql/schema.sql
sqlite3 mamaearth.db < sql/seed_data.sql
sqlite3 mamaearth.db < sql/reports.sql
```

The schema script drops and recreates the three tables so the complete SQL layer is repeatable.

---

# Part 2 — Python/Pandas Data Wrangling & EDA

Run from the repository root:

```bash
python analysis/clean_and_eda.py
```

The script is independent of SQLite and reads:

```text
data/orders.csv
data/customers.csv
data/products.csv
```

## Task coverage

### Task 1
Loads all three CSV files and prints the raw orders shape:

```text
(180, 9)
```

### Task 2
Standardizes payment methods using:

```python
.str.strip().str.upper()
```

Expected cleaned counts:

```text
CARD    70
COD     55
UPI     55
```

### Task 3
Detects duplicates using the natural key excluding `order_id`.

Expected duplicate IDs:

```text
O0176
O0177
O0178
O0179
O0180
```

Expected cleaned shape:

```text
(175, 9)
```

### Task 4
- Missing `discount_pct` → `0`
- Missing `rating` → median of the deduplicated frame
- Median rating → `3.0`

After imputation:

```text
discount_pct    0
rating          0
```

### Task 5
Merges orders with products and customers and calculates:

```text
order_value = quantity × price × (1 - discount_pct / 100)
```

Expected cleaned revenue:

```text
₹97,358.30
```

The script also independently calculates the value of the five dropped duplicate rows:

```text
₹2,501.90
```

and prints the required reconciliation explaining why:

```text
₹99,860.20 raw SQL revenue
- ₹2,501.90 duplicate revenue
= ₹97,358.30 cleaned revenue
```

Missing-value imputation does not alter `order_value`.

### Task 6
IQR outlier detection is performed on `quantity`.

Expected:

```text
Q1       = 1.0
Q3       = 2.0
IQR      = 1.0
Lower    = -0.5
Upper    = 3.5
```

Flagged but **not removed**:

```text
O0011 → quantity 25
O0098 → quantity 30
```

### Task 7
The script explicitly tests:

> Hypothesis: COD has a higher return rate.

Expected rates:

```text
CARD    14.7%
COD     44.4%
UPI     18.9%
```

The script labels the hypothesis:

```text
Confirmed
```

### Task 8
The script performs payment-method × city-tier segmentation.

Expected highest-risk segment:

```text
COD + Tier-2
Return rate = 54.5%
```

### Task 9
The script calculates correlations across:

```text
rating
returned
discount_pct
quantity
```

It labels every pair using the taught bands:

```text
negligible: |r| < 0.2
weak:       0.2 ≤ |r| < 0.4
moderate:   0.4 ≤ |r| < 0.7
strong:     0.7 ≤ |r| ≤ 1.0
```

All six pairwise relationships are expected to be negligible.

The discount-vs-return hypothesis is explicitly printed as:

```text
Busted
```

with correlation approximately:

```text
-0.09
```

### Task 10
The script prints monthly revenue both:

1. including quantity outliers
2. excluding quantity outliers

The corrected series is:

```text
2026-01    11637.10
2026-02    13195.50
2026-03    20318.90
2026-04     9495.30
2026-05    13151.10
2026-06    11615.40
```

The script explicitly explains that January's apparent lead is caused by O0011 and O0098, and that March is the genuine corrected peak.

### Part 3 hand-off

At the end of `clean_and_eda.py`, the script writes:

```text
narrator/findings.json
```

This is generated from the values actually calculated by the analysis pipeline; it is not hand-typed.

---

# Part 2 — Task 11: Visualizations

Run:

```bash
python analysis/visualize.py
```

This creates:

```text
visualizations/return_rate_by_payment.png
visualizations/monthly_revenue_trend.png
```

The first chart shows cleaned return rate by payment method in descending order and labels each bar with its percentage.

The second chart uses the **outlier-corrected** monthly revenue and identifies March 2026 as the true peak.

Both scripts are re-runnable from the raw CSV files.

---

# Part 3 — GenAI-Powered Insight Narrator

## Task 1 — findings.json

Do not manually edit `narrator/findings.json`.

Generate it with:

```bash
python analysis/clean_and_eda.py
```

It contains the required verified figures:

```json
{
  "cleaned_total_revenue_inr": 97358.30,
  "raw_total_revenue_inr": 99860.20,
  "duplicate_reconciliation_delta_inr": 2501.90,
  "return_rate_by_payment": {
    "COD": 44.4,
    "CARD": 14.7,
    "UPI": 18.9
  },
  "highest_risk_segment": {
    "payment_method": "COD",
    "city_tier": 2,
    "return_rate_pct": 54.5
  },
  "true_peak_month": {
    "month": "2026-03",
    "revenue_inr": 20318.90
  },
  "outlier_inflated_month": {
    "month": "2026-01",
    "apparent_revenue_inr": 29582.10,
    "corrected_revenue_inr": 11637.10
  }
}
```

---

## Task 2–4 — Gemini + offline fallback

The narrator uses:

```python
from google import genai
```

The Gemini call:

- uses a separate system instruction
- fixes the role as a senior data analyst
- requires Situation / Complication / Resolution
- receives numbers through the `findings` argument
- uses `temperature=0.0`
- uses explicit `max_output_tokens=600`
- uses a 10-second HTTP timeout
- catches API errors
- falls back to a deterministic offline template

### Option A — Gemini online path

Set a Gemini API key.

**Windows PowerShell:**

```powershell
$env:GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
python narrator/generate_narrative.py
```

**Windows CMD:**

```cmd
set GEMINI_API_KEY=YOUR_GEMINI_API_KEY
python narrator/generate_narrative.py
```

**macOS/Linux:**

```bash
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
python narrator/generate_narrative.py
```

You can optionally choose a model:

```bash
set GEMINI_MODEL=gemini-2.5-flash
```

The script accepts the legacy-style environment variable `GenAI_APIKey` too, but `GEMINI_API_KEY` is the recommended name.

### Option B — fully offline/keyless path

Do nothing.

Simply run:

```bash
python narrator/generate_narrative.py
```

If no API key is present, the script automatically uses:

```python
generate_scr_narrative_offline(findings)
```

No network request and no paid API quota are required.

If a key exists but the Gemini call fails, the same offline fallback is used.

---

# Task 5 — Numeric accuracy checker

The narrator checks that the generated narrative contains all required figures:

```text
97,358.30
44.4
54.5
2,501.90
March + 20,318.90
```

The checker normalizes commas before matching.

The exact generated narrative is saved to:

```text
narrator/sample_output.txt
```

Therefore, the saved sample can be inspected independently of a future live API call.

---

# Expected key results

| Check | Expected result |
|---|---:|
| Raw orders | 180 |
| Cleaned orders | 175 |
| Raw SQL revenue | ₹99,860.20 |
| Cleaned revenue | ₹97,358.30 |
| Duplicate reconciliation delta | ₹2,501.90 |
| CARD return rate | 14.7% |
| COD return rate | 44.4% |
| UPI return rate | 18.9% |
| Highest-risk segment | COD + Tier-2 |
| Highest-risk return rate | 54.5% |
| Apparent January revenue | ₹29,582.10 |
| Corrected January revenue | ₹11,637.10 |
| True peak month | March 2026 |
| True peak revenue | ₹20,318.90 |

---
