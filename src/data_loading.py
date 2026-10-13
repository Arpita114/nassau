"""Cleaning & validation pipeline (PRD §7.3, DQ-1..DQ-5).

Every step records how many rows it touched so the cleaning log is generated
from the same run that produced the cleaned data (reproducibility).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import config

REQUIRED_COLUMNS = [
    "Row ID", "Order ID", "Order Date", "Ship Date", "Ship Mode", "Customer ID",
    "Country/Region", "City", "State/Province", "Postal Code", "Division", "Region",
    "Product ID", "Product Name", "Sales", "Units", "Gross Profit", "Cost",
]
GP_TOLERANCE = 0.01


@dataclass
class CleaningReport:
    steps: list[dict] = field(default_factory=list)
    raw_rows: int = 0
    clean_rows: int = 0

    def add(self, step: str, rule: str, affected: int, action: str) -> None:
        self.steps.append({"step": step, "rule": rule, "rows_affected": int(affected), "action": action})

    def to_markdown(self) -> str:
        lines = [
            "# Cleaning Log",
            "",
            f"- Raw rows: **{self.raw_rows:,}**",
            f"- Clean rows: **{self.clean_rows:,}**",
            f"- Rows removed: **{self.raw_rows - self.clean_rows:,}**",
            "",
            "| # | Step | Rule | Rows affected | Action |",
            "|---|------|------|---------------|--------|",
        ]
        for i, s in enumerate(self.steps, 1):
            lines.append(f"| {i} | {s['step']} | {s['rule']} | {s['rows_affected']:,} | {s['action']} |")
        return "\n".join(lines) + "\n"


def _clean_label(s: pd.Series) -> pd.Series:
    """Trim and collapse internal whitespace."""
    return s.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)


def _normalise_product_name(name: str) -> str:
    # "Wonka Bar -Scrumdiddlyumptious" -> "Wonka Bar - Scrumdiddlyumptious"
    name = re.sub(r"\s*-\s*", " - ", name)
    return config.PRODUCT_NAME_OVERRIDES.get(name, name)


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, CleaningReport]:
    rep = CleaningReport(raw_rows=len(raw))
    df = raw.copy()
    df.columns = [c.strip() for c in df.columns]
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Input is missing required columns: {missing_cols}")
    df = df[REQUIRED_COLUMNS]

    # --- Types -------------------------------------------------------------
    for c in ["Sales", "Units", "Gross Profit", "Cost"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    bad_num = df[["Sales", "Units", "Gross Profit", "Cost"]].isna().any(axis=1)
    rep.add("Type check", "Sales, Units, Gross Profit, Cost must be numeric", bad_num.sum(),
            "Dropped non-numeric rows")
    df = df[~bad_num].copy()

    df["Order Date"] = pd.to_datetime(df["Order Date"], format="%d-%m-%Y", errors="coerce")
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], format="%d-%m-%Y", errors="coerce")
    bad_date = df["Order Date"].isna()
    rep.add("Date parse", "Order Date parsed as DD-MM-YYYY", bad_date.sum(), "Dropped unparseable order dates")
    df = df[~bad_date].copy()

    # --- DQ-1: non-negative sales/cost ------------------------------------
    neg = (df["Sales"] < 0) | (df["Cost"] < 0)
    rep.add("DQ-1", "Sales and Cost must be non-negative", neg.sum(), "Dropped")
    df = df[~neg].copy()

    # --- DQ-2: zero-sales or invalid profit -------------------------------
    zero_sales = df["Sales"] == 0
    rep.add("DQ-2a", "Sales must be > 0", zero_sales.sum(), "Dropped zero-sales records")
    df = df[~zero_sales].copy()
    # Invalid profit: gross profit above sales (impossible at a positive cost)
    bad_profit = df["Gross Profit"] > df["Sales"]
    rep.add("DQ-2b", "Gross Profit must not exceed Sales", bad_profit.sum(), "Dropped invalid-profit records")
    df = df[~bad_profit].copy()

    # --- DQ-3: units ------------------------------------------------------
    # Units must be a positive integer. Missing/zero units are imputed as
    # Sales / median unit price for that product (documented assumption);
    # rows where imputation is impossible are excluded.
    df["Units"] = pd.to_numeric(df["Units"], errors="coerce")
    df["units_imputed"] = False
    bad_units = df["Units"].isna() | (df["Units"] <= 0)
    if bad_units.any():
        price = (df.loc[~bad_units, "Sales"] / df.loc[~bad_units, "Units"]).groupby(df["Product ID"]).median()
        implied = df.loc[bad_units, "Product ID"].map(price)
        fill = (df.loc[bad_units, "Sales"] / implied).round()
        ok = fill.notna() & (fill > 0)
        df.loc[bad_units & ok, "Units"] = fill[ok]
        df.loc[bad_units & ok, "units_imputed"] = True
        rep.add("DQ-3", "Units missing or <= 0", bad_units.sum(),
                f"Imputed {int(ok.sum()):,} as Sales / product median unit price; "
                f"excluded {int((~ok).sum()):,} where no price was available")
        df = df[~(bad_units & ~ok)].copy()
    else:
        rep.add("DQ-3", "Units missing or <= 0", 0, "None needed (0 imputed)")
    df["Units"] = df["Units"].astype(int)

    # --- DQ-4: label standardisation -------------------------------------
    for c in ["Division", "Region", "Ship Mode", "Country/Region", "State/Province", "City", "Product ID"]:
        before = df[c].astype(str)
        df[c] = _clean_label(df[c])
        rep.add("DQ-4", f"Trim/collapse whitespace in '{c}'", int((before != df[c].astype(str)).sum()),
                "Standardised")
    before = df["Product Name"].astype(str)
    df["Product Name"] = _clean_label(df["Product Name"]).map(_normalise_product_name)
    rep.add("DQ-4", "Standardise product names (hyphen spacing)", int((before != df["Product Name"]).sum()),
            "e.g. 'Wonka Bar -Scrumdiddlyumptious' -> 'Wonka Bar - Scrumdiddlyumptious'")
    df["Division"] = df["Division"].str.title()

    # Postal codes lost leading zeros in the export (e.g. 01234 -> 1234); pad US codes to 5 digits.
    pc = df["Postal Code"].astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
    us = df["Country/Region"].eq("United States") & pc.str.fullmatch(r"\d{1,4}")
    pc = pc.where(~us, pc.str.zfill(5))
    rep.add("DQ-4", "Pad US postal codes to 5 digits", int(us.sum()), "Leading zeros restored")
    df["Postal Code"] = pc

    # --- DQ-5: gross profit identity -------------------------------------
    diff = (df["Sales"] - df["Cost"] - df["Gross Profit"]).abs()
    gp_mismatch = diff > GP_TOLERANCE
    rep.add("DQ-5", f"Gross Profit = Sales - Cost (tolerance {GP_TOLERANCE})", gp_mismatch.sum(),
            "Flagged in column gp_identity_ok (rows kept; reported GP used)")
    df["gp_identity_ok"] = ~gp_mismatch

    # --- Additional validation flags (not removals) ----------------------
    lag = (df["Ship Date"] - df["Order Date"]).dt.days
    ship_anom = lag.isna() | (lag < 0) | (lag > 30)
    rep.add("Audit", "Ship lag outside 0-30 days (implausible for candy distribution)", ship_anom.sum(),
            "Flagged in ship_date_suspect; excluded from every KPI (ship dates not used)")
    df["ship_date_suspect"] = ship_anom

    # Division labels that contradict the Product ID prefix (e.g. OTH-* labelled Sugar)
    prefix_map = {"CHO": "Chocolate", "SUG": "Sugar", "OTH": "Other"}
    prefix_div = df["Product ID"].str.split("-").str[0].map(prefix_map)
    conflict = prefix_div.notna() & (prefix_div != df["Division"])
    conflict_products = sorted(df.loc[conflict, "Product Name"].unique())
    rep.add("Audit", "Division label disagrees with Product ID prefix", conflict.sum(),
            "Kept the labelled division; conflicting products: " + ", ".join(conflict_products))
    df["division_conflict"] = conflict

    # --- Derived columns --------------------------------------------------
    df["Year-Month"] = df["Order Date"].dt.to_period("M").astype(str)
    df["Cost Ratio"] = df["Cost"] / df["Sales"]
    df["Gross Margin %"] = df["Gross Profit"] / df["Sales"]
    df["Profit per Unit"] = df["Gross Profit"] / df["Units"]

    df = df.sort_values(["Order Date", "Row ID"]).reset_index(drop=True)
    rep.clean_rows = len(df)
    return df, rep


def load_raw(path=config.RAW_CSV) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"Postal Code": "string", "Product ID": "string"})


def load_clean(path=config.RAW_CSV) -> tuple[pd.DataFrame, CleaningReport]:
    return clean(load_raw(path))
