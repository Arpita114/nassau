"""Streamlit entry point: Nassau Candy Product Line Profitability & Margin Performance Analysis."""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src import charts, config, metrics  # noqa: E402
from src.data_loading import load_clean  # noqa: E402

st.set_page_config(page_title="Nassau Candy Profitability", page_icon="🍬", layout="wide")


@st.cache_data(show_spinner="Cleaning and validating order data…")
def get_data():
    df, rep = load_clean(config.RAW_CSV)
    return df, rep


def csv_button(df: pd.DataFrame, label: str, name: str, key: str):
    st.download_button(label, df.to_csv(index=False).encode("utf-8"), file_name=name,
                       mime="text/csv", key=key)


def fmt_money(x):
    return f"${x:,.0f}"


df_all, cleaning = get_data()
st.title(config.APP_TITLE)

# ---------------- Global controls (sidebar) ----------------
st.sidebar.title("Navigation")
module = st.sidebar.radio("Module", [
    "1 · Product Profitability",
    "2 · Division Performance",
    "3 · Cost vs Margin Diagnostics",
    "4 · Profit Concentration",
    "Data & Cleaning Log",
], label_visibility="collapsed")

st.sidebar.divider()
st.sidebar.header("Global controls")
min_d, max_d = df_all["Order Date"].min().date(), df_all["Order Date"].max().date()
date_range = st.sidebar.date_input("Order date range", value=(min_d, max_d),
                                   min_value=min_d, max_value=max_d)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = date_range
else:
    start, end = min_d, max_d

divisions = sorted(df_all["Division"].unique())
sel_div = st.sidebar.multiselect("Division", divisions, default=divisions)
margin_thr = st.sidebar.slider("Margin threshold (gross margin %)", 0, 100,
                               int(config.DEFAULT_MARGIN_THRESHOLD * 100), 1) / 100
search = st.sidebar.text_input("Product search (fuzzy)", placeholder="e.g. wonka bar, gobstopper")

# Apply filters
mask = (df_all["Order Date"].dt.date >= start) & (df_all["Order Date"].dt.date <= end) \
       & df_all["Division"].isin(sel_div)
df = df_all[mask].copy()
name_hit = metrics.product_search(df["Product Name"], search)
df = df[name_hit.values] if not df.empty else df

if df.empty:
    st.warning("No records match the current filters. Widen the date range or division selection.")
    st.stop()

pt_base = metrics.product_table(df)
kpi = metrics.kpi_summary(df)
pt = metrics.classify_quadrants(pt_base, kpi["gross_margin"])
pt = metrics.risk_flags(pt, margin_thr)
n_flagged = int(pt["Flagged"].sum())

# ---------------- KPI header strip ----------------
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Sales", fmt_money(kpi["total_sales"]))
c2.metric("Total Gross Profit", fmt_money(kpi["total_gp"]))
c3.metric("Avg Gross Margin %", f"{kpi['gross_margin']:.1%}")
c4.metric("Profit per Unit", f"${kpi['profit_per_unit']:.2f}")
c5.metric("# Flagged Products", f"{n_flagged} of {len(pt)}")
st.caption(f"Filtered records: {len(df):,} of {len(df_all):,} · Products: {len(pt)} · "
           f"Margin threshold: {margin_thr:.0%}")

