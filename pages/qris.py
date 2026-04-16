"""
pages/qris.py
─────────────
QRIS & Digital Payment Surveillance — deep dive on adoption trends,
regional breakdown, growth velocity, and transaction value analysis.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data.data_loader import get_qris_data, get_qris_by_region, get_payment_system_data
from utils.metrics import compute_cagr, mom_growth, yoy_growth
from utils.charts import line_chart, bar_chart, NAVY, BLUE, GREEN, AMBER, RED, TEAL, PALETTE


def render(year_range):
    st.markdown('<div class="section-header">QRIS & Digital Payment Surveillance</div>',
                unsafe_allow_html=True)
    st.caption("Source: Bank Indonesia QRIS Statistics · BIS CPMI Red Book")

    qris = get_qris_data()
    region = get_qris_by_region()
    ps = get_payment_system_data()

    # Filter
    qris_f = qris[
        (qris["date"].dt.year >= year_range[0]) &
        (qris["date"].dt.year <= year_range[1])
    ].copy()

    # ── Growth metrics ────────────────────────────────────────────────────────
    latest = qris_f.iloc[-1]
    first  = qris_f.iloc[0]

    merch_cagr = compute_cagr(first["merchants"], latest["merchants"],
                               max((qris_f["date"].dt.year.max() - qris_f["date"].dt.year.min()), 1))
    txn_cagr   = compute_cagr(first["txn_volume"], latest["txn_volume"],
                               max((qris_f["date"].dt.year.max() - qris_f["date"].dt.year.min()), 1))

    c1, c2, c3, c4 = st.columns(4)
    for col, label, val in [
        (c1, "Merchant CAGR", f"{merch_cagr:.1f}%"),
        (c2, "Transaction CAGR", f"{txn_cagr:.1f}%"),
        (c3, "Latest merchants", f"{latest['merchants']/1e6:.1f}M"),
        (c4, "Txn value (latest month)", f"IDR {latest['txn_value_idr']:,.0f}B"),
    ]:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{val}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Main chart: volume + value dual axis ──────────────────────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=qris_f["date"], y=qris_f["txn_volume"] / 1e6,
            name="Transaction volume (M)",
            line=dict(color=BLUE, width=2.5),
            fill="tozeroy", fillcolor="rgba(29,78,216,0.08)",
            hovertemplate="%{y:.1f}M<extra>Volume</extra>",
        ))
        fig.add_trace(go.Scatter(
            x=qris_f["date"], y=qris_f["txn_value_idr"],
            name="Transaction value (B IDR)",
            yaxis="y2",
            line=dict(color=AMBER, width=2, dash="dot"),
            hovertemplate="IDR %{y:,.0f}B<extra>Value</extra>",
        ))
        fig.update_layout(
            title="QRIS monthly transaction volume & value",
            yaxis=dict(title="Volume (millions)", showgrid=True, gridcolor="#f1f5f9"),
            yaxis2=dict(title="Value (B IDR)", overlaying="y", side="right", showgrid=False),
            legend=dict(orientation="h", y=-0.18),
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=40, r=40, t=48, b=40),
            font=dict(family="Inter, Arial, sans-serif", size=12),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        # YoY growth rate
        qris_f = qris_f.copy()
        qris_f["yoy_merchants"] = yoy_growth(qris_f["merchants"]).round(1)
        qris_f["yoy_txn"] = yoy_growth(qris_f["txn_volume"]).round(1)
        qris_plot = qris_f.dropna(subset=["yoy_merchants"])

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=qris_plot["date"], y=qris_plot["yoy_merchants"],
            name="Merchant YoY %",
            marker_color=BLUE, opacity=0.75,
            hovertemplate="%{y:.1f}%<extra>Merchant growth</extra>",
        ))
        fig2.add_trace(go.Scatter(
            x=qris_plot["date"], y=qris_plot["yoy_txn"],
            name="Transaction YoY %",
            line=dict(color=GREEN, width=2.5),
            hovertemplate="%{y:.1f}%<extra>Txn growth</extra>",
        ))
        fig2.update_layout(
            title="Year-over-year growth rates",
            yaxis=dict(title="Growth (%)", showgrid=True, gridcolor="#f1f5f9"),
            legend=dict(orientation="h", y=-0.18),
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=40, r=20, t=48, b=40),
            font=dict(family="Inter, Arial, sans-serif", size=12),
            hovermode="x unified",
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Regional adoption breakdown ───────────────────────────────────────────
    st.markdown('<div class="section-header">Regional QRIS adoption</div>',
                unsafe_allow_html=True)

    reg_f = region[(region["year"] >= year_range[0]) & (region["year"] <= year_range[1])]
    latest_reg = reg_f[reg_f["year"] == reg_f["year"].max()]

    col_a, col_b = st.columns(2)

    with col_a:
        fig3 = go.Figure()
        for i, rgn in enumerate(reg_f["region"].unique()):
            d = reg_f[reg_f["region"] == rgn]
            fig3.add_trace(go.Scatter(
                x=d["year"], y=d["penetration_pct"],
                name=rgn,
                line=dict(color=PALETTE[i % len(PALETTE)], width=2.5),
                mode="lines+markers",
                marker=dict(size=6),
                hovertemplate="%{y:.1f}%<extra>" + rgn + "</extra>",
            ))
        fig3.update_layout(
            title="QRIS penetration by region (%)",
            yaxis=dict(title="Penetration (%)", showgrid=True, gridcolor="#f1f5f9"),
            legend=dict(orientation="h", y=-0.22, font=dict(size=10)),
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=40, r=20, t=48, b=60),
            font=dict(family="Inter, Arial, sans-serif", size=12),
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col_b:
        fig4 = bar_chart(
            latest_reg.sort_values("merchants", ascending=True),
            x="merchants", y="region",
            title="QRIS merchants by region (latest year)",
            y_suffix="",
        )
        fig4.update_traces(
            marker_color=[PALETTE[i] for i in range(len(latest_reg))],
            orientation="h",
            hovertemplate="%{x:,.0f} merchants<extra></extra>",
        )
        fig4.update_layout(
            xaxis=dict(title="Registered merchants"),
            yaxis=dict(title=""),
            margin=dict(l=120, r=20, t=48, b=40),
        )
        st.plotly_chart(fig4, use_container_width=True)

    # ── Average ticket size trend ─────────────────────────────────────────────
    st.markdown('<div class="section-header">Transaction value analysis</div>',
                unsafe_allow_html=True)

    qris_f["avg_ticket_idr"] = (
        qris_f["txn_value_idr"] * 1e9 / qris_f["txn_volume"]
    ).round(0)

    col_x, col_y = st.columns(2)

    with col_x:
        fig5 = go.Figure()
        fig5.add_trace(go.Scatter(
            x=qris_f["date"], y=qris_f["avg_ticket_idr"],
            line=dict(color=TEAL, width=2.5),
            fill="tozeroy", fillcolor="rgba(8,145,178,0.08)",
            hovertemplate="IDR %{y:,.0f}<extra>Avg ticket</extra>",
        ))
        fig5.update_layout(
            title="Average transaction ticket size (IDR)",
            yaxis=dict(title="IDR", tickformat=",.0f",
                       showgrid=True, gridcolor="#f1f5f9"),
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=60, r=20, t=48, b=40),
            font=dict(family="Inter, Arial, sans-serif", size=12),
        )
        st.plotly_chart(fig5, use_container_width=True)

    with col_y:
        # Digital share over time
        ps_f = ps[(ps["year"] >= year_range[0]) & (ps["year"] <= year_range[1])]
        fig6 = go.Figure()
        fig6.add_trace(go.Scatter(
            x=ps_f["year"], y=ps_f["digital_share_pct"],
            line=dict(color=GREEN, width=3),
            mode="lines+markers", marker=dict(size=8),
            hovertemplate="%{y:.1f}%<extra>Digital share</extra>",
        ))
        fig6.add_hline(y=50, line_dash="dash", line_color=AMBER,
                       annotation_text="50% milestone", annotation_font_size=10)
        fig6.add_hline(y=80, line_dash="dot", line_color=RED,
                       annotation_text="BI 2025 target (80%)", annotation_font_size=10)
        fig6.update_layout(
            title="Digital payment share of retail transactions (%)",
            yaxis=dict(title="%", range=[0, 100],
                       showgrid=True, gridcolor="#f1f5f9"),
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=40, r=20, t=48, b=40),
            font=dict(family="Inter, Arial, sans-serif", size=12),
        )
        st.plotly_chart(fig6, use_container_width=True)

    # ── Insight box ───────────────────────────────────────────────────────────
    st.markdown("""
    <div class="insight-box">
        <strong>Surveillance note:</strong>
        Average ticket size increasing from ~IDR 50k to ~IDR 75k suggests QRIS
        is graduating from micro-payment use cases (street food, parking) to
        higher-value retail and service transactions — a sign of consumer trust
        maturation. Eastern Indonesia penetration growth rate (+71% CAGR) now
        exceeds Java (+42% CAGR), suggesting catch-up dynamics consistent with
        BI's financial inclusion objectives. Monitor for merchant churn in
        over-penetrated Java markets.
    </div>
    """, unsafe_allow_html=True)
