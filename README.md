# Nassau Candy — Product Line Profitability & Margin Analysis

An interactive data analytics dashboard built with **Python, Pandas, Streamlit, and Plotly** to analyze product profitability, gross margins, pricing inefficiencies, and business performance using Nassau Candy sales data.

**🚀 Live Dashboard:** [View Nassau Candy Dashboard](https://wroxn94cuplmefqp37frkm.streamlit.app/)

**💻 GitHub Repository:** [Arpita114/nassau](https://github.com/Arpita114/nassau)

---

## Project Overview

This project transforms raw sales data into an interactive business intelligence dashboard. It helps explore product-level profitability, identify low-margin products, evaluate cost pressures, and understand revenue concentration across the portfolio.

The dataset contains **10,194 order lines** covering January 2024 through December 2025.

## Tech Stack

- **Python** — application logic and data analysis
- **Pandas & NumPy** — data cleaning, transformation, and calculations
- **Streamlit** — interactive dashboard interface
- **Plotly** — interactive data visualizations
- **CSV** — source and processed datasets
- **Git & GitHub** — version control and project hosting
- **Streamlit Community Cloud** — deployment

## Key Features

- Interactive dashboard with global filters and navigation
- Product-level sales, gross profit, and gross margin analysis
- Profit-per-unit and revenue/profit contribution metrics
- Product profitability quadrant analysis
- Low-margin product identification and repricing recommendations
- Cost renegotiation and discontinuation review flags
- Product-level pricing inefficiency analysis
- Pareto analysis of revenue and profit concentration
- Factory and state-level analytical rollups
- Data quality validation, audit flags, and cleaning logs
- Export functionality for analytical outputs

## Key Business Findings

Based on the default settings and full date range:

| Metric | Result |
|---|---:|
| Total Sales | $141,784 |
| Gross Profit | $93,443 |
| Gross Margin | 65.9% |
| Profit per Unit | $2.42 |

### Portfolio Insights

- **Chocolate dominates the portfolio**, contributing 92.9% of revenue and 95.1% of gross profit.
- **Sugar contributes approximately 0.3% of revenue**, indicating a highly concentrated product portfolio.
- Five products account for approximately 80% of revenue and gross profit.
- The top five products contribute approximately 95% of gross profit, highlighting dependency on a small number of products.

### Pricing and Cost Recommendations

**Products flagged for repricing** under the default 50% gross margin threshold:

- Kazookles — 7.7% margin
- Fun Dip — 40.0% margin
- Nerds — 46.7% margin
- SweeTARTS — 46.7% margin

**Cost renegotiation candidate:**
- Kazookles — cost represents approximately 92% of sales, with 371 units sold.

**Products flagged for discontinuation review:**
- Laffy Taffy
- SweeTARTS
- Nerds
- Fun Dip

These are analytical flags intended to support business review, not automatic decisions to change prices or discontinue products.

## KPI Definitions

- **Gross Margin %** = Gross Profit ÷ Sales × 100
- **Profit per Unit** = Gross Profit ÷ Units Sold
- **Revenue Contribution** = Product Sales ÷ Total Sales
- **Profit Contribution** = Product Gross Profit ÷ Total Gross Profit
- **Margin Volatility** = Standard deviation of monthly product gross margins
- **Repricing Flag** = Gross margin below the selected threshold
- **Cost Renegotiation Flag** = Cost-to-sales ratio of at least 60% and unit volume at or above the median product volume
- **Discontinuation Review Flag** = Sales at or below the 25th percentile and either gross profit at or below the 25th percentile or margin below the selected threshold

## Data Quality and Limitations

The project includes validation rules and data quality flags. Important limitations should be considered when interpreting the dashboard:

1. **Factory allocation:** The source data does not contain a factory column. Product sales are split equally across candidate factories based on the available mapping. Factory figures are estimates, not measured production or sales by plant.
2. **Approximate factory coordinates:** Factory locations use approximate metropolitan coordinates and should be replaced with verified plant addresses for geographic analysis.
3. **Ship-date anomalies:** The dataset contains implausible shipping lags of approximately 904–1,642 days. These are flagged and excluded from KPI calculations.
4. **Product classification conflict:** Fizzy Lifting Drinks has an `OTH-` product ID but is labelled as Sugar. The supplied division label is retained and the conflict is logged.
5. **Limited product count:** Only 15 products are present, so Pareto thresholds are relatively coarse.
6. **Margin volatility:** Unit prices and unit costs are constant in this dataset, resulting in effectively zero monthly margin volatility. This metric therefore provides limited differentiation between products.
7. **Postal code formatting:** Leading zeros were lost in the original export. US postal codes were padded to five digits for consistency.

## Project Structure

```text
nassau/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   ├── raw/
│   │   └── nassau_candy_raw.csv
│   └── processed/
│       └── nassau_candy_clean.csv
├── docs/
│   └── cleaning_log.md
├── scripts/
│   ├── audit.py
│   └── build_clean.py
└── src/
    ├── __init__.py
    ├── charts.py
    ├── config.py
    ├── data_loading.py
    └── metrics.py
```

## Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/Arpita114/nassau.git
cd nassau
```

### 2. Create and activate a virtual environment (optional but recommended)

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Build the cleaned dataset

```bash
python scripts/build_clean.py
```

This runs the cleaning pipeline and generates the processed dataset and cleaning log.

### 5. Run the KPI audit

```bash
python scripts/audit.py
```

This independently recalculates headline KPIs from the raw CSV and checks data quality flags.

### 6. Launch the dashboard

```bash
streamlit run app.py
```

Open the local URL displayed in the terminal.

## Deployment

This application is deployed using **Streamlit Community Cloud**.

- Main file: `app.py`
- Python runtime: Python 3.11
- Dependencies: `requirements.txt`
- Source data: `data/raw/nassau_candy_raw.csv`

**Live application:** https://wroxn94cuplmefqp37frkm.streamlit.app/

The raw dataset must remain available in the repository because the application uses it as a source for loading and analysis.

## Future Improvements

- Integrate verified factory-level data and coordinates.
- Investigate anomalous order and shipping dates with the data owner.
- Add time-varying prices and costs to make margin volatility more informative.
- Add automated tests and continuous integration for data validation.
- Improve product-level recommendations with additional business context.

## Author

**Arpita Gupta**

- GitHub: [@Arpita114](https://github.com/Arpita114)
- Project Repository: [Nassau Candy Analysis](https://github.com/Arpita114/nassau)
- Live Demo: [Streamlit Dashboard](https://wroxn94cuplmefqp37frkm.streamlit.app/)

---

*This project demonstrates data cleaning, exploratory data analysis, KPI design, interactive visualization, data quality auditing, and deployment of a Python analytics application.*
