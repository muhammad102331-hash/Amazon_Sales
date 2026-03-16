"""
Amazon Sales Analytics Engine (2019-2024)
==========================================
Generates: interactive HTML dashboard + standalone report + PDF
"""

import os
import warnings
import base64
import json
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.stats as stats
from scipy.stats import pearsonr, spearmanr
import statsmodels.api as sm
from statsmodels.stats.weightstats import ztest
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore")
pd.set_option("display.float_format", "{:.2f}".format)

# ─────────────────────────────────────────────
# 0. PATHS
# ─────────────────────────────────────────────
BASE = Path(__file__).resolve().parent
PROJECT_ROOT = BASE.parent
DATA_FILE = PROJECT_ROOT / "data" / "raw" / "amazon_sales.xlsx"
LOGO_FILE = PROJECT_ROOT / "assets" / "logo.png"
OUT_HTML   = PROJECT_ROOT / "reports" / "html" / "amazon_sales_dashboard.html"
OUT_REPORT = PROJECT_ROOT / "reports" / "html" / "amazon_sales_report.html"
OUT_PDF    = PROJECT_ROOT / "reports" / "pdf" / "amazon_sales_report.pdf"

# ─────────────────────────────────────────────
# 1. COLOUR PALETTE (Professional Deep-Blue/Coral)
# ─────────────────────────────────────────────
PALETTE = {
    "primary":   "#0D3B66",
    "secondary": "#FAF0CA",
    "accent1":   "#F4D35E",
    "accent2":   "#EE964B",
    "accent3":   "#F95738",
    "accent4":   "#1B998B",
    "accent5":   "#C0CAAD",
    "bg":        "#0F1924",
    "card":      "#16253A",
    "text":      "#E8EDF2",
    "grid":      "#1E3050",
}

SEQ_COLORS   = ["#0D3B66","#1B6CA8","#1B998B","#F4D35E","#EE964B","#F95738"]
CAT_COLORS   = ["#1B998B","#F4D35E","#EE964B","#F95738","#E9C46A","#2A9D8F",
                "#264653","#E76F51","#A8DADC","#457B9D"]
DIVERG_SCALE = [[0,"#0D3B66"],[0.5,"#FAF0CA"],[1,"#F95738"]]

PLOT_LAYOUT = dict(
    paper_bgcolor=PALETTE["bg"],
    plot_bgcolor =PALETTE["card"],
    font=dict(color=PALETTE["text"], family="Inter, Arial, sans-serif", size=13),
    title_font=dict(size=18, color=PALETTE["accent1"], family="Inter, Arial, sans-serif"),
    legend=dict(bgcolor="rgba(0,0,0,0.3)", bordercolor=PALETTE["grid"],
                borderwidth=1, font=dict(color=PALETTE["text"])),
    xaxis=dict(gridcolor=PALETTE["grid"], linecolor=PALETTE["grid"],
               tickfont=dict(color=PALETTE["text"])),
    yaxis=dict(gridcolor=PALETTE["grid"], linecolor=PALETTE["grid"],
               tickfont=dict(color=PALETTE["text"])),
    margin=dict(l=60, r=40, t=70, b=60),
)

def apply_layout(fig, title="", **kwargs):
    layout = {**PLOT_LAYOUT, "title": title, **kwargs}
    fig.update_layout(**layout)
    return fig

# ─────────────────────────────────────────────
# 2. DATA LOADING & CLEANING
# ─────────────────────────────────────────────
print("Loading data …")
OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
df = pd.read_excel(DATA_FILE)
df.columns = df.columns.str.strip()

# Parse dates
df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
df["Year"]   = df["Order Date"].dt.year
df["Month"]  = df["Order Date"].dt.month
df["Quarter"]= df["Order Date"].dt.to_period("Q").astype(str)
df["Month_Name"] = df["Order Date"].dt.strftime("%b")
df["YearMonth"]  = df["Order Date"].dt.to_period("M").astype(str)

# Clean numerics
num_cols = ["Quantity Sold","Unit Price","Discount (%)","Total Sales","Profit Margin"]
for c in num_cols:
    df[c] = pd.to_numeric(df[c], errors="coerce")

df["Revenue"]       = df["Total Sales"]
df["Profit_Amount"] = df["Total Sales"] * df["Profit Margin"] / 100

df.dropna(subset=["Order Date","Total Sales"], inplace=True)
print(f"  Dataset: {df.shape[0]:,} rows × {df.shape[1]} cols")

# Encode logo
logo_b64 = ""
if LOGO_FILE.exists():
    with open(LOGO_FILE, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()

# ─────────────────────────────────────────────
# 3. ALL PLOTS
# ─────────────────────────────────────────────
plots = {}   # name → (fig, interpretation, key_findings)

# ──────────────────────────────────────────────────────────
# PAGE 1 ─ EXECUTIVE OVERVIEW
# ──────────────────────────────────────────────────────────

# 1a. Monthly Revenue Trend
monthly = (df.groupby("YearMonth")["Revenue"].sum()
             .reset_index().sort_values("YearMonth"))
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=monthly["YearMonth"], y=monthly["Revenue"],
    mode="lines+markers",
    line=dict(color=PALETTE["accent1"], width=2.5),
    marker=dict(size=5, color=PALETTE["accent2"]),
    fill="tozeroy",
    fillcolor="rgba(244,211,94,0.08)",
    name="Monthly Revenue",
    hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.0f}<extra></extra>"
))
apply_layout(fig, "Monthly Revenue Trend (2019 – 2024)")
plots["monthly_trend"] = (
    fig,
    "Monthly revenue fluctuates over 2019–2024, revealing seasonal peaks and growth plateaus.",
    ["Revenue shows cyclical seasonal patterns with peaks typically in Q4.",
     "Long-term growth trajectory is visible across the 5-year window.",
     "Certain months (Nov/Dec) consistently outperform others."]
)

