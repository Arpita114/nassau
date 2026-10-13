# Nassau Candy — Product Line Profitability & Margin Performance Analysis

Streamlit dashboard built to the PRD (v1.0). Source data: `data/raw/nassau_candy_raw.csv`
(10,194 order lines, Jan 2024 – Dec 2025).

## Run locally
```bash
pip install -r requirements.txt
python scripts/build_clean.py   # cleaning pipeline -> data/processed + docs/cleaning_log.md
python scripts/audit.py         # independent KPI audit vs raw CSV
streamlit run app.py
```

## Deploy (Streamlit Community Cloud)
1. Push this folder to a GitHub repo (keep `data/raw/` so the app can load the bundled CSV).
2. In share.streamlit.io, create an app: main file `app.py`, Python 3.11+.
3. Requirements come from `requirements.txt`. The live URL is the deployed app's URL.

## Layout
```
app.py                 Streamlit entry point (sidebar nav, global controls, 4 modules, exports)
src/config.py          Paths, factory reference data, default thresholds
src/data_loading.py    Cleaning & validation pipeline (DQ-1..DQ-5 + audit flags), cleaning log
src/metrics.py         KPIs, quadrants, risk flags, pricing inefficiency, Pareto, factory & state rollups
src/charts.py          Plotly chart builders
scripts/build_clean.py Writes cleaned CSV + cleaning log
scripts/audit.py       Recomputes headline KPIs from raw data and checks flags
docs/cleaning_log.md   Generated record of every cleaning step and row count
```

## Key definitions
- Gross Margin % = Gross Profit ÷ Sales · Profit per Unit = Gross Profit ÷ Units
- Revenue / Profit Contribution = product share of total Sales / Gross Profit
- Margin Volatility = std. dev. of monthly gross margin per product (blank if < 2 months)
- Reprice: margin % < slider threshold (default 50%)
- Cost renegotiation: Cost/Sales ≥ 60% AND units ≥ median product volume
- Discontinuation review: product sales ≤ 25th percentile AND (gross profit ≤ 25th percentile OR margin < threshold)

## Assumptions and data caveats (read before using the numbers)
1. **No factory column in the data.** The PRD's product→factory mapping is one-to-many, so each
   product's sales are split equally across its candidate factories. Factory figures are allocations, not
   measured plant output. Chocolate's two factories therefore show identical values.
2. **Factory coordinates are approximate** metro-level points (`src/config.py`). Replace with exact
   plant addresses.
3. **Ship dates are implausible:** every row has a 904–1,642 day lag between order and ship date. The
   field is flagged and excluded from all KPIs.
4. **Fizzy Lifting Drinks** has an `OTH-` product ID but is labelled "Sugar". The labelled division is kept
   and the conflict is logged.
5. **Only 15 products** exist, so Pareto "80%" thresholds are coarse (5 of 15 products).
6. **Margin volatility is effectively zero** for every product: unit price and unit cost are constant in
   this dataset, so monthly margin never moves. The metric is implemented correctly but cannot discriminate
   here.
7. **Postal codes** lost leading zeros in the export; US codes were padded to 5 digits (449 rows).

## Headline findings (default settings, full date range)
- Portfolio: Sales $141,784 · Gross Profit $93,443 · Gross Margin 65.9% · Profit per unit $2.42
- Chocolate = 92.9% of revenue and 95.1% of profit; Sugar is 0.3% of revenue.
- Five products produce 80% of both revenue and profit; the top five hold 95% of gross profit (over-dependency).
- Reprice (margin < 50%): Kazookles (7.7%), Fun Dip (40%), Nerds (46.7%), SweeTARTS (46.7%).
- Cost renegotiation: Kazookles (cost is 92% of sales on 371 units).
- Discontinuation review: Laffy Taffy, SweeTARTS, Nerds, Fun Dip (bottom-quartile sales and profit).
- Pricing inefficiency: Fun Dip has unit cost within 11% of Nutty Crunch and Hair Toffee but a 31–38 pp lower margin.