# ---------------- Module 1 ----------------
if module.startswith("1"):
    st.header("Module 1 · Product Profitability Overview")
    sort_by = st.selectbox("Sort leaderboard by", ["Gross Profit", "Gross Margin %", "Profit per Unit", "Sales"])
    show = pt.sort_values(sort_by, ascending=False)
    cols = ["Product Name", "Division", "Units", "Sales", "Gross Profit", "Gross Margin %",
            "Profit per Unit", "Revenue Contribution", "Profit Contribution", "Margin Volatility", "Quadrant"]
    st.subheader("Margin leaderboard")
    st.dataframe(show[cols], hide_index=True, width="stretch",
                 column_config={
                     "Sales": st.column_config.NumberColumn(format="$%.2f"),
                     "Gross Profit": st.column_config.NumberColumn(format="$%.2f"),
                     "Gross Margin %": st.column_config.NumberColumn(format="%.1f%%"),
                     "Profit per Unit": st.column_config.NumberColumn(format="$%.3f"),
                     "Revenue Contribution": st.column_config.NumberColumn(format="%.2f%%"),
                     "Profit Contribution": st.column_config.NumberColumn(format="%.2f%%"),
                     "Margin Volatility": st.column_config.NumberColumn(format="%.3f"),
                 })
    csv_button(show[cols], "Download leaderboard (CSV)", "product_leaderboard.csv", "dl_m1")
    st.caption("Margin Volatility = std. dev. of monthly gross margin per product (blank = fewer than 2 months).")

    left, right = st.columns(2)
    with left:
        st.subheader("Profit contribution")
        st.plotly_chart(charts.profit_contribution_bar(pt), width="stretch")
    with right:
        st.subheader("Margin % by product")
        st.plotly_chart(charts.margin_bar(pt, "Gross Margin %"), width="stretch")
    st.subheader("Quadrant map: sales vs. margin")
    st.plotly_chart(charts.quadrant_scatter(pt, kpi["gross_margin"]), width="stretch")
    st.caption("Quadrants: High-Sales = product sales ≥ median product sales; High-Margin = margin ≥ portfolio margin.")

# ---------------- Module 2 ----------------
elif module.startswith("2"):
    st.header("Module 2 · Division Performance")
    div = metrics.division_table(df)
    st.subheader("Division KPIs")
    st.dataframe(div, hide_index=True, width="stretch",
                 column_config={
                     "Sales": st.column_config.NumberColumn(format="$%.0f"),
                     "Gross Profit": st.column_config.NumberColumn(format="$%.0f"),
                     "Gross Margin %": st.column_config.NumberColumn(format="%.1f%%"),
                     "Profit per Unit": st.column_config.NumberColumn(format="$%.3f"),
                     "Revenue Share": st.column_config.NumberColumn(format="%.1f%%"),
                     "Profit Share": st.column_config.NumberColumn(format="%.1f%%"),
                     "Share Gap (pp)": st.column_config.NumberColumn(format="%+.1f"),
                 })
    csv_button(div, "Download division KPIs (CSV)", "division_kpis.csv", "dl_m2")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Revenue share vs. profit share")
        st.plotly_chart(charts.division_share_bar(div), width="stretch")
    with c2:
        st.subheader("Margin distribution by division (order lines)")
        st.plotly_chart(charts.margin_box(df), width="stretch")

    st.subheader("Factory rollup")
    fac = metrics.factory_table(df)
    st.plotly_chart(charts.factory_map(fac), width="stretch")
    st.dataframe(fac, hide_index=True, width="stretch")
    csv_button(fac, "Download factory rollup (CSV)", "factory_rollup.csv", "dl_m2f")
    st.info("The dataset has no factory column. Sales are allocated equally across the factories the PRD "
            "maps to each division (Chocolate → 2 factories; Sugar and Other → 3). Coordinates are approximate.")