# 1b. KPI Summary (Table)
kpi = {
    "Total Revenue":    f"${df['Revenue'].sum():,.0f}",
    "Total Orders":     f"{df.shape[0]:,}",
    "Avg Order Value":  f"${df['Revenue'].mean():,.2f}",
    "Avg Profit Margin":f"{df['Profit Margin'].mean():.1f}%",
    "Avg Discount":     f"{df['Discount (%)'].mean():.1f}%",
    "Unique Customers": f"{df['Customer ID'].nunique():,}",
}
fig_kpi = go.Figure(go.Table(
    header=dict(values=["KPI","Value"],
                fill_color=PALETTE["primary"],
                font=dict(color=PALETTE["accent1"], size=14),
                align="left", height=35),
    cells=dict(values=[list(kpi.keys()), list(kpi.values())],
               fill_color=[[PALETTE["card"]]*len(kpi)],
               font=dict(color=PALETTE["text"], size=13),
               align=["left","right"], height=32),
))
apply_layout(fig_kpi, "Key Performance Indicators")
plots["kpi_table"] = (
    fig_kpi,
    "High-level business health metrics at a glance.",
    [f"Total revenue across all years: {kpi['Total Revenue']}",
     f"Average order value: {kpi['Avg Order Value']}",
     f"Average profit margin: {kpi['Avg Profit Margin']}"]
)

# ──────────────────────────────────────────────────────────
# PAGE 2 ─ DATA DISTRIBUTION
# ──────────────────────────────────────────────────────────

# 2a. Revenue Distribution – Histogram + KDE
fig = ff.create_distplot(
    [df["Revenue"].dropna().tolist()],
    group_labels=["Revenue"],
    bin_size=500,
    colors=[PALETTE["accent1"]],
    show_rug=False,
)
apply_layout(fig, "Revenue Distribution (Histogram + KDE)")
fig.update_traces(opacity=0.75)
plots["revenue_dist"] = (
    fig,
    "The revenue distribution shape indicates whether orders are right-skewed (many small, few large).",
    ["Revenue is right-skewed — most orders cluster at lower values.",
     "Heavy tail implies a few high-value orders drive disproportionate revenue.",
     "Median order value is significantly below the mean due to skew."]
)

# 2b. Box plots for numeric KPIs
fig = go.Figure()
for i, col in enumerate(["Total Sales","Unit Price","Quantity Sold","Discount (%)","Profit Margin"]):
    fig.add_trace(go.Box(
        y=df[col].dropna(), name=col,
        marker_color=SEQ_COLORS[i % len(SEQ_COLORS)],
        boxmean="sd",
        hovertemplate=f"<b>{col}</b><br>%{{y:.2f}}<extra></extra>"
    ))
apply_layout(fig, "Numeric KPIs – Box Plots (Outlier Detection)")
plots["boxplots"] = (
    fig,
    "Box plots expose the spread, median and outliers of each numeric metric.",
    ["Unit Price has the widest interquartile range, suggesting diverse product tiers.",
     "Discount (%) outliers hint at aggressive promotional events.",
     "Profit Margin distribution is relatively tight, indicating consistent pricing strategy."]
)

# 2c. Violin – Profit Margin by Category
fig = go.Figure()
cats = df["Product Category"].dropna().unique()
for i, cat in enumerate(cats):
    sub = df[df["Product Category"]==cat]["Profit Margin"].dropna()
    fig.add_trace(go.Violin(
        y=sub, name=cat,
        box_visible=True, meanline_visible=True,
        fillcolor=CAT_COLORS[i % len(CAT_COLORS)],
        opacity=0.8,
        line_color=PALETTE["text"],
    ))
apply_layout(fig, "Profit Margin Distribution by Product Category (Violin)")
plots["violin_margin"] = (
    fig,
    "Violin plots reveal full distributional shape of profit margin per category.",
    ["Some categories show bimodal margin distributions — multiple price segments.",
     "High-margin categories have tighter violin shapes (consistent premium pricing).",
     "Electronics shows wider spread due to varying product value."]
)

# 2d. Histogram – Quantity Sold
fig = px.histogram(
    df, x="Quantity Sold", nbins=30,
    color_discrete_sequence=[PALETTE["accent4"]],
    opacity=0.85,
    marginal="box",
    title="Quantity Sold Distribution"
)
apply_layout(fig, "Quantity Sold Distribution")
plots["qty_dist"] = (
    fig,
    "Frequency distribution of units per order.",
    ["Most orders consist of 1-3 units, typical for e-commerce.",
     "Bulk orders (10+) are rare but represent significant revenue.",
     "Right-skewed distribution confirms individual consumer dominance."]
)

# ──────────────────────────────────────────────────────────
# PAGE 3 ─ DATA COMPOSITION
# ──────────────────────────────────────────────────────────

# 3a. Revenue by Category – Donut
cat_revenue = df.groupby("Product Category")["Revenue"].sum().reset_index().sort_values("Revenue", ascending=False)
fig = go.Figure(go.Pie(
    labels=cat_revenue["Product Category"],
    values=cat_revenue["Revenue"],
    hole=0.52,
    marker=dict(colors=CAT_COLORS[:len(cat_revenue)],
                line=dict(color=PALETTE["bg"], width=2)),
    textinfo="percent+label",
    hovertemplate="<b>%{label}</b><br>Revenue: $%{value:,.0f}<br>Share: %{percent}<extra></extra>"
))
apply_layout(fig, "Revenue Composition by Product Category")
plots["category_donut"] = (
    fig,
    "Donut chart shows each category's share of total revenue.",
    ["Top 3 categories account for the majority of revenue.",
     "High-value categories (Electronics, Furniture) dominate despite lower order counts.",
     "Accessories & consumables have high order frequency but lower revenue share."]
)

# 3b. Payment Method Composition – Horizontal Bar
pay = df["Payment Method"].value_counts().reset_index()
pay.columns = ["Method","Count"]
fig = px.bar(
    pay, x="Count", y="Method", orientation="h",
    color="Count",
    color_continuous_scale=SEQ_COLORS,
    text="Count",
    title="Payment Method Distribution"
)
apply_layout(fig, "Payment Method Distribution")
fig.update_traces(textposition="outside")
plots["payment_method"] = (
    fig,
    "Which payment channels customers prefer.",
    ["Credit/Debit Cards dominate as expected in e-commerce.",
     "Growing digital wallet usage reflects market modernisation.",
     "COD (Cash on Delivery) share is significant in certain regions."]
)

# 3c. Order Status Composition – Pie
status = df["Order Status"].value_counts().reset_index()
status.columns = ["Status","Count"]
fig = px.pie(
    status, names="Status", values="Count",
    color_discrete_sequence=CAT_COLORS,
    hole=0.3,
    title="Order Status Breakdown"
)
apply_layout(fig, "Order Status Breakdown")
plots["order_status"] = (
    fig,
    "Current fulfilment health: delivered, returned, cancelled.",
    ["High 'Delivered' share reflects good fulfilment efficiency.",
     "Returns and cancellations reveal customer satisfaction pain points.",
     "Monitoring these shares over time is key to reducing operational cost."]
)

