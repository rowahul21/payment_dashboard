"""
utils/charts.py
───────────────
Reusable Plotly chart builders for consistent visual language across pages.
All functions return a plotly.graph_objects.Figure ready for st.plotly_chart().
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import List, Optional, Tuple

# ── Design tokens ─────────────────────────────────────────────────────────────
NAVY    = "#0f2044"
BLUE    = "#1d4ed8"
TEAL    = "#0891b2"
GREEN   = "#16a34a"
AMBER   = "#d97706"
RED     = "#dc2626"
PURPLE  = "#7c3aed"
GRAY    = "#64748b"
LIGHT   = "#f8fafc"

PALETTE = [BLUE, TEAL, GREEN, AMBER, RED, PURPLE]

LAYOUT_BASE = dict(
    font=dict(family="Inter, Arial, sans-serif", size=12, color="#1e293b"),
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=40, r=20, t=48, b=40),
    legend=dict(
        orientation="h", y=-0.18, x=0,
        font=dict(size=11),
        bgcolor="rgba(0,0,0,0)",
    ),
    hovermode="x unified",
    xaxis=dict(showgrid=False, linecolor="#e2e8f0", tickfont=dict(size=11)),
    yaxis=dict(gridcolor="#f1f5f9", linecolor="#e2e8f0", tickfont=dict(size=11)),
)


def line_chart(
    df: pd.DataFrame,
    x: str,
    y_cols: List[str],
    labels: Optional[dict] = None,
    title: str = "",
    y_suffix: str = "",
    secondary_y_col: Optional[str] = None,
    secondary_label: str = "",
) -> go.Figure:
    """Multi-line chart with optional secondary Y axis."""
    fig = go.Figure()
    labels = labels or {}

    for i, col in enumerate(y_cols):
        fig.add_trace(go.Scatter(
            x=df[x], y=df[col],
            name=labels.get(col, col),
            line=dict(color=PALETTE[i % len(PALETTE)], width=2.5),
            mode="lines+markers",
            marker=dict(size=5),
            hovertemplate=f"%{{y:.1f}}{y_suffix}<extra>{labels.get(col, col)}</extra>",
        ))

    if secondary_y_col:
        fig.add_trace(go.Bar(
            x=df[x], y=df[secondary_y_col],
            name=secondary_label,
            yaxis="y2",
            marker_color=AMBER,
            opacity=0.35,
            hovertemplate="%{y:,.0f}<extra>" + secondary_label + "</extra>",
        ))
        fig.update_layout(
            yaxis2=dict(
                title=secondary_label,
                overlaying="y", side="right",
                showgrid=False,
                tickfont=dict(size=10),
            )
        )

    fig.update_layout(title=dict(text=title, font=dict(size=14, color=NAVY)), **LAYOUT_BASE)
    return fig


def bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str = None,
    title: str = "",
    color_map: dict = None,
    text_col: str = None,
    h_line: float = None,
    h_label: str = "",
    y_suffix: str = "",
) -> go.Figure:
    """Grouped or colored bar chart."""
    fig = px.bar(
        df, x=x, y=y,
        color=color,
        color_discrete_map=color_map or {},
        text=text_col,
        title=title,
    )
    if h_line is not None:
        fig.add_hline(
            y=h_line, line_dash="dash",
            line_color=NAVY, line_width=1.5,
            annotation_text=h_label,
            annotation_font_size=10,
            annotation_font_color=NAVY,
        )
    fig.update_traces(
        texttemplate=f"%{{text:.1f}}{y_suffix}" if text_col else None,
        textposition="outside",
    )
    fig.update_layout(title=dict(font=dict(size=14, color=NAVY)), **LAYOUT_BASE)
    return fig


def area_chart(
    df: pd.DataFrame,
    x: str,
    y_cols: List[str],
    labels: Optional[dict] = None,
    title: str = "",
    y_suffix: str = "",
) -> go.Figure:
    """Stacked area chart."""
    fig = go.Figure()
    labels = labels or {}

    for i, col in enumerate(y_cols):
        fig.add_trace(go.Scatter(
            x=df[x], y=df[col],
            name=labels.get(col, col),
            fill="tonexty" if i > 0 else "tozeroy",
            mode="lines",
            line=dict(color=PALETTE[i % len(PALETTE)], width=1.5),
            stackgroup="one",
            hovertemplate=f"%{{y:.2f}}{y_suffix}<extra>{labels.get(col, col)}</extra>",
        ))

    fig.update_layout(title=dict(text=title, font=dict(size=14, color=NAVY)), **LAYOUT_BASE)
    return fig


def scatter_bubble(
    df: pd.DataFrame,
    x: str, y: str, size: str, color: str,
    hover_name: str,
    title: str = "",
    x_label: str = "", y_label: str = "",
) -> go.Figure:
    """Bubble chart — useful for ASEAN comparisons."""
    fig = px.scatter(
        df, x=x, y=y,
        size=size, color=color,
        hover_name=hover_name,
        title=title,
        labels={x: x_label, y: y_label},
        color_discrete_sequence=PALETTE,
        size_max=60,
    )
    fig.update_layout(title=dict(font=dict(size=14, color=NAVY)), **LAYOUT_BASE)
    return fig


def choropleth_map(
    df: pd.DataFrame,
    lat: str, lon: str,
    color_col: str,
    hover_name: str,
    hover_data: List[str],
    title: str = "",
    color_scale: str = "Blues",
    zoom: float = 4.0,
) -> go.Figure:
    """
    Scatter-mapbox choropleth using province centroids.
    Uses OpenStreetMap tiles (no token required).

    For a true polygon choropleth, replace with:
        px.choropleth_mapbox(geojson=indonesia_geojson, ...)
    and load the GeoJSON from:
        https://github.com/superpikar/indonesia-geojson
    """
    fig = px.scatter_mapbox(
        df,
        lat=lat, lon=lon,
        color=color_col,
        size=color_col,
        hover_name=hover_name,
        hover_data=hover_data,
        title=title,
        color_continuous_scale=color_scale,
        size_max=40,
        zoom=zoom,
        center={"lat": -2.5, "lon": 118},
        mapbox_style="open-street-map",
    )
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=NAVY)),
        margin=dict(l=0, r=0, t=48, b=0),
        coloraxis_colorbar=dict(
            title=color_col.replace("_", " ").title(),
            thickness=14, len=0.6,
            tickfont=dict(size=10),
        ),
        paper_bgcolor="white",
        font=dict(family="Inter, Arial, sans-serif"),
    )
    return fig


def gauge_chart(value: float, title: str, max_val: float = 100) -> go.Figure:
    """Single gauge for summary risk/score display."""
    if value >= 75:
        bar_color = GREEN
    elif value >= 50:
        bar_color = AMBER
    else:
        bar_color = RED

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        title={"text": title, "font": {"size": 13, "color": NAVY}},
        number={"font": {"size": 28, "color": NAVY}},
        gauge={
            "axis": {"range": [0, max_val], "tickwidth": 1, "tickfont": {"size": 10}},
            "bar": {"color": bar_color, "thickness": 0.25},
            "bgcolor": "white",
            "borderwidth": 0,
            "steps": [
                {"range": [0, max_val * 0.4], "color": "#fee2e2"},
                {"range": [max_val * 0.4, max_val * 0.7], "color": "#fef9c3"},
                {"range": [max_val * 0.7, max_val], "color": "#dcfce7"},
            ],
            "threshold": {
                "line": {"color": NAVY, "width": 2},
                "thickness": 0.75,
                "value": value,
            },
        },
    ))
    fig.update_layout(
        margin=dict(l=20, r=20, t=60, b=20),
        paper_bgcolor="white",
        height=200,
    )
    return fig


def waterfall_chart(
    categories: List[str],
    values: List[float],
    title: str = "",
) -> go.Figure:
    """Waterfall chart showing contribution breakdown."""
    fig = go.Figure(go.Waterfall(
        name="", orientation="v",
        measure=["relative"] * (len(values) - 1) + ["total"],
        x=categories,
        y=values,
        connector={"line": {"color": "#e2e8f0"}},
        increasing={"marker": {"color": GREEN}},
        decreasing={"marker": {"color": RED}},
        totals={"marker": {"color": BLUE}},
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=NAVY)),
        **LAYOUT_BASE
    )
    return fig
