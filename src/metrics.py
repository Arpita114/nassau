"""KPI definitions (PRD §8), risk flags (§6 Module 3) and concentration analysis (§6 Module 4)."""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from . import config


def kpi_summary(df: pd.DataFrame) -> dict:
    sales = df["Sales"].sum()
    gp = df["Gross Profit"].sum()
    units = df["Units"].sum()
    return {
        "total_sales": sales,
        "total_gp": gp,
        "gross_margin": gp / sales if sales else np.nan,
        "profit_per_unit": gp / units if units else np.nan,
        "units": units,
        "orders": df["Order ID"].nunique(),
    }


def product_table(df: pd.DataFrame) -> pd.DataFrame:
    """One row per product with all product-level KPIs."""
    if df.empty:
        return pd.DataFrame()
    g = df.groupby(["Product ID", "Product Name", "Division"], as_index=False).agg(
        Units=("Units", "sum"), Sales=("Sales", "sum"), Cost=("Cost", "sum"),
        **{"Gross Profit": ("Gross Profit", "sum"), "Order Lines": ("Row ID", "count")},
    )
    total_sales = g["Sales"].sum()
    total_gp = g["Gross Profit"].sum()
    g["Gross Margin %"] = g["Gross Profit"] / g["Sales"]
    g["Profit per Unit"] = g["Gross Profit"] / g["Units"]
    g["Unit Cost"] = g["Cost"] / g["Units"]
    g["Cost Ratio"] = g["Cost"] / g["Sales"]
    g["Revenue Contribution"] = g["Sales"] / total_sales
    g["Profit Contribution"] = g["Gross Profit"] / total_gp if total_gp else np.nan

    # Margin Volatility: std. dev. of monthly gross margin per product (PRD §8)
    monthly = (df.groupby(["Product ID", "Year-Month"])
                 .agg(s=("Sales", "sum"), p=("Gross Profit", "sum")).reset_index())
    monthly["m"] = monthly["p"] / monthly["s"]
    vol = monthly.groupby("Product ID")["m"].agg(["std", "count"])
    vol.loc[vol["count"] < 2, "std"] = np.nan
    g["Margin Volatility"] = g["Product ID"].map(vol["std"])
    g["Months Observed"] = g["Product ID"].map(vol["count"]).fillna(0).astype(int)
    return g.sort_values("Gross Profit", ascending=False).reset_index(drop=True)


def classify_quadrants(pt: pd.DataFrame, portfolio_margin: float) -> pd.DataFrame:
    """PRD FR-1.2 quadrant labels. High sales = at/above median product sales;
    high margin = at/above portfolio gross margin."""
    if pt.empty:
        return pt.assign(Quadrant=pd.Series(dtype=str))
    hs = pt["Sales"] >= pt["Sales"].median()
    hm = pt["Gross Margin %"] >= portfolio_margin
    labels = np.select(
        [hs & hm, hs & ~hm, ~hs & ~hm, ~hs & hm],
        ["High-Profit / High-Margin", "High-Sales / Low-Margin",
         "Low-Sales / Low-Profit", "High-Margin / Low-Volume (Hidden Gem)"],
        default="Unclassified",
    )
    return pt.assign(Quadrant=labels)


def risk_flags(pt: pd.DataFrame, margin_threshold: float) -> pd.DataFrame:
    """PRD FR-3.2. Returns product table with boolean flags and a text summary."""
    if pt.empty:
        return pt
    out = pt.copy()
    out["Flag: Reprice"] = out["Gross Margin %"] < margin_threshold
    healthy_units = out["Units"] >= out["Units"].quantile(config.HEALTHY_VOLUME_QUANTILE)
    out["Flag: Cost Renegotiation"] = (out["Cost Ratio"] >= config.COST_RATIO_THRESHOLD) & healthy_units
    low_sales = out["Sales"] <= out["Sales"].quantile(config.LOW_SALES_QUANTILE)
    low_profit = (out["Gross Profit"] <= out["Gross Profit"].quantile(config.LOW_SALES_QUANTILE)) | \
                 (out["Gross Margin %"] < margin_threshold)
    out["Flag: Discontinuation Review"] = low_sales & low_profit
    out["Flags"] = out.apply(lambda r: " ".join(
        s for s, on in [("🔴 Reprice", r["Flag: Reprice"]),
                        ("🟠 Cost renegotiation", r["Flag: Cost Renegotiation"]),
                        ("⚫ Discontinuation review", r["Flag: Discontinuation Review"])] if on), axis=1)
    out["Flagged"] = out[["Flag: Reprice", "Flag: Cost Renegotiation", "Flag: Discontinuation Review"]].any(axis=1)
    return out