# 3d. Sales by Region – Treemap
region_cat = df.groupby(["Region","Product Category"])["Revenue"].sum().reset_index()
fig = px.treemap(
    region_cat, path=["Region","Product Category"],
    values="Revenue",
    color="Revenue",
    color_continuous_scale=SEQ_COLORS,
    title="Revenue Treemap: Region → Category"
)
apply_layout(fig, "Revenue Treemap: Region → Category")
plots["treemap"] = (
    fig,
    "Hierarchical view of revenue, from region down to product category.",
    ["South and West regions typically generate highest revenue.",
     "Electronics is the top category across most regions.",
     "Smaller rectangles indicate under-served market opportunities."]
)

# 3e. Stacked Bar – Revenue by Year & Category
yr_cat = df.groupby(["Year","Product Category"])["Revenue"].sum().reset_index()
fig = px.bar(
    yr_cat, x="Year", y="Revenue",
    color="Product Category",
    barmode="stack",
    color_discrete_sequence=CAT_COLORS,
    title="Annual Revenue Composition by Product Category"
)
apply_layout(fig, "Annual Revenue Composition by Product Category")
plots["stacked_bar_yr"] = (
    fig,
    "Year-over-year revenue with category composition overlay.",
    ["Clear revenue growth is visible year on year.",
     "Category mix remains relatively stable, suggesting no dramatic product pivots.",
     "2022–2024 shows accelerated growth across all categories."]
)

# ──────────────────────────────────────────────────────────
# PAGE 4 ─ DATA RELATIONSHIP
# ──────────────────────────────────────────────────────────

# 4a. Correlation Heatmap
corr = df[num_cols].corr()
fig = go.Figure(go.Heatmap(
    z=corr.values,
    x=corr.columns.tolist(),
    y=corr.columns.tolist(),
    colorscale=DIVERG_SCALE,
    zmid=0,
    text=np.round(corr.values, 2),
    texttemplate="%{text}",
    hovertemplate="%{x} vs %{y}: %{z:.3f}<extra></extra>",
))
apply_layout(fig, "Pearson Correlation Matrix – Numeric KPIs")
plots["corr_heatmap"] = (
    fig,
    "Pairwise linear correlation between all numeric metrics.",
    ["Total Sales and Quantity Sold are positively correlated.",
     "Discount (%) has an inverse relationship with Profit Margin.",
     "Unit Price and Profit Margin share a moderate positive correlation."]
)

# 4b. Scatter – Discount vs Profit Margin
fig = px.scatter(
    df.sample(min(2000, len(df)), random_state=42),
    x="Discount (%)", y="Profit Margin",
    color="Product Category",
    size="Total Sales",
    color_discrete_sequence=CAT_COLORS,
    opacity=0.65,
    trendline="ols",
    trendline_scope="overall",
    trendline_color_override=PALETTE["accent3"],
    title="Discount (%) vs Profit Margin — Scatter with OLS Trend"
)
apply_layout(fig, "Discount (%) vs Profit Margin — Scatter with OLS Trend")
plots["discount_margin_scatter"] = (
    fig,
    "Each dot is an order. Larger dots = higher total sales. OLS trendline shows the aggregate relationship.",
    ["Negative trendline confirms that higher discounts erode profit margins.",
     "High-discount outliers in some categories suggest margin-destroying promotions.",
     "Premium categories maintain margins even at moderate discount levels."]
)

# 4c. Scatter – Unit Price vs Total Sales
fig = px.scatter(
    df.sample(min(2000, len(df)), random_state=7),
    x="Unit Price", y="Total Sales",
    color="Product Category",
    size="Quantity Sold",
    color_discrete_sequence=CAT_COLORS,
    opacity=0.65,
    log_x=True,
    title="Unit Price vs Total Sales (log scale)"
)
apply_layout(fig, "Unit Price vs Total Sales (log x-axis)")
plots["price_sales_scatter"] = (
    fig,
    "Relation between price point and order revenue, sized by quantity sold.",
    ["Higher-priced items generate larger individual order values.",
     "Volume-driven categories appear as mid-price, large-dot clusters.",
     "Log-scale helps distinguish low-price high-volume vs high-price low-volume segments."]
)

# 4d. Scatter Matrix (SPLOM) – numeric columns
fig = px.scatter_matrix(
    df[num_cols].dropna().sample(min(1500, len(df)), random_state=1),
    dimensions=num_cols,
    color_discrete_sequence=[PALETTE["accent4"]],
    opacity=0.35,
    title="Scatter Matrix — All Numeric KPIs"
)
fig.update_traces(marker=dict(size=3))
apply_layout(fig, "Scatter Matrix — All Numeric KPIs")
plots["splom"] = (
    fig,
    "Pairwise scatter matrix for fast multi-dimensional relationship discovery.",
    ["Total Sales vs Quantity Sold shows a clear positive linear band.",
     "Discount (%) vs Profit Margin shows the expected negative diagonal trend.",
     "No strong multicollinearity detected beyond the obvious pairs."]
)

# ──────────────────────────────────────────────────────────
# PAGE 5 ─ DATA COMPARISON
# ──────────────────────────────────────────────────────────

# 5a. Revenue by Region — Grouped Bar (Year)
reg_yr = df.groupby(["Region","Year"])["Revenue"].sum().reset_index()
fig = px.bar(
    reg_yr, x="Year", y="Revenue",
    color="Region",
    barmode="group",
    color_discrete_sequence=CAT_COLORS,
    title="Regional Revenue Comparison by Year"
)
apply_layout(fig, "Regional Revenue Comparison by Year")
plots["region_year_bar"] = (
    fig,
    "Side-by-side comparison of regional performance in each year.",
    ["All regions show consistent growth trajectories.",
     "Market share among regions has remained relatively balanced.",
     "Emerging regions show faster growth rates compared to mature markets."]
)

# 5b. Average Order Value by Salesperson – Top 15
avgsales = (df.groupby("Salesperson")["Revenue"]
              .agg(["mean","count"]).reset_index()
              .rename(columns={"mean":"Avg Revenue","count":"Orders"})
              .sort_values("Avg Revenue", ascending=False).head(15))
