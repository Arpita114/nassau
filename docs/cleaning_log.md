# Cleaning Log

- Raw rows: **10,194**
- Clean rows: **10,194**
- Rows removed: **0**

| # | Step | Rule | Rows affected | Action |
|---|------|------|---------------|--------|
| 1 | Type check | Sales, Units, Gross Profit, Cost must be numeric | 0 | Dropped non-numeric rows |
| 2 | Date parse | Order Date parsed as DD-MM-YYYY | 0 | Dropped unparseable order dates |
| 3 | DQ-1 | Sales and Cost must be non-negative | 0 | Dropped |
| 4 | DQ-2a | Sales must be > 0 | 0 | Dropped zero-sales records |
| 5 | DQ-2b | Gross Profit must not exceed Sales | 0 | Dropped invalid-profit records |
| 6 | DQ-3 | Units missing or <= 0 | 0 | None needed (0 imputed) |
| 7 | DQ-4 | Trim/collapse whitespace in 'Division' | 0 | Standardised |
| 8 | DQ-4 | Trim/collapse whitespace in 'Region' | 0 | Standardised |
| 9 | DQ-4 | Trim/collapse whitespace in 'Ship Mode' | 0 | Standardised |
| 10 | DQ-4 | Trim/collapse whitespace in 'Country/Region' | 0 | Standardised |
| 11 | DQ-4 | Trim/collapse whitespace in 'State/Province' | 0 | Standardised |
| 12 | DQ-4 | Trim/collapse whitespace in 'City' | 0 | Standardised |
| 13 | DQ-4 | Trim/collapse whitespace in 'Product ID' | 0 | Standardised |
| 14 | DQ-4 | Standardise product names (hyphen spacing) | 2,064 | e.g. 'Wonka Bar -Scrumdiddlyumptious' -> 'Wonka Bar - Scrumdiddlyumptious' |
| 15 | DQ-4 | Pad US postal codes to 5 digits | 449 | Leading zeros restored |
| 16 | DQ-5 | Gross Profit = Sales - Cost (tolerance 0.01) | 0 | Flagged in column gp_identity_ok (rows kept; reported GP used) |
| 17 | Audit | Ship lag outside 0-30 days (implausible for candy distribution) | 10,194 | Flagged in ship_date_suspect; excluded from every KPI (ship dates not used) |
| 18 | Audit | Division label disagrees with Product ID prefix | 6 | Kept the labelled division; conflicting products: Fizzy Lifting Drinks |
