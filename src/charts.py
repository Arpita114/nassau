"""Plotly chart builders (all charts use Plotly per PRD §10)."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

PALETTE = px.colors.qualitative.Safe


def margin_bar(pt, sort_col: str):
    d = pt.sort_values(sort_col, ascending=True)
    fig = px.bar(d, x=sort_col, y="Product Name", orientation="h", color="Gross Margin %",
                 color_continuous_scale="RdYlGn", range_color=(0, 1),
                 hover_data={"Gross Margin %": ":.1%", "Sales": ":,.0f", "Units": True},
                 labels={sort_col: sort_col})
    fig.update_layout(height=max(380, 28 * len(d) + 120), margin=dict(l=10, r=10, t=40, b=10))
    return fig


def quadrant_scatter(pt, portfolio_margin: float):
    fig = px.scatter(pt, x="Sales", y="Gross Margin %", size="Units", color="Quadrant",
                     hover_name="Product Name", text="Product Name", size_max=45,
                     hover_data={"Gross Profit": ":,.0f", "Profit per Unit": ":.2f"})
    fig.add_hline(y=portfolio_margin, line_dash="dash", annotation_text="Portfolio margin")
    fig.add_vline(x=pt["Sales"].median(), line_dash="dot", annotation_text="Median sales")
    fig.update_traces(textposition="top center", textfont_size=10)
    fig.update_layout(yaxis_tickformat=".0%", height=520, margin=dict(l=10, r=10, t=40, b=10))
    return fig


def profit_contribution_bar(pt):
    d = pt.sort_values("Gross Profit", ascending=False)
    fig = px.bar(d, x="Product Name", y="Gross Profit", color="Division",
                 hover_data={"Profit Contribution": ":.1%"})
    fig.update_layout(height=430, xaxis_tickangle=-40, margin=dict(l=10, r=10, t=40, b=120))
    return fig


def pareto_chart(p: pd.DataFrame, value_col: str, title: str, threshold: float = 0.8):
    fig = go.Figure()
    fig.add_bar(x=p["Product Name"], y=p[value_col], name=value_col, marker_color="#4C78A8")
    fig.add_scatter(x=p["Product Name"], y=p["Cumulative Share"], name="Cumulative share",
                    yaxis="y2", mode="lines+markers", line=dict(color="#E45756"))
    fig.add_hline(y=threshold, yref="y2", line_dash="dash", annotation_text=f"{int(threshold*100)}%")
    fig.update_layout(
        title=title, height=460, xaxis_tickangle=-40, margin=dict(l=10, r=10, t=60, b=120),
        yaxis=dict(title=value_col), yaxis2=dict(title="Cumulative share", overlaying="y", side="right",
                                                 range=[0, 1.05], tickformat=".0%"),
        legend=dict(orientation="h", y=1.12))
    return fig


def division_share_bar(div):
    long = div.melt(id_vars="Division", value_vars=["Revenue Share", "Profit Share"],
                    var_name="Metric", value_name="Share")
    fig = px.bar(long, x="Division", y="Share", color="Metric", barmode="group",
                 text=long["Share"].map(lambda v: f"{v:.1%}"))
    fig.update_layout(yaxis_tickformat=".0%", height=400, margin=dict(l=10, r=10, t=40, b=10))
    return fig


def margin_box(df):
    fig = px.box(df, x="Division", y="Gross Margin %", color="Division", points="outliers",
                 hover_data=["Product Name"])
    fig.update_layout(yaxis_tickformat=".0%", height=420, showlegend=False,
                      margin=dict(l=10, r=10, t=40, b=10))
    return fig


def cost_sales_scatter(pt):
    fig = px.scatter(pt, x="Sales", y="Cost", size="Units", color="Division",
                     hover_name="Product Name", size_max=50,
                     hover_data={"Gross Margin %": ":.1%", "Cost Ratio": ":.1%"})
    mx = max(pt["Sales"].max(), pt["Cost"].max()) * 1.05 if len(pt) else 1
    fig.add_scatter(x=[0, mx], y=[0, mx], mode="lines", line=dict(dash="dot", color="grey"),
                    name="Cost = Sales (0% margin)", showlegend=True)
    fig.update_layout(height=520, margin=dict(l=10, r=10, t=40, b=10))
    return fig


def factory_map(fac):
    fig = px.scatter_map(fac, lat="Lat", lon="Lon", size="Allocated Sales", color="Allocated Gross Margin %",
                         hover_name="Factory", color_continuous_scale="RdYlGn",
                         hover_data={"State": True, "Divisions": True, "Allocated Sales": ":,.0f",
                                     "Lat": False, "Lon": False},
                         size_max=40, zoom=2.6, center=dict(lat=39, lon=-95), height=480)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    return fig


def state_bar(st_df, n=15):
    d = st_df.sort_values("Gross Margin %")
    d = pd.concat([d.head(n), d.tail(n)]).drop_duplicates()
    fig = px.bar(d, x="Gross Margin %", y="State/Province", color="Country/Region", orientation="h",
                 hover_data={"Sales": ":,.0f", "Gross Profit": ":,.0f"})
    fig.update_layout(xaxis_tickformat=".0%", height=max(400, 22 * len(d) + 120),
                      margin=dict(l=10, r=10, t=40, b=10))
    return fig