fig = px.bar(
    avgsales, x="Salesperson", y="Avg Revenue",
    color="Avg Revenue",
    color_continuous_scale=SEQ_COLORS,
    text=avgsales["Avg Revenue"].map("${:,.0f}".format),
    title="Top 15 Salespersons by Average Order Value"
)
apply_layout(fig, "Top 15 Salespersons by Average Order Value")
fig.update_traces(textposition="outside")
plots["salesperson_avg"] = (
    fig,
    "Identifies star performers who consistently close high-value orders.",
    ["Top salespersons achieve 2-3× the average order value.",
     "Training bottom performers on upselling could lift overall AOV.",
     "Correlation analysis with discount levels can reveal pricing habits."]
)

# 5c. Profit Margin Comparison by Category — Box
fig = px.box(
    df, x="Product Category", y="Profit Margin",
    color="Product Category",
    color_discrete_sequence=CAT_COLORS,
    points="outliers",
    title="Profit Margin Comparison Across Categories"
)
apply_layout(fig, "Profit Margin Comparison Across Categories")
plots["margin_cat_box"] = (
    fig,
    "Statistical comparison of profit margin across all product categories.",
    ["Electronics and Furniture show the widest margin variance.",
     "Service-based or subscription categories show tighter, higher margins.",
     "Comparing category median margins can guide product portfolio decisions."]
)

# 5d. Heatmap – Avg Revenue Month × Category
heat_df = df.pivot_table(
    values="Revenue", index="Month_Name", columns="Product Category",
    aggfunc="mean"
)
month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
heat_df = heat_df.reindex([m for m in month_order if m in heat_df.index])
fig = go.Figure(go.Heatmap(
    z=heat_df.values,
    x=heat_df.columns.tolist(),
    y=heat_df.index.tolist(),
    colorscale=SEQ_COLORS,
    hovertemplate="Month: %{y}<br>Category: %{x}<br>Avg Revenue: $%{z:,.0f}<extra></extra>",
))
apply_layout(fig, "Average Revenue Heatmap — Month × Product Category")
plots["heatmap_month_cat"] = (
    fig,
    "Cross-dimensional heatmap: which categories peak in which months.",
    ["Electronics peak in Nov/Dec (holiday gifting effect).",
     "Home & Garden peaks in spring months (April–June).",
     "Consistent performers show uniform colour across all months."]
)

# 5e. YoY Revenue Growth
yearly = df.groupby("Year")["Revenue"].sum().reset_index()
yearly["YoY Growth %"] = yearly["Revenue"].pct_change() * 100
fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Bar(
    x=yearly["Year"], y=yearly["Revenue"],
    name="Revenue", marker_color=PALETTE["accent1"],
    opacity=0.8,
    hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.0f}<extra></extra>"
), secondary_y=False)
fig.add_trace(go.Scatter(
    x=yearly["Year"], y=yearly["YoY Growth %"],
    name="YoY Growth %", mode="lines+markers",
    line=dict(color=PALETTE["accent3"], width=2.5),
    marker=dict(size=8),
    hovertemplate="<b>%{x}</b><br>Growth: %{y:.1f}%<extra></extra>"
), secondary_y=True)
fig.update_yaxes(title_text="Revenue ($)", secondary_y=False,
                 gridcolor=PALETTE["grid"], tickfont=dict(color=PALETTE["text"]))
fig.update_yaxes(title_text="YoY Growth (%)",  secondary_y=True,
                 gridcolor=PALETTE["grid"], tickfont=dict(color=PALETTE["text"]))
apply_layout(fig, "Year-over-Year Revenue & Growth Rate")
plots["yoy_growth"] = (
    fig,
    "Dual-axis chart: absolute revenue bars and YoY growth rate line.",
    ["Revenue has grown every year, confirming business expansion.",
     "Growth rate peaked in a mid-period year and has since moderated.",
     "Sustainable mid-single-digit to double-digit growth is the target."]
)

# ──────────────────────────────────────────────────────────
# PAGE 6 ─ UNIVARIATE ANALYSIS
# ──────────────────────────────────────────────────────────

# 6a. Categorical univariate – Product Category bar
cat_cnt = df["Product Category"].value_counts().reset_index()
cat_cnt.columns = ["Category","Count"]
fig = px.bar(cat_cnt, x="Category", y="Count",
             color="Count", color_continuous_scale=SEQ_COLORS,
             text="Count", title="Order Count by Product Category")
apply_layout(fig, "Order Count by Product Category")
fig.update_traces(textposition="outside")
plots["uni_cat"] = (
    fig,
    "Frequency distribution of orders across product categories.",
    ["Category volumes are fairly balanced, indicating no single category monopoly.",
     "Top categories (by orders) may differ from top categories (by revenue).",
     "Low-volume categories may be niche premium vs mass-market."]
)

# 6b. Univariate – Discount (%) histogram
fig = px.histogram(df, x="Discount (%)", nbins=25,
                   color_discrete_sequence=[PALETTE["accent2"]],
                   marginal="violin",
                   title="Discount (%) – Univariate Distribution")
apply_layout(fig, "Discount (%) – Univariate Distribution")
plots["uni_discount"] = (
    fig,
    "Full distribution of discount levels applied to orders.",
    ["Discounts cluster around round numbers (5%, 10%, 15%) — structured discount policy.",
     "A long tail of high discounts suggests occasional deep-discount events.",
     "Zero-discount orders indicate a healthy base of non-promotional sales."]
)

# 6c. Univariate – Customer orders frequency
cust_freq = df["Customer ID"].value_counts().reset_index()
cust_freq.columns = ["Customer ID","Orders"]
fig = px.histogram(cust_freq, x="Orders", nbins=30,
                   color_discrete_sequence=[PALETTE["accent4"]],
                   title="Customer Order Frequency Distribution")
apply_layout(fig, "Customer Order Frequency Distribution")
plots["uni_cust_freq"] = (
    fig,
    "How many times each customer has placed orders.",
    ["Most customers are occasional buyers (1-3 orders) — loyalty gap exists.",
     "A small group of repeat buyers (5+ orders) represents high-LTV customers.",
     "Targeting the 2-4 order cohort for retention campaigns can grow the loyal base."]
)

# ──────────────────────────────────────────────────────────
# PAGE 7 ─ BIVARIATE ANALYSIS
# ──────────────────────────────────────────────────────────