# ---------------- Module 3 ----------------
elif module.startswith("3"):
    st.header("Module 3 · Cost vs. Margin Diagnostics")
    st.subheader("Cost vs. sales (size = units, colour = division)")
    st.plotly_chart(charts.cost_sales_scatter(pt), width="stretch")

    st.subheader(f"Margin risk flags (margin threshold {margin_thr:.0%})")
    st.markdown("🔴 **Reprice**: margin below threshold · 🟠 **Cost renegotiation**: Cost/Sales ≥ "
                f"{config.COST_RATIO_THRESHOLD:.0%} with healthy volume · ⚫ **Discontinuation review**: "
                "bottom-quartile sales AND (bottom-quartile profit OR margin below threshold)")
    flag_cols = ["Product Name", "Division", "Sales", "Gross Profit", "Gross Margin %", "Cost Ratio",
                 "Units", "Flags"]
    flagged = pt[pt["Flagged"]].sort_values("Gross Margin %")
    if flagged.empty:
        st.success("No products flagged at this threshold.")
    else:
        st.dataframe(flagged[flag_cols], hide_index=True, width="stretch",
                     column_config={"Gross Margin %": st.column_config.NumberColumn(format="%.1f%%"),
                                    "Cost Ratio": st.column_config.NumberColumn(format="%.1f%%")})
        csv_button(flagged[flag_cols], "Download flagged products (CSV)", "risk_flags.csv", "dl_m3")
    with st.expander("All products with flags"):
        st.dataframe(pt[flag_cols], hide_index=True, width="stretch")

    st.subheader("Pricing inefficiency: similar unit cost, divergent margin")
    pi = metrics.pricing_inefficiency(pt)
    if pi.empty:
        st.info("No product pairs meet the similar-cost / divergent-margin criteria at current settings.")
    else:
        st.dataframe(pi, hide_index=True, width="stretch")
        csv_button(pi, "Download pricing inefficiency pairs (CSV)", "pricing_inefficiency.csv", "dl_m3p")

# ---------------- Module 4 ----------------
elif module.startswith("4"):
    st.header("Module 4 · Profit Concentration")
    n_rev = metrics.products_for_share(pt, "Sales")
    n_prof = metrics.products_for_share(pt, "Gross Profit")
    top5_prof = metrics.top_n_share(pt, "Gross Profit", 5)
    top5_rev = metrics.top_n_share(pt, "Sales", 5)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Products → 80% of revenue", f"{n_rev['n']} of {len(pt)}", f"{n_rev['pct']:.0%} of products")
    c2.metric("Products → 80% of profit", f"{n_prof['n']} of {len(pt)}", f"{n_prof['pct']:.0%} of products")
    c3.metric("Top-5 share of profit", f"{top5_prof:.1%}")
    c4.metric("Top-5 share of revenue", f"{top5_rev:.1%}")
    if top5_prof >= 0.5:
        st.warning(f"Over-dependency: the top 5 products hold {top5_prof:.0%} of gross profit. "
                   "A high Pareto share is a concentration risk, not a sign of safety.")
    st.caption(f"Only {len(pt)} products exist in the dataset, so the 80% cut-off is coarse. "
               "Read these figures alongside the dependency indicator.")

    p_rev = metrics.pareto(pt, "Sales")
    p_prof = metrics.pareto(pt, "Gross Profit")
    st.plotly_chart(charts.pareto_chart(p_rev, "Sales", "Pareto: revenue by product"), width="stretch")
    st.plotly_chart(charts.pareto_chart(p_prof, "Gross Profit", "Pareto: gross profit by product"), width="stretch")
    csv_button(p_prof, "Download profit Pareto (CSV)", "profit_pareto.csv", "dl_m4")

    st.subheader("Geographic profitability (state / province)")
    st_df = metrics.state_table(df)
    st.plotly_chart(charts.state_bar(st_df), width="stretch")
    st.dataframe(st_df, hide_index=True, width="stretch",
                 column_config={"Gross Margin %": st.column_config.NumberColumn(format="%.1f%%"),
                                "Profit Share": st.column_config.NumberColumn(format="%.2f%%")})
    csv_button(st_df, "Download state profitability (CSV)", "state_profitability.csv", "dl_m4s")

# ---------------- Data & cleaning ----------------
else:
    st.header("Data & Cleaning Log")
    st.markdown(cleaning.to_markdown())
    st.subheader("Cleaned dataset preview")
    st.dataframe(df_all.head(200), hide_index=True, width="stretch")
    csv_button(df_all, "Download cleaned dataset (CSV)", "nassau_candy_clean.csv", "dl_clean")