def pricing_inefficiency(pt: pd.DataFrame) -> pd.DataFrame:
    """FR-3.3: product pairs with similar unit cost (within tolerance) but margins
    differing by at least the configured gap."""
    rows = []
    recs = pt[["Product Name", "Unit Cost", "Gross Margin %", "Sales"]].to_dict("records")
    for a, b in itertools.combinations(recs, 2):
        hi, lo = (a, b) if a["Unit Cost"] >= b["Unit Cost"] else (b, a)
        if lo["Unit Cost"] <= 0:
            continue
        cost_gap = hi["Unit Cost"] / lo["Unit Cost"] - 1
        margin_gap = abs(a["Gross Margin %"] - b["Gross Margin %"])
        if cost_gap <= config.PRICING_COST_TOL and margin_gap >= config.PRICING_MARGIN_GAP:
            rows.append({
                "Product A": a["Product Name"], "Product B": b["Product Name"],
                "Unit cost A": round(a["Unit Cost"], 2), "Unit cost B": round(b["Unit Cost"], 2),
                "Unit cost gap %": round(cost_gap * 100, 1),
                "Margin A %": round(a["Gross Margin %"] * 100, 1),
                "Margin B %": round(b["Gross Margin %"] * 100, 1),
                "Margin gap (pp)": round(margin_gap * 100, 1),
            })
    return pd.DataFrame(rows)


def pareto(pt: pd.DataFrame, value_col: str) -> pd.DataFrame:
    """Products sorted descending by value_col with cumulative share."""
    s = pt.sort_values(value_col, ascending=False).reset_index(drop=True).copy()
    total = s[value_col].sum()
    s["Share"] = s[value_col] / total if total else np.nan
    s["Cumulative Share"] = s["Share"].cumsum()
    s["Cumulative % of Products"] = (np.arange(1, len(s) + 1)) / len(s)
    return s[["Product Name", value_col, "Share", "Cumulative Share", "Cumulative % of Products"]]


def products_for_share(pt: pd.DataFrame, value_col: str, share: float = 0.8) -> dict:
    """FR-4.2: minimum number (and %) of products reaching `share` of the total."""
    p = pareto(pt, value_col)
    if p.empty or p[value_col].sum() <= 0:
        return {"n": 0, "pct": np.nan}
    n = int((p["Cumulative Share"] < share).sum() + 1)
    n = min(n, len(p))
    return {"n": n, "pct": n / len(p)}


def top_n_share(pt: pd.DataFrame, value_col: str, n: int = 5) -> float:
    """FR-4.3: share of total held by the top-n products (over-dependency indicator)."""
    total = pt[value_col].sum()
    return float(pt[value_col].nlargest(n).sum() / total) if total else np.nan


def division_table(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("Division", as_index=False).agg(
        Sales=("Sales", "sum"), **{"Gross Profit": ("Gross Profit", "sum")}, Units=("Units", "sum"),
        Products=("Product ID", "nunique"))
    g["Gross Margin %"] = g["Gross Profit"] / g["Sales"]
    g["Profit per Unit"] = g["Gross Profit"] / g["Units"]
    g["Revenue Share"] = g["Sales"] / g["Sales"].sum()
    g["Profit Share"] = g["Gross Profit"] / g["Gross Profit"].sum()
    g["Share Gap (pp)"] = (g["Profit Share"] - g["Revenue Share"]) * 100
    return g.sort_values("Sales", ascending=False).reset_index(drop=True)


def factory_table(df: pd.DataFrame) -> pd.DataFrame:
    """FR-2.4. The dataset has no factory column, so each product's sales are
    allocated EQUALLY across the factories that the PRD maps to its division."""
    rows = []
    for name, meta in config.FACTORIES.items():
        sub = df[df["Division"].isin(meta["divisions"])]
        n_share = sub.groupby("Division")["Product ID"].nunique()
        # equal split across factories sharing the division
        alloc_factor = {d: 1 / sum(d in f["divisions"] for f in config.FACTORIES.values())
                        for d in meta["divisions"]}
        s = sub["Sales"] * sub["Division"].map(alloc_factor)
        p = sub["Gross Profit"] * sub["Division"].map(alloc_factor)
        rows.append({
            "Factory": name, "State": meta["state"], "Lat": meta["lat"], "Lon": meta["lon"],
            "Divisions": ", ".join(meta["divisions"]),
            "Products (mapped)": int(n_share.sum()),
            "Allocated Sales": float(s.sum()), "Allocated Gross Profit": float(p.sum()),
        })
    out = pd.DataFrame(rows)
    total_s = out["Allocated Sales"].sum()
    out["Allocated Gross Margin %"] = out["Allocated Gross Profit"] / out["Allocated Sales"].replace(0, np.nan)
    out["Sales Share"] = out["Allocated Sales"] / total_s if total_s else np.nan
    return out


def state_table(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["Country/Region", "State/Province"], as_index=False).agg(
        Sales=("Sales", "sum"), **{"Gross Profit": ("Gross Profit", "sum")}, Units=("Units", "sum"),
        Orders=("Order ID", "nunique"))
    g["Gross Margin %"] = g["Gross Profit"] / g["Sales"]
    g["Profit Share"] = g["Gross Profit"] / g["Gross Profit"].sum()
    return g.sort_values("Gross Profit", ascending=False).reset_index(drop=True)


def product_search(names: pd.Series, query: str) -> pd.Series:
    """Fuzzy (token-set) match against product names; empty query matches everything."""
    if not query or not query.strip():
        return pd.Series(True, index=names.index)
    from rapidfuzz import fuzz
    q = query.strip().lower()
    scores = names.astype(str).str.lower().map(lambda n: max(fuzz.partial_ratio(q, n), fuzz.token_set_ratio(q, n)))
    return scores >= config.PRODUCT_SEARCH_CUTOFF