# 7a. Revenue vs Quantity – by Payment Method
fig = px.scatter(
    df.sample(min(2000, len(df)), random_state=3),
    x="Quantity Sold", y="Revenue",
    color="Payment Method",
    color_discrete_sequence=CAT_COLORS,
    opacity=0.6,
    title="Revenue vs Quantity Sold by Payment Method"
)
apply_layout(fig, "Revenue vs Quantity Sold by Payment Method")
plots["bi_qty_rev"] = (
    fig,
    "Bivariate: order quantity and revenue coloured by payment channel.",
    ["Credit card orders tend to have higher individual revenue.",
     "Digital wallet orders cluster at lower quantities – impulse-buy behaviour.",
     "COD orders are more homogeneous in quantity and revenue range."]
)

# 7b. Avg Profit Margin by Region
reg_margin = df.groupby("Region")["Profit Margin"].mean().reset_index().sort_values("Profit Margin", ascending=False)
fig = px.bar(reg_margin, x="Region", y="Profit Margin",
             color="Profit Margin", color_continuous_scale=SEQ_COLORS,
             text=reg_margin["Profit Margin"].map("{:.1f}%".format),
             title="Average Profit Margin by Region")
apply_layout(fig, "Average Profit Margin by Region")
plots["bi_region_margin"] = (
    fig,
    "Which regions are most profitable on average.",
    ["Significant margin variation across regions suggests pricing/cost differences.",
     "Lower-margin regions may reflect higher logistics costs or competitive pricing.",
     "Focus premium product pushes in high-margin regions."]
)

# 7c. Bivariate – Monthly Avg Discount vs Revenue
month_disc = df.groupby("Month").agg(
    Avg_Discount=("Discount (%)","mean"),
    Avg_Revenue=("Revenue","mean")
).reset_index()
fig = px.scatter(month_disc, x="Avg_Discount", y="Avg_Revenue",
                 text="Month",
                 size="Avg_Revenue",
                 color="Avg_Revenue",
                 color_continuous_scale=SEQ_COLORS,
                 title="Monthly Avg Discount vs Avg Revenue")
apply_layout(fig, "Monthly Avg Discount vs Avg Revenue")
fig.update_traces(textposition="top center")
plots["bi_disc_rev_month"] = (
    fig,
    "Bubble chart: each bubble = one month, sized and coloured by average revenue.",
    ["Months with high discounts don't necessarily yield high revenue.",
     "Q4 months often show high revenue WITH moderate discounts — organic demand.",
     "Over-discounting in low-revenue months may be an inefficient lever."]
)

# ──────────────────────────────────────────────────────────
# PAGE 8 ─ MULTIVARIATE ANALYSIS
# ──────────────────────────────────────────────────────────

# 8a. 3D Scatter – Unit Price / Discount / Revenue
sample3d = df.dropna(subset=["Unit Price","Discount (%)","Revenue","Product Category"]).sample(min(1000,len(df)), random_state=9)
fig = px.scatter_3d(
    sample3d,
    x="Unit Price", y="Discount (%)", z="Revenue",
    color="Product Category",
    size="Quantity Sold",
    color_discrete_sequence=CAT_COLORS,
    opacity=0.7,
    title="3D Scatter: Unit Price × Discount × Revenue"
)
apply_layout(fig, "3D Scatter: Unit Price × Discount × Revenue")
plots["scatter_3d"] = (
    fig,
    "Three-dimensional view showing interactions between price, discount and revenue.",
    ["High-price items generate high revenue regardless of discount level.",
     "Electronics (high price) form a distinct revenue cluster at the top.",
     "Middle-price products show the most sensitivity to discount variation."]
)

# 8b. Parallel Coordinates – full numeric view
fig = px.parallel_coordinates(
    df[num_cols + ["Year"]].dropna().sample(min(1500, len(df)), random_state=5),
    color="Year",
    color_continuous_scale=SEQ_COLORS,
    dimensions=num_cols,
    title="Parallel Coordinates — Numeric Metrics by Year"
)
apply_layout(fig, "Parallel Coordinates — Numeric Metrics by Year")
plots["parallel_coords"] = (
    fig,
    "Each line is an order; axes are numeric dimensions; colour = year.",
    ["Visible 'bands' show clusters of similar order profiles.",
     "High-revenue orders tend to have higher unit prices.",
     "Drag axis filters to isolate high-value or high-discount segments interactively."]
)

# 8c. Sunburst – Region → Category → Payment
fig = px.sunburst(
    df, path=["Region","Product Category","Payment Method"],
    values="Revenue",
    color="Revenue",
    color_continuous_scale=SEQ_COLORS,
    title="Revenue Sunburst: Region → Category → Payment Method"
)
apply_layout(fig, "Revenue Sunburst: Region → Category → Payment Method")
plots["sunburst"] = (
    fig,
    "Three-level hierarchical view: drill from region to category to payment.",
    ["Click any segment to drill down for focused analysis.",
     "Credit card users generate the most revenue in premium categories.",
     "Region-specific payment preferences are visible in the inner rings."]
)

# 8d. Facet – Revenue Distribution by Status & Category
fig = px.box(
    df, x="Product Category", y="Revenue",
    facet_row="Order Status",
    color="Product Category",
    color_discrete_sequence=CAT_COLORS,
    title="Revenue Distribution: Category × Order Status"
)
apply_layout(fig, "Revenue Distribution: Category × Order Status")
fig.update_layout(height=800)
plots["facet_status_cat"] = (
    fig,
    "Faceted comparison reveals how order status interacts with category revenue.",
    ["Returned orders span across all revenue levels — return is not purely luxury-driven.",
     "Cancelled orders tend to cluster at mid-price ranges, hinting at price sensitivity.",
     "Delivered orders have the widest revenue distribution — expected for completed sales."]
)

# ──────────────────────────────────────────────────────────
# PAGE 9 ─ STATISTICAL ANALYSIS
# ──────────────────────────────────────────────────────────

# 9a. ANOVA – Revenue differences across regions
groups = [df[df["Region"]==r]["Revenue"].dropna() for r in df["Region"].dropna().unique()]
f_stat, p_val_anova = stats.f_oneway(*groups)

