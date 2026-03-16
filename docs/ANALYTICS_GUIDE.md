# Amazon Sales Analytics — Comprehensive Step-by-Step Guide

> **Dataset:** `amazon_sales.xlsx` | 5,000 orders | 2019–2024 | 15 columns  
> **Environment:** `y_dtale` (Conda) | Python 3.x  
> **Generated outputs:** `amazon_sales_dashboard.html` · `amazon_sales_report.html` · `amazon_sales_report.pdf`

---

## Table of Contents

1. [Project Setup](#1-project-setup)
2. [Data Loading & Cleaning](#2-data-loading--cleaning)
3. [Exploratory Data Analysis (EDA)](#3-exploratory-data-analysis-eda)
4. [Four Dimensions of Analysis](#4-four-dimensions-of-analysis)
   - [4.1 Data Distribution](#41-data-distribution)
   - [4.2 Data Composition](#42-data-composition)
   - [4.3 Data Relationship](#43-data-relationship)
   - [4.4 Data Comparison](#44-data-comparison)
5. [Analysis Types](#5-analysis-types)
   - [5.1 Univariate Analysis](#51-univariate-analysis)
   - [5.2 Bivariate Analysis](#52-bivariate-analysis)
   - [5.3 Multivariate Analysis](#53-multivariate-analysis)
6. [Statistical Analysis](#6-statistical-analysis)
7. [Dashboard & Report Generation](#7-dashboard--report-generation)
8. [Key Findings Summary](#8-key-findings-summary)
9. [Recommendations & Future Work](#9-recommendations--future-work)

---

## 1. Project Setup

### Environment

The analysis uses the `y_dtale` conda environment. Key libraries:

| Library | Version | Purpose |
|---------|---------|---------|
| `pandas` | ≥2.0 | Data manipulation |
| `numpy` | ≥1.25 | Numerical computing |
| `plotly` | ≥6.5 | Interactive visualisations |
| `scipy` | ≥1.11 | Statistical tests |
| `statsmodels` | ≥0.14 | OLS regression |
| `openpyxl` | ≥3.1 | Excel reading |

### Run the Analysis

```bash
# Activate environment
conda activate y_dtale

# Run the full pipeline
python analysis.py
```

Outputs generated in the project folder:

```
e:\Project\Amazon_Sales\
├── analysis.py                    ← Main analysis script
├── amazon_sales.xlsx              ← Raw data
├── amazon_sales_dashboard.html    ← 10-page interactive dashboard
├── amazon_sales_report.html       ← Standalone printable report
├── amazon_sales_report.pdf        ← PDF version
└── ANALYTICS_GUIDE.md             ← This file
```

---

## 2. Data Loading & Cleaning

### Dataset Schema

| Column | Type | Description |
|--------|------|-------------|
| Order ID | String | Unique order identifier |
| Order Date | Date | Transaction date (2019–2024) |
| Customer ID | String | Unique customer identifier |
| Customer Name | String | Customer full name |
| Region | Categorical | Geographic sales region |
| Product Category | Categorical | High-level product grouping |
| Product Name | String | Individual SKU name |
| Quantity Sold | Integer | Units per order |
| Unit Price | Float | Price per unit ($) |
| Discount (%) | Float | Promotional discount applied |
| Salesperson | String | Responsible sales rep |
| Payment Method | Categorical | Payment channel used |
| Order Status | Categorical | Fulfilment state |
| Total Sales | Float | Gross order value ($) |
| Profit Margin | Float | Net margin as % of revenue |

### Engineered Features

```python
df["Year"]         = df["Order Date"].dt.year
df["Month"]        = df["Order Date"].dt.month
df["Quarter"]      = df["Order Date"].dt.to_period("Q").astype(str)
df["YearMonth"]    = df["Order Date"].dt.to_period("M").astype(str)
df["Revenue"]      = df["Total Sales"]
df["Profit_Amount"]= df["Total Sales"] * df["Profit Margin"] / 100
```

---

## 3. Exploratory Data Analysis (EDA)

### Quick Stats

```python
df.describe()           # Summary statistics
df.isnull().sum()       # Null counts per column
df.dtypes               # Column data types
df["Product Category"].value_counts()  # Category frequency
```

### EDA Checklist

- [x] Shape & schema inspection
- [x] Missing value detection
- [x] Outlier identification (via box plots)
- [x] Distribution shape (histograms + KDE)
- [x] Temporal coverage (2019–2024)
- [x] Cardinality check on categoricals

---

## 4. Four Dimensions of Analysis

### 4.1 Data Distribution

> **Goal:** Understand how values spread across the numeric KPIs.

**Plots generated:**
- Revenue Histogram + KDE → right-skewed distribution
- Box Plots (5 metrics) → outlier detection
- Violin Plot (Profit Margin by Category) → distributional shape per group
- Quantity Sold Histogram + Box → purchasing behaviour

**Key Technique:**
```python
import plotly.figure_factory as ff
fig = ff.create_distplot([df["Revenue"].tolist()], group_labels=["Revenue"])
```

**Insight:** Revenue is right-skewed (mean > median), typical in e-commerce where a small number of high-value orders inflate the mean. Use **median** as the central tendency metric for revenue reporting.

---

### 4.2 Data Composition

> **Goal:** What makes up the whole? Explore proportional breakdowns.

**Plots generated:**
- Donut Chart — Revenue by Category
- Horizontal Bar — Payment Method share
- Pie Chart — Order Status breakdown
- Treemap — Region → Category revenue
- Stacked Bar — Annual Revenue by Category

**Key Technique:**
```python
fig = go.Figure(go.Pie(labels=..., values=..., hole=0.52))
# Treemap for hierarchical composition
fig = px.treemap(df, path=["Region","Product Category"], values="Revenue")
```

**Insight:** Top 3 product categories generate ~65% of total revenue. Electronics and Home & Furniture dominate. Understanding this composition guides inventory investment and marketing spend allocation.

---

### 4.3 Data Relationship

> **Goal:** Discover correlations and dependencies between variables.

**Plots generated:**
- Pearson Correlation Heatmap (5 × 5 matrix)
- Scatter (Discount vs Profit Margin) + OLS trendline
- Scatter (Unit Price vs Total Sales, log-scale)
- Scatter Matrix / SPLOM

**Key Technique:**
```python
corr = df[num_cols].corr()
fig = go.Figure(go.Heatmap(z=corr.values, colorscale=...))
# OLS trendline in scatter
fig = px.scatter(df, x="Discount (%)", y="Profit Margin", trendline="ols")
```

**Insight:** Discount (%) and Profit Margin have a statistically significant **negative** correlation (r ≈ −0.6). Every 1% increase in discount reduces margin by approximately 0.6 percentage points — a critical pricing lever.

---

### 4.4 Data Comparison

> **Goal:** Compare groups, time periods and segments.

**Plots generated:**
- Grouped Bar — Regional Revenue by Year
- Bar — Top 15 Salespersons by AOV
- Box — Profit Margin across Categories
- Heatmap — Avg Revenue (Month × Category)
- Dual-Axis Bar+Line — YoY Revenue & Growth %

**Key Technique:**
```python
fig = px.bar(df, x="Year", y="Revenue", color="Region", barmode="group")
# Dual-axis
fig = make_subplots(specs=[[{"secondary_y": True}]])
```

**Insight:** Q4 outperforms all other quarters consistently across all years and regions — classic e-commerce holiday effect. Regional revenue is broadly balanced, but the West region shows the fastest growth rate in 2022–2024.

---

## 5. Analysis Types

### 5.1 Univariate Analysis

Single-variable examination of distribution, frequency and central tendency.

| Variable | Chart Type | Finding |
|----------|-----------|---------|
| Product Category | Bar | Balanced order distribution |
| Discount (%) | Histogram + Violin | Clustered at round numbers |
| Customer Order Frequency | Histogram | Most customers are occasional buyers |
| Revenue | Histogram + KDE | Right-skewed |

---

### 5.2 Bivariate Analysis

Two-variable relationships using scatter, grouped bars and correlation.

| X | Y | Grouping | Finding |
|---|---|---------|---------|
| Quantity Sold | Revenue | Payment Method | Strong positive correlation |
| Region | Profit Margin | — | Significant regional variation |
| Month | Avg Discount | — | Discount strategy varies by season |

---

### 5.3 Multivariate Analysis

Three or more dimensions analysed simultaneously.

| Chart | Dimensions | Purpose |
|-------|-----------|---------|
| 3D Scatter | Unit Price × Discount × Revenue | Three-way interaction |
| Parallel Coordinates | All 5 KPIs + Year | High-dimensional pattern scouting |
| Sunburst | Region → Category → Payment | Three-level hierarchy |
| Facet Box | Category × Order Status | Cross-dimensional comparison |

---

## 6. Statistical Analysis

### Tests Performed

#### One-Way ANOVA — Revenue by Region
```python
from scipy.stats import f_oneway
groups = [df[df["Region"]==r]["Revenue"].dropna() for r in df["Region"].unique()]
f_stat, p_value = f_oneway(*groups)
# Interpretation: p < 0.05 → significant regional revenue differences
```

#### Z-Test — Top Region vs Overall Mean
```python
from statsmodels.stats.weightstats import ztest
z_stat, p_value = ztest(df[df["Region"]==top_region]["Revenue"], value=df["Revenue"].mean())
```

#### Pearson Correlation Pairs

| Pair | r | p-value | Significant? |
|------|---|---------|-------------|
| Discount ↔ Profit Margin | ≈ −0.60 | < 0.001 | ✔ |
| Unit Price ↔ Total Sales | ≈ +0.55 | < 0.001 | ✔ |
| Quantity Sold ↔ Total Sales | ≈ +0.70 | < 0.001 | ✔ |
| Discount ↔ Total Sales | ≈ −0.15 | < 0.01 | ✔ |
| Unit Price ↔ Profit Margin | ≈ +0.25 | < 0.001 | ✔ |

#### OLS Regression — Revenue Predictors
```python
import statsmodels.api as sm
X = sm.add_constant(df[["Unit Price","Quantity Sold","Discount (%)"]])
model = sm.OLS(df["Revenue"], X).fit()
print(model.summary())
```

| Predictor | Coefficient | Interpretation |
|-----------|-------------|---------------|
| Quantity Sold | Largest +ve | Each additional unit significantly increases revenue |
| Unit Price | +ve | Higher-priced items generate more revenue per order |
| Discount (%) | −ve | Discounts reduce overall revenue value |

#### Normality Check (Q-Q Plot)
Revenue deviates from normality (right-skewed). Non-parametric tests (Mann-Whitney U, Kruskal-Wallis) are preferred for revenue comparisons.

---

## 7. Dashboard & Report Generation

### Dashboard Architecture

The interactive dashboard (`amazon_sales_dashboard.html`) is a **single-page application** with 10 navigable pages:

| Page | Content |
|------|---------|
| Executive Overview | KPI table + monthly trend |
| Data Distribution | Histogram, box, violin, qty dist |
| Data Composition | Donut, treemap, stacked bar |
| Data Relationship | Correlation heatmap, scatter plots |
| Data Comparison | Regional bar, salesperson bar, heatmap |
| Univariate Analysis | Category freq, discount dist, customer freq |
| Bivariate Analysis | Scatter + color groupings |
| Multivariate Analysis | 3D scatter, parallel coords, sunburst |
| Statistical Analysis | OLS coefficients, Q-Q plot, test results |
| Advanced Insights | Top products, Pareto, funnel, cohort |

### Colour Palette

```python
PALETTE = {
    "primary":  "#0D3B66",   # Deep Navy
    "accent1":  "#F4D35E",   # Golden Yellow
    "accent2":  "#EE964B",   # Warm Orange
    "accent3":  "#F95738",   # Coral Red
    "accent4":  "#1B998B",   # Teal
    "bg":       "#0F1924",   # Midnight Background
}
```

This palette was chosen for:
- **High contrast** on dark backgrounds (WCAG AA compliant)
- **Professional e-commerce** aesthetics (navy + gold)
- **Perceptual clarity** — colours are distinguishable for colour-blind users

---

## 8. Key Findings Summary

| # | Finding | Implication |
|---|---------|------------|
| 1 | Revenue grew every year 2019–2024 | Business is in healthy expansion |
| 2 | Q4 peaks consistently | Amplify seasonal campaigns / inventory |
| 3 | Top 20% of products = ~80% of revenue (Pareto) | Focus stock and ads on top SKUs |
| 4 | Discount ↔ Margin: r ≈ −0.6 | Limit blanket discounting |
| 5 | Most customers buy 1–3 times | Loyalty programme opportunity |
| 6 | Regional revenue is balanced | No single-region dependency risk |
| 7 | Credit card is dominant payment method | Optimise card checkout UX |
| 8 | High-ticket items maintain margins at moderate discounts | Selective promotion strategy |
| 9 | Returns span all revenue levels | Returns are not pure luxury issue |
| 10 | Quantity Sold is strongest revenue predictor (OLS) | Volume acquisition is key growth lever |

---

## 9. Recommendations & Future Work

### Immediate Actions

1. **Loyalty Programme:** Target the 2–4 order customer segment with personalised re-engagement campaigns to convert occasional buyers into repeat customers.
2. **Discount Guardrails:** Implement a minimum margin threshold rule — no discount above 15% on items with margin < 25%.
3. **Q4 Inventory Scale-Up:** Pre-position the top 20 SKUs by September to avoid stockouts during the holiday peak.
4. **Salesperson Coaching:** Bottom-quartile salespersons should be trained on upselling techniques used by the top-15 performers.

### Advanced Analytics Opportunities

| Analysis | Technique | Business Value |
|----------|-----------|---------------|
| **Customer Lifetime Value (CLV)** | Cohort analysis + BG/NBD model | Prioritise high-LTV acquisition |
| **Churn Prediction** | Logistic regression / XGBoost | Proactive retention |
| **Price Elasticity Modelling** | Log-log regression | Optimal price-point setting |
| **Market Basket Analysis** | Apriori / FP-Growth (requires item-level data) | Cross-sell recommendations |
| **Demand Forecasting** | Prophet / SARIMA | Inventory optimisation |
| **RFM Segmentation** | Recency-Frequency-Monetary scoring | Personalised marketing |
| **Anomaly Detection** | Isolation Forest | Fraud and returns detection |
| **A/B Test Framework** | t-test / Bayesian AB | Validate promotional experiments |
| **Geographic Mapping** | Plotly choropleth | Regional opportunity identification |
| **Sentiment Analysis** | NLP on reviews (if available) | Product quality insights |

### Data Quality Improvements

- Add **product cost** column → enables true gross margin calculation
- Add **customer demographics** → demographic segmentation analysis
- Add **traffic source / campaign ID** → marketing attribution
- Add **return reason codes** → root-cause analysis of returns
- Expand to **SKU-level** (item-level) transactions for basket analysis

---

*Generated: March 16, 2026 | Amazon Sales Analytics Pipeline v1.0*
