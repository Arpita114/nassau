"""Independent KPI audit (PRD §12): recomputes headline numbers from the RAW csv with
plain pandas (no app code) and checks them against the app's metrics module."""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import config, metrics  # noqa: E402
from src.data_loading import load_clean  # noqa: E402

failures = []


def check(name, a, b, tol=1e-6):
    ok = abs(a - b) <= tol * max(1, abs(a))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: independent={a:,.4f} app={b:,.4f}")
    if not ok:
        failures.append(name)


raw = pd.read_csv(config.RAW_CSV)
df, _ = load_clean(config.RAW_CSV)
kpi = metrics.kpi_summary(df)
check("Total Sales", raw["Sales"].sum(), kpi["total_sales"])
check("Total Gross Profit", raw["Gross Profit"].sum(), kpi["total_gp"])
check("Gross Margin %", raw["Gross Profit"].sum() / raw["Sales"].sum(), kpi["gross_margin"])
check("Profit per Unit", raw["Gross Profit"].sum() / raw["Units"].sum(), kpi["profit_per_unit"])

pt = metrics.product_table(df)
ind = raw.groupby("Product Name").agg(s=("Sales", "sum"), p=("Gross Profit", "sum"))
for _, r in pt.iterrows():
    key = [k for k in ind.index if k.replace(" ", "") == r["Product Name"].replace(" ", "")]
    check(f"GP {r['Product Name']}", ind.loc[key[0], "p"], r["Gross Profit"])
check("Revenue contribution sums to 1", 1.0, pt["Revenue Contribution"].sum())
check("Profit contribution sums to 1", 1.0, pt["Profit Contribution"].sum())

# Risk-flag correctness at the default threshold (PRD §12)
flagged = metrics.risk_flags(pt, config.DEFAULT_MARGIN_THRESHOLD)
truth_low = set(pt.loc[pt["Gross Margin %"] < config.DEFAULT_MARGIN_THRESHOLD, "Product Name"])
got_low = set(flagged.loc[flagged["Flag: Reprice"], "Product Name"])
ok = truth_low == got_low
print(f"[{'PASS' if ok else 'FAIL'}] Reprice flags == products below {config.DEFAULT_MARGIN_THRESHOLD:.0%} margin: {sorted(got_low)}")
if not ok:
    failures.append("risk flags")
neg = set(pt.loc[pt["Gross Margin %"] < 0, "Product Name"])
print(f"[INFO] Negative-margin products: {sorted(neg) or 'none'}")
assert neg <= got_low, "negative-margin product not flagged"

print("\nRESULT:", "ALL CHECKS PASSED" if not failures else f"FAILURES: {failures}")
sys.exit(1 if failures else 0)