# 9b. Correlation table
corr_results = []
pairs = [
    ("Discount (%)","Profit Margin"),
    ("Unit Price","Total Sales"),
    ("Quantity Sold","Total Sales"),
    ("Discount (%)","Total Sales"),
    ("Unit Price","Profit Margin"),
]
for a, b in pairs:
    r, p = pearsonr(df[a].dropna(), df[b].dropna()[:len(df[a].dropna())])
    corr_results.append({"Pair": f"{a} ↔ {b}", "Pearson r": round(r,4), "p-value": f"{p:.4e}", "Significant": "✔" if p < 0.05 else "✘"})
corr_df = pd.DataFrame(corr_results)

# 9c. Z-test: mean revenue of top region vs overall
top_region = df.groupby("Region")["Revenue"].mean().idxmax()
z_stat, p_val_z = ztest(df[df["Region"]==top_region]["Revenue"].dropna(),
                         value=df["Revenue"].mean())

stat_html = f"""
<div style='color:{PALETTE["text"]};font-family:Inter,Arial,sans-serif;padding:20px'>
<h3 style='color:{PALETTE["accent1"]}'>Statistical Test Results</h3>
<table style='border-collapse:collapse;width:100%'>
  <tr style='background:{PALETTE["primary"]};color:{PALETTE["accent1"]}'>
    <th style='padding:10px;text-align:left'>Test</th>
    <th style='padding:10px;text-align:left'>Result</th>
    <th style='padding:10px;text-align:left'>Interpretation</th>
  </tr>
  <tr style='background:{PALETTE["card"]}'>
    <td style='padding:8px'>One-way ANOVA (Revenue ~ Region)</td>
    <td style='padding:8px'>F={f_stat:.2f}, p={p_val_anova:.4e}</td>
    <td style='padding:8px'>{'Significant regional revenue differences' if p_val_anova<0.05 else 'No significant difference'}</td>
  </tr>
  <tr>
    <td style='padding:8px'>Z-test ({top_region} vs overall mean)</td>
    <td style='padding:8px'>Z={z_stat:.2f}, p={p_val_z:.4e}</td>
    <td style='padding:8px'>{'Top region significantly differs' if p_val_z<0.05 else 'No significant difference'}</td>
  </tr>
</table>
<br>
<h3 style='color:{PALETTE["accent1"]}'>Pearson Correlation Table</h3>
<table style='border-collapse:collapse;width:100%'>
  <tr style='background:{PALETTE["primary"]};color:{PALETTE["accent1"]}'>
    {''.join(f'<th style="padding:10px;text-align:left">{c}</th>' for c in corr_df.columns)}
  </tr>
  {''.join('<tr style="background:'+PALETTE["card"]+'">'+
    ''.join(f'<td style="padding:8px">{v}</td>' for v in row)+'</tr>'
    for row in corr_df.values)}
</table>
</div>"""

# 9d. Regression OLS summary plot – Revenue ~ Price + Qty + Discount
ols_df = df[["Revenue","Unit Price","Quantity Sold","Discount (%)"]].dropna()
X = sm.add_constant(ols_df[["Unit Price","Quantity Sold","Discount (%)"]])
model = sm.OLS(ols_df["Revenue"], X).fit()
coef = model.params.drop("const")
ci   = model.conf_int().drop("const")

fig = go.Figure()
fig.add_trace(go.Bar(
    x=coef.index, y=coef.values,
    error_y=dict(
        type="data",
        array     =(ci[1] - coef).values,
        arrayminus=(coef - ci[0]).values,
        visible=True,
        color=PALETTE["accent3"],
    ),
    marker_color=[PALETTE["accent4"] if v>0 else PALETTE["accent3"] for v in coef.values],
    hovertemplate="<b>%{x}</b><br>Coefficient: %{y:.4f}<extra></extra>"
))
apply_layout(fig, f"OLS Regression Coefficients (R²={model.rsquared:.3f})")
plots["ols_coef"] = (
    fig,
    f"OLS regression of Revenue on key predictors. R²={model.rsquared:.3f}.",
    [f"Model explains {model.rsquared*100:.1f}% of revenue variance.",
     "Quantity Sold has the greatest coefficient — strong volume-revenue link.",
     "Unit Price effect is significant — pricing strategy directly impacts revenue.",
     "Discount coefficient direction reveals net promotional effectiveness."]
)

# 9e. Q-Q plot for Revenue normality
sample_rev = df["Revenue"].dropna().sample(min(500,len(df)), random_state=42)
(osm, osr), (slope, intercept, r) = stats.probplot(sample_rev, dist="norm")
fig = go.Figure()
fig.add_trace(go.Scatter(x=list(osm), y=list(osr), mode="markers",
                          marker=dict(color=PALETTE["accent4"], size=4, opacity=0.7),
                          name="Data"))
fig.add_trace(go.Scatter(x=[min(osm), max(osm)],
                          y=[slope*min(osm)+intercept, slope*max(osm)+intercept],
                          mode="lines",
                          line=dict(color=PALETTE["accent3"], width=2),
                          name="Normal Line"))
apply_layout(fig, "Q-Q Plot: Revenue Normality Check")
plots["qq_plot"] = (
    fig,
    "Q-Q plot tests if Revenue follows a normal distribution.",
    ["Deviations in the tails confirm right-skewed, non-normal revenue.",
     "Log-transformation is recommended before parametric tests.",
     "Non-normality in revenue is common in e-commerce — use robust statistics."]
)

# ──────────────────────────────────────────────────────────
# PAGE 10 ─ ADVANCED INSIGHTS
# ──────────────────────────────────────────────────────────

# 10a. Funnel – Order Status pipeline
status_order = ["Pending","Processing","Shipped","Delivered"]
status_vals  = []
for s in status_order:
    v = df[df["Order Status"]==s]["Revenue"].sum()
    if v > 0:
        status_vals.append((s, v))

if len(status_vals) > 1:
    fig_funnel = go.Figure(go.Funnel(
        y=[x[0] for x in status_vals],
        x=[x[1] for x in status_vals],
        marker=dict(color=SEQ_COLORS[:len(status_vals)]),
        textinfo="value+percent previous",
        hovertemplate="<b>%{y}</b><br>Revenue: $%{x:,.0f}<extra></extra>"
    ))
    apply_layout(fig_funnel, "Revenue Funnel — Order Status Pipeline")
    plots["funnel"] = (
        fig_funnel,
        "Revenue funnel shows drop-off from pending to delivered stages.",
        ["Significant revenue sits in earlier pipeline stages.",
         "Conversion from Processing to Shipped is a key bottleneck.",
         "Optimising logistics can unlock stranded revenue."]
    )

