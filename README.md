# Amazon Sales Analytics

A complete e-commerce analytics project built with Python and interactive Plotly dashboards.

## Project Structure

```text
Amazon_Sales/
├── assets/                      # Optional branding assets (logo.png)
├── data/
│   └── raw/
│       └── amazon_sales.xlsx
├── docs/
│   └── ANALYTICS_GUIDE.md
├── notebooks/
│   └── amazon.ipynb
├── reports/
│   ├── html/
│   │   ├── amazon_sales_dashboard.html
│   │   └── amazon_sales_report.html
│   └── pdf/
│       └── amazon_sales_report.pdf
├── scripts/
│   ├── generate_pdf.py
│   ├── inspect_data.py
│   └── inspect2.py
└── src/
    └── analysis.py
```

## Highlights

- EDA and business-focused insights for e-commerce sales
- Four analytics dimensions:
  - Data Distribution
  - Data Composition
  - Data Relationship
  - Data Comparison
- Univariate, bivariate, and multivariate analysis
- Statistical testing (ANOVA, correlation, OLS)
- Multi-page interactive dashboard (HTML)
- Standalone HTML report and PDF export support

## Insights and Results

This project produced a business-ready analytics report from 5,000 e-commerce orders (2019-2024), with key findings below.

- Revenue shows a clear upward long-term trend with recurring seasonal peaks (especially in Q4).
- Sales performance differs across regions and categories, highlighting where growth is strongest.
- Discount and profit margin show an inverse relationship, confirming margin pressure from aggressive discounting.
- A small subset of products contributes a large share of total revenue (Pareto concentration).
- Payment method and order status distributions reveal operational and customer behavior patterns.
- Statistical analysis (ANOVA, correlation, OLS) supports the visual findings with significant quantitative evidence.

### Business Impact

- Better promotion strategy by balancing discount depth against profit margin.
- Stronger inventory planning based on seasonal and category-level demand patterns.
- Clear focus areas for regional expansion and product portfolio optimization.
- Decision-ready reporting through interactive dashboard pages and exportable HTML/PDF outputs.

## Run

1. Use your existing conda environment:

```bash
conda activate y_dtale
```

2. Generate dashboard + reports:

```bash
python src/analysis.py
```

3. Generate PDF from HTML report:

```bash
python scripts/generate_pdf.py
```

## Notes

- Place your logo at: `assets/logo.png`
- Main outputs are saved to:
  - `reports/html/amazon_sales_dashboard.html`
  - `reports/html/amazon_sales_report.html`
  - `reports/pdf/amazon_sales_report.pdf`
