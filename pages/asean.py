"""
pages/asean.py
──────────────
ASEAN Payment System Benchmarking — position Indonesia vs 5 peer economies.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data.data_loader import get_asean_comparison
from utils.charts import NAVY, BLUE, GREEN, AMBER, RED, TEAL, PURPLE, PALETTE


def render(year_range):
    st.markdown('<div class="section-header">ASEAN Payment System Benchmarking</div>',
                unsafe_allow_html=True)
    st.caption("Source: BIS CPMI Red Book · World Bank Global Findex · Central bank annual reports")

    df = get_asean_comparison()
    df_f = df[(df["year"] >= year_range[0]) & (df["year"] <= year_range[1])]

    latest_year = df_f["year"].max()
    latest = df_f[df_f["year"] == latest_year]
    idn = latest[latest["country"] == "Indonesia"].iloc[0]

    # ── Rank cards ────────────────────────────────────────────────────────────
    metrics = [
        ("Digital payment adoption", "digital_pay_pct", "%"),
        ("Mobile payment usage", "mobile_pay_pct", "%"),
        ("Cashless txn per capita", "cashless_per_cap", ""),
        ("Bank account ownership", "bank_acc_pct", "%"),
    ]

    cols = st.columns(4)
    for i, (label, col, suffix) in enumerate(metrics):
        ranked = latest.sort_values(col, ascending=False).reset_index(drop=True)
        rank = ranked[ranked["country"] == "Indonesia"].index[0] + 1
        val = idn[col]
        leader = ranked.iloc[0]

        with cols[i]:
            gap = leader[col] - val
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{val:.0f}{suffix}</div>
                <div class="metric-delta" style="color:#64748b">
                    Rank {rank}/6 · Gap to leader: {gap:.0f}{suffix} ({leader['country']})
                </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Trend comparison ──────────────────────────────────────────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        fig = go.Figure()
        country_colors = {
            "Indonesia": BLUE, "Malaysia": GREEN, "Thailand": TEAL,
            "Philippines": AMBER, "Vietnam": PURPLE, "Singapore": RED,
        }
        for country in df_f["country"].unique():
            d = df_f[df_f["country"] == country]
            width = 3.5 if country == "Indonesia" else 1.5
            dash = "solid" if country == "Indonesia" else "dot"
            fig.add_trace(go.Scatter(
                x=d["year"], y=d["digital_pay_pct"],
                name=country,
                line=dict(color=country_colors.get(country, BLUE), width=width, dash=dash),
                mode="lines+markers",
                marker=dict(size=6 if country == "Indonesia" else 4),
                hovertemplate="%{y:.0f}%<extra>" + country + "</extra>",
            ))
        fig.update_layout(
            title="Digital payment adoption — ASEAN trend (%)",
            yaxis=dict(title="% adults using digital payments", range=[0, 105],
                       showgrid=True, gridcolor="#f1f5f9"),
            legend=dict(orientation="h", y=-0.22, font=dict(size=10)),
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=40, r=20, t=48, b=60),
            font=dict(family="Inter, Arial, sans-serif", size=12),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        # Latest year bar comparison
        latest_sorted = latest.sort_values("digital_pay_pct", ascending=True)
        colors = [RED if c == "Indonesia" else "#93c5fd" for c in latest_sorted["country"]]
        fig2 = go.Figure(go.Bar(
            x=latest_sorted["digital_pay_pct"],
            y=latest_sorted["country"],
            orientation="h",
            marker_color=colors,
            text=latest_sorted["digital_pay_pct"].apply(lambda x: f"{x:.0f}%"),
            textposition="outside",
            hovertemplate="%{y}: %{x:.0f}%<extra></extra>",
        ))
        fig2.add_vline(
            x=idn["digital_pay_pct"], line_dash="dash",
            line_color=NAVY, line_width=1.5,
            annotation_text="Indonesia", annotation_font_size=10,
        )
        fig2.update_layout(
            title=f"Digital payment adoption ranking ({latest_year})",
            xaxis=dict(title="%", range=[0, 110]),
            yaxis=dict(title=""),
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=100, r=60, t=48, b=40),
            font=dict(family="Inter, Arial, sans-serif", size=12),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Bubble chart: efficiency vs inclusion ─────────────────────────────────
    st.markdown('<div class="section-header">Efficiency vs inclusion positioning</div>',
                unsafe_allow_html=True)

    fig3 = px.scatter(
        latest,
        x="bank_acc_pct",
        y="efficiency_score",
        size="cashless_per_cap",
        color="country",
        hover_name="country",
        text="country",
        labels={
            "bank_acc_pct": "Bank account ownership (%)",
            "efficiency_score": "Payment system efficiency score",
            "cashless_per_cap": "Cashless txn per capita",
        },
        title="Payment system positioning — ASEAN (bubble size = cashless transactions per capita)",
        color_discrete_map=country_colors,
        size_max=60,
    )
    fig3.update_traces(textposition="top center", textfont=dict(size=11))
    fig3.add_vline(x=idn["bank_acc_pct"], line_dash="dot",
                   line_color="#94a3b8", line_width=1)
    fig3.add_hline(y=idn["efficiency_score"], line_dash="dot",
                   line_color="#94a3b8", line_width=1)
    fig3.update_layout(
        showlegend=False,
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=40, r=20, t=60, b=40),
        font=dict(family="Inter, Arial, sans-serif", size=12),
        height=420,
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ── Convergence analysis ──────────────────────────────────────────────────
    st.markdown('<div class="section-header">Convergence gap to ASEAN-3 average</div>',
                unsafe_allow_html=True)

    asean3_avg = df_f[df_f["country"].isin(["Malaysia", "Thailand", "Singapore"])].groupby("year")["digital_pay_pct"].mean()
    idn_trend  = df_f[df_f["country"] == "Indonesia"].set_index("year")["digital_pay_pct"]
    gap_series = (asean3_avg - idn_trend).reset_index()
    gap_series.columns = ["year", "gap"]

    fig4 = go.Figure()
    fig4.add_trace(go.Bar(
        x=gap_series["year"], y=gap_series["gap"],
        marker_color=[GREEN if g < 20 else AMBER if g < 30 else RED for g in gap_series["gap"]],
        hovertemplate="Gap: %{y:.1f}pp<extra></extra>",
    ))
    fig4.update_layout(
        title="Indonesia digital payment gap vs ASEAN-3 average (percentage points)",
        yaxis=dict(title="Gap (pp)", showgrid=True, gridcolor="#f1f5f9"),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=40, r=20, t=48, b=40),
        font=dict(family="Inter, Arial, sans-serif", size=12),
    )
    st.plotly_chart(fig4, use_container_width=True)

    latest_gap = gap_series["gap"].iloc[-1]
    first_gap  = gap_series["gap"].iloc[0]
    st.markdown(f"""
    <div class="insight-box">
        <strong>Convergence finding:</strong>
        Indonesia's digital payment gap vs the ASEAN-3 average (Malaysia, Thailand, Singapore)
        has narrowed from {first_gap:.1f}pp to {latest_gap:.1f}pp — a significant improvement
        driven by QRIS rapid adoption. At the current trajectory, Indonesia could reach
        ASEAN-3 levels within 4–6 years. Key bottleneck remains bank account ownership (65%)
        vs ASEAN-3 average (~90%), which limits the addressable base for digital payment adoption.
    </div>
    """, unsafe_allow_html=True)