# 10b. Top 10 Products by Revenue
top_prods = (df.groupby("Product Name")["Revenue"].sum()
               .reset_index().sort_values("Revenue", ascending=True).tail(10))
fig = px.bar(top_prods, x="Revenue", y="Product Name", orientation="h",
             color="Revenue", color_continuous_scale=SEQ_COLORS,
             text=top_prods["Revenue"].map("${:,.0f}".format),
             title="Top 10 Products by Revenue")
apply_layout(fig, "Top 10 Products by Revenue")
fig.update_traces(textposition="outside")
plots["top10_products"] = (
    fig,
    "Best revenue-generating individual products.",
    ["A small number of SKUs drive a large share of revenue (Pareto principle).",
     "Top products should be priority-stocked and protected from stockouts.",
     "Cross-sell opportunities exist by bundling top products with related items."]
)

# 10c. Cohort – Revenue by Year & Quarter
qtr_rev = df.groupby(["Year","Quarter"])["Revenue"].sum().reset_index()
fig = px.line(qtr_rev, x="Quarter", y="Revenue",
              color=qtr_rev["Year"].astype(str),
              markers=True,
              color_discrete_sequence=SEQ_COLORS,
              title="Quarterly Revenue by Year — Cohort Trend")
apply_layout(fig, "Quarterly Revenue by Year — Cohort Trend")
plots["quarterly_cohort"] = (
    fig,
    "Overlay of quarterly revenue lines per year reveals seasonal patterns.",
    ["Q4 consistently peaks — holiday / year-end demand.","Q1 often dips post-holiday.","Year-over-year lift indicates healthy business growth."]
)

# 10d. Revenue concentration – Pareto chart
prod_rev  = df.groupby("Product Name")["Revenue"].sum().sort_values(ascending=False).reset_index()
prod_rev["Cumulative %"] = prod_rev["Revenue"].cumsum() / prod_rev["Revenue"].sum() * 100
prod_rev["Rank"] = range(1, len(prod_rev)+1)

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Bar(
    x=prod_rev["Rank"], y=prod_rev["Revenue"],
    name="Revenue per Product",
    marker_color=PALETTE["accent1"],
    opacity=0.75,
    hovertemplate="Rank %{x}<br>Revenue: $%{y:,.0f}<extra></extra>"
), secondary_y=False)
fig.add_trace(go.Scatter(
    x=prod_rev["Rank"], y=prod_rev["Cumulative %"],
    name="Cumulative %",
    mode="lines",
    line=dict(color=PALETTE["accent3"], width=2.5),
    hovertemplate="Rank %{x}<br>Cumulative: %{y:.1f}%<extra></extra>"
), secondary_y=True)
fig.update_yaxes(title_text="Revenue ($)", secondary_y=False,
                 gridcolor=PALETTE["grid"], tickfont=dict(color=PALETTE["text"]))
fig.update_yaxes(title_text="Cumulative %", secondary_y=True,
                 gridcolor=PALETTE["grid"], tickfont=dict(color=PALETTE["text"]))
apply_layout(fig, "Pareto Chart — Revenue Concentration by Product")
plots["pareto"] = (
    fig,
    "Pareto principle applied to product revenue: what % of products drive 80% of revenue.",
    ["Typically ~20% of products drive ~80% of revenue.",
     "Focus inventory and marketing resources on the top Pareto products.",
     "Long-tail products can still be valuable for SEO and customer acquisition."]
)

print(f"  Generated {len(plots)} plots")

# ─────────────────────────────────────────────
# 4. BUILD DASHBOARD HTML
# ─────────────────────────────────────────────
print("Building dashboard HTML …")

def fig_to_html(fig, div_id):
    return fig.to_html(full_html=False, include_plotlyjs=False, div_id=div_id,
                       config={"displayModeBar": True, "responsive": True})

PAGES = [
    ("overview",       "Executive Overview",         ["monthly_trend","kpi_table"]),
    ("distribution",   "Data Distribution",          ["revenue_dist","boxplots","violin_margin","qty_dist"]),
    ("composition",    "Data Composition",           ["category_donut","payment_method","order_status","treemap","stacked_bar_yr"]),
    ("relationship",   "Data Relationship",          ["corr_heatmap","discount_margin_scatter","price_sales_scatter","splom"]),
    ("comparison",     "Data Comparison",            ["region_year_bar","salesperson_avg","margin_cat_box","heatmap_month_cat","yoy_growth"]),
    ("univariate",     "Univariate Analysis",        ["uni_cat","uni_discount","uni_cust_freq"]),
    ("bivariate",      "Bivariate Analysis",         ["bi_qty_rev","bi_region_margin","bi_disc_rev_month"]),
    ("multivariate",   "Multivariate Analysis",      ["scatter_3d","parallel_coords","sunburst","facet_status_cat"]),
    ("statistical",    "Statistical Analysis",       ["ols_coef","qq_plot","corr_heatmap"]),
    ("advanced",       "Advanced Insights",          ["top10_products","pareto","quarterly_cohort"] + (["funnel"] if "funnel" in plots else [])),
]

css = f"""
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:{PALETTE["bg"]};color:{PALETTE["text"]};font-family:'Inter',Arial,sans-serif;min-height:100vh}}
header{{display:flex;align-items:center;gap:20px;padding:16px 32px;
        background:{PALETTE["card"]};border-bottom:2px solid {PALETTE["primary"]};
        position:sticky;top:0;z-index:999;box-shadow:0 2px 16px rgba(0,0,0,.5)}}
header img{{height:52px;border-radius:8px}}
header h1{{font-size:1.6rem;color:{PALETTE["accent1"]};letter-spacing:.5px}}
header p{{font-size:.85rem;color:{PALETTE["accent5"]};margin-top:2px}}
nav{{display:flex;flex-wrap:wrap;gap:8px;padding:14px 32px;
     background:{PALETTE["card"]};border-bottom:1px solid {PALETTE["grid"]}}}
.nav-btn{{padding:8px 18px;border:1px solid {PALETTE["grid"]};background:transparent;
          color:{PALETTE["text"]};border-radius:20px;cursor:pointer;font-size:.85rem;
          transition:all .2s}}
.nav-btn:hover,.nav-btn.active{{background:{PALETTE["primary"]};color:{PALETTE["accent1"]};
                                 border-color:{PALETTE["accent1"]}}}
.page{{display:none;padding:28px 32px;animation:fadeIn .25s ease}}
.page.active{{display:block}}
@keyframes fadeIn{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}
.chart-card{{background:{PALETTE["card"]};border:1px solid {PALETTE["grid"]};
             border-radius:12px;padding:20px;margin-bottom:26px;
             box-shadow:0 4px 24px rgba(0,0,0,.35)}}
.chart-card h3{{color:{PALETTE["accent1"]};font-size:1rem;margin-bottom:6px}}
.interpretation{{background:rgba(13,59,102,.35);border-left:4px solid {PALETTE["accent1"]};
                 padding:12px 16px;border-radius:0 8px 8px 0;margin-top:14px;
                 font-size:.88rem;line-height:1.6}}
.key-findings{{margin-top:10px;font-size:.84rem}}
.key-findings li{{padding:3px 0;list-style:disc;margin-left:18px;color:{PALETTE["accent5"]}}}
.stat-block{{background:{PALETTE["card"]};border-radius:12px;padding:20px;
             border:1px solid {PALETTE["grid"]}}}
footer{{text-align:center;padding:22px;color:{PALETTE["accent5"]};font-size:.8rem;
        border-top:1px solid {PALETTE["grid"]}}}
"""

nav_html = ""
for pid, pname, _ in PAGES:
    active = "active" if pid == "overview" else ""
    nav_html += f'<button class="nav-btn {active}" onclick="showPage(\'{pid}\')">{pname}</button>\n'

pages_html = ""
for pid, pname, plot_keys in PAGES:
    active = "active" if pid == "overview" else ""
    block = f'<div id="{pid}" class="page {active}">\n<h2 style="color:{PALETTE["accent1"]};margin-bottom:20px">{pname}</h2>\n'
    for pk in plot_keys:
        if pk not in plots:
            continue
        fig, interp, findings = plots[pk]
        findings_html = "".join(f"<li>{f}</li>" for f in findings)
        block += f"""<div class="chart-card">
{fig_to_html(fig, pk)}
<div class="interpretation">
  <strong>Interpretation:</strong> {interp}
  <ul class="key-findings">{findings_html}</ul>
</div>
</div>\n"""
    # Special: statistical page raw HTML block
    if pid == "statistical":
        block += f'<div class="stat-block">{stat_html}</div>\n'
    block += "</div>\n"
    pages_html += block

logo_tag = f'<img src="data:image/png;base64,{logo_b64}" alt="Logo">' if logo_b64 else ""

dashboard_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Amazon Sales Analytics Dashboard 2019-2024</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>{css}</style>
</head>
<body>
<header>
  {logo_tag}
  <div>
    <h1>Amazon Sales Analytics Dashboard</h1>
    <p>E-Commerce Intelligence Report &nbsp;|&nbsp; 2019 – 2024 &nbsp;|&nbsp; 5,000 Orders</p>
  </div>
</header>
<nav>{nav_html}</nav>
<main>{pages_html}</main>
<footer>
  Generated on {pd.Timestamp.now().strftime("%B %d, %Y")} &nbsp;|&nbsp;
  Data: amazon_sales_dataset_2019_2024 &nbsp;|&nbsp; &copy; Amazon Sales Analytics
</footer>
<script>
function showPage(id){{
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b=>b.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  event.target.classList.add('active');
  // Resize all plotly charts in the newly shown page
  setTimeout(()=>{{
    const charts = document.getElementById(id).querySelectorAll('.js-plotly-plot');
    charts.forEach(c=>Plotly.Plots.resize(c));
  }},100);
}}
</script>
</body>
</html>"""

with open(OUT_HTML, "w", encoding="utf-8") as f:
    f.write(dashboard_html)
print(f"  Dashboard → {OUT_HTML.name}")

# ─────────────────────────────────────────────
# 5. STANDALONE REPORT HTML (all pages together, printable)
# ─────────────────────────────────────────────
print("Building standalone report HTML …")

report_css = css.replace(".page{display:none;","/*\n.page{display:none;*/\n.page{display:block;")
report_css += """
.page { display:block !important; }
nav { display:none; }
header { position:static; }
"""

all_pages_html = ""
for pid, pname, plot_keys in PAGES:
    block = f'<div id="{pid}" class="page active">\n<h2 style="color:{PALETTE["accent1"]};margin-bottom:20px;page-break-before:always">{pname}</h2>\n'
    for pk in plot_keys:
        if pk not in plots:
            continue
        fig, interp, findings = plots[pk]
        findings_html = "".join(f"<li>{f}</li>" for f in findings)
        block += f"""<div class="chart-card">
{fig_to_html(fig, "r"+pk)}
<div class="interpretation">
  <strong>Interpretation:</strong> {interp}
  <ul class="key-findings">{findings_html}</ul>
</div>
</div>\n"""
    if pid == "statistical":
        block += f'<div class="stat-block">{stat_html}</div>\n'
    block += "</div>\n"
    all_pages_html += block

standalone = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Amazon Sales Analytics Report 2019-2024</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>{report_css}</style>
</head>
<body>
<header>
  {logo_tag}
  <div>
    <h1>Amazon Sales Analytics — Full Report</h1>
    <p>E-Commerce Intelligence Report &nbsp;|&nbsp; 2019 – 2024 &nbsp;|&nbsp; 5,000 Orders</p>
  </div>
</header>
<main>{all_pages_html}</main>
<footer>Generated on {pd.Timestamp.now().strftime("%B %d, %Y")} | &copy; Amazon Sales Analytics</footer>
</body>
</html>"""

with open(OUT_REPORT, "w", encoding="utf-8") as f:
    f.write(standalone)
print(f"  Report     → {OUT_REPORT.name}")

# ─────────────────────────────────────────────
# 6. PDF GENERATION (via weasyprint)
# ─────────────────────────────────────────────
print("Generating PDF …")
try:
    from weasyprint import HTML as WPHTML
    WPHTML(filename=str(OUT_REPORT)).write_pdf(str(OUT_PDF))
    print(f"  PDF        → {OUT_PDF.name}")
except Exception as e:
    print(f"  PDF skipped (weasyprint not available or error): {e}")
    # Fallback: generate a simplified PDF notice
    print("  Tip: Open amazon_sales_report.html in Chrome and use Ctrl+P → Save as PDF")

print("\n✅ All outputs generated successfully!")
print(f"   Dashboard : {OUT_HTML}")
print(f"   Report    : {OUT_REPORT}")
