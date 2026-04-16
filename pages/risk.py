"""
pages/risk.py
─────────────
Payment System Risk & Anomaly Detection — operational risk surveillance,
EWS signals, anomaly flagging, and scenario stress testing.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data.data_loader import get_risk_indicators
from utils.metrics import (
    compute_payment_risk_score, risk_label_color,
    detect_anomalies, herfindahl_index, concentration_label,
)
from utils.charts import gauge_chart, waterfall_chart, NAVY, BLUE, GREEN, AMBER, RED, TEAL


def render(year_range):
    st.markdown('<div class="section-header">Payment System Risk & Anomaly Detection</div>',
                unsafe_allow_html=True)
    st.caption("Source: Bank Indonesia Payment System Oversight · BIS CPMI operational risk guidelines")

    risk = get_risk_indicators()
    risk_f = risk[
        (risk["date"].dt.year >= year_range[0]) &
        (risk["date"].dt.year <= year_range[1])
    ].copy()

    latest = risk_f.iloc[-1]

    # ── Composite risk score ──────────────────────────────────────────────────
    score, components = compute_payment_risk_score(
        settlement_fails=latest["settlement_fails"],
        downtime_hours=latest["system_downtime"],
        fraud_rate_bps=latest["fraud_rate_bps"],
        concentration=latest["concentration"],
        interop_score=latest["interop_score"],
    )
    risk_lbl, risk_color = risk_label_color(score)

    # ── Gauges row ────────────────────────────────────────────────────────────
    g1, g2, g3, g4 = st.columns(4)
    with g1:
        st.plotly_chart(
            gauge_chart(score, "Composite risk score", max_val=100),
            use_container_width=True,
        )
    with g2:
        st.plotly_chart(
            gauge_chart(latest["interop_score"], "Interoperability score", max_val=100),
            use_container_width=True,
        )
    with g3:
        fraud_norm = min(latest["fraud_rate_bps"] / 10 * 100, 100)
        st.plotly_chart(
            gauge_chart(100 - fraud_norm, "Fraud safety score", max_val=100),
            use_container_width=True,
        )
    with g4:
        conc_norm = min(latest["concentration"] / 0.4 * 100, 100)
        st.plotly_chart(
            gauge_chart(100 - conc_norm, "Market competition score", max_val=100),
            use_container_width=True,
        )

    # ── Risk component waterfall ──────────────────────────────────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        cats = list(components.keys()) + ["Composite score"]
        vals = list(components.values()) + [score]
        fig_wf = waterfall_chart(cats, vals, title="Risk score component breakdown")
        st.plotly_chart(fig_wf, use_container_width=True)

    with col_r:
        # Risk trend over time
        scores = []
        for _, row in risk_f.iterrows():
            s, _ = compute_payment_risk_score(
                settlement_fails=row["settlement_fails"],
                downtime_hours=row["system_downtime"],
                fraud_rate_bps=row["fraud_rate_bps"],
                concentration=row["concentration"],
                interop_score=row["interop_score"],
            )
            scores.append(s)
        risk_f["risk_score"] = scores

        fig_rt = go.Figure()
        fig_rt.add_trace(go.Scatter(
            x=risk_f["date"], y=risk_f["risk_score"],
            line=dict(color=BLUE, width=2.5),
            fill="tozeroy", fillcolor="rgba(29,78,216,0.08)",
            hovertemplate="%{y:.1f}<extra>Risk score</extra>",
        ))
        for threshold, color, label in [(60, RED, "High"), (35, AMBER, "Elevated"), (15, GREEN, "Moderate")]:
            fig_rt.add_hline(y=threshold, line_dash="dash",
                             line_color=color, line_width=1,
                             annotation_text=label, annotation_font_size=9,
                             annotation_font_color=color)
        fig_rt.update_layout(
            title="Composite risk score trend",
            yaxis=dict(title="Risk score (0=safe, 100=critical)",
                       range=[0, 100], showgrid=True, gridcolor="#f1f5f9"),
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=40, r=20, t=48, b=40),
            font=dict(family="Inter, Arial, sans-serif", size=12),
        )
        st.plotly_chart(fig_rt, use_container_width=True)

    # ── Anomaly detection ─────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Anomaly detection — operational indicators</div>',
                unsafe_allow_html=True)

    for col_name, label, color, unit in [
        ("settlement_fails", "Settlement failures", RED, "count"),
        ("system_downtime", "System downtime", AMBER, "hours"),
        ("fraud_rate_bps", "Fraud rate", TEAL, "bps"),
    ]:
        risk_f[f"{col_name}_anomaly"] = detect_anomalies(risk_f[col_name])

    col_a, col_b = st.columns(2)

    for i, (col_name, label, color, unit) in enumerate([
        ("settlement_fails", "Settlement failures", RED, "txn"),
        ("fraud_rate_bps", "Fraud rate (bps)", TEAL, "bps"),
    ]):
        anom_dates = risk_f[risk_f[f"{col_name}_anomaly"]]["date"]
        anom_vals  = risk_f[risk_f[f"{col_name}_anomaly"]][col_name]

        fig_a = go.Figure()
        fig_a.add_trace(go.Scatter(
            x=risk_f["date"], y=risk_f[col_name],
            line=dict(color=color, width=2),
            name=label,
            hovertemplate=f"%{{y:.1f}} {unit}<extra>{label}</extra>",
        ))
        fig_a.add_trace(go.Scatter(
            x=anom_dates, y=anom_vals,
            mode="markers",
            marker=dict(color=RED, size=10, symbol="x-thin-open", line=dict(width=2.5)),
            name="Anomaly flagged",
            hovertemplate=f"%{{y:.1f}} {unit}<extra>ANOMALY</extra>",
        ))
        fig_a.update_layout(
            title=f"{label} — anomaly detection (2.5σ rolling z-score)",
            yaxis=dict(title=unit, showgrid=True, gridcolor="#f1f5f9"),
            legend=dict(orientation="h", y=-0.18),
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=40, r=20, t=48, b=50),
            font=dict(family="Inter, Arial, sans-serif", size=12),
        )
        target_col = col_a if i == 0 else col_b
        with target_col:
            st.plotly_chart(fig_a, use_container_width=True)

    # ── Concentration trend ───────────────────────────────────────────────────
    st.markdown('<div class="section-header">Market concentration surveillance</div>',
                unsafe_allow_html=True)

    col_x, col_y = st.columns(2)

    with col_x:
        fig_conc = go.Figure()
        fig_conc.add_trace(go.Scatter(
            x=risk_f["date"], y=risk_f["concentration"],
            line=dict(color=BLUE, width=2.5),
            fill="tozeroy", fillcolor="rgba(29,78,216,0.06)",
            hovertemplate="%{y:.3f}<extra>HHI</extra>",
        ))
        fig_conc.add_hline(y=0.25, line_dash="dash", line_color=AMBER,
                           annotation_text="BIS concentrated threshold (0.25)",
                           annotation_font_size=10)
        fig_conc.add_hline(y=0.15, line_dash="dot", line_color=GREEN,
                           annotation_text="Competitive threshold (0.15)",
                           annotation_font_size=10)
        fig_conc.update_layout(
            title="Payment market HHI — concentration trend",
            yaxis=dict(title="Herfindahl-Hirschman Index",
                       showgrid=True, gridcolor="#f1f5f9"),
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=40, r=20, t=48, b=40),
            font=dict(family="Inter, Arial, sans-serif", size=12),
        )
        st.plotly_chart(fig_conc, use_container_width=True)

    with col_y:
        # Interoperability score trend
        fig_interop = go.Figure()
        fig_interop.add_trace(go.Scatter(
            x=risk_f["date"], y=risk_f["interop_score"],
            line=dict(color=GREEN, width=2.5),
            mode="lines+markers",
            marker=dict(size=5),
            hovertemplate="%{y:.1f}/100<extra>Interop score</extra>",
        ))
        fig_interop.add_hline(y=80, line_dash="dash", line_color=NAVY,
                              annotation_text="BI target: 80+",
                              annotation_font_size=10)
        fig_interop.update_layout(
            title="Payment system interoperability score",
            yaxis=dict(title="Score (0–100)", range=[0, 105],
                       showgrid=True, gridcolor="#f1f5f9"),
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=40, r=20, t=48, b=40),
            font=dict(family="Inter, Arial, sans-serif", size=12),
        )
        st.plotly_chart(fig_interop, use_container_width=True)

    # ── Scenario stress test ──────────────────────────────────────────────────
    st.markdown('<div class="section-header">Scenario stress test</div>',
                unsafe_allow_html=True)

    st.markdown("Simulate a payment system stress scenario and see the impact on the composite risk score.")

    s1, s2, s3 = st.columns(3)
    with s1:
        shock_fails = st.slider("Settlement failure spike (×)", 1.0, 10.0, 1.0, step=0.5)
    with s2:
        shock_fraud = st.slider("Fraud rate spike (×)", 1.0, 5.0, 1.0, step=0.25)
    with s3:
        shock_down  = st.slider("System downtime spike (×)", 1.0, 8.0, 1.0, step=0.5)

    stressed_score, stressed_components = compute_payment_risk_score(
        settlement_fails=latest["settlement_fails"] * shock_fails,
        downtime_hours=latest["system_downtime"] * shock_down,
        fraud_rate_bps=latest["fraud_rate_bps"] * shock_fraud,
        concentration=latest["concentration"],
        interop_score=latest["interop_score"],
    )
    s_lbl, s_color = risk_label_color(stressed_score)

    r1, r2 = st.columns(2)
    with r1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Stressed risk score</div>
            <div class="metric-value" style="color:{s_color}">{stressed_score:.1f}/100</div>
            <div class="metric-delta">
                <span class="badge" style="background:{s_color}20;color:{s_color};
                font-size:13px;padding:4px 12px;border-radius:6px">{s_lbl}</span>
            </div>
        </div>""", unsafe_allow_html=True)
    with r2:
        delta = stressed_score - score
        direction = "deterioration" if delta > 0 else "improvement"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Score change vs baseline</div>
            <div class="metric-value" style="color:{'#dc2626' if delta>0 else '#16a34a'}">
                {'+' if delta > 0 else ''}{delta:.1f} pts
            </div>
            <div class="metric-delta" style="color:#64748b">
                {abs(delta):.1f}-point {direction} under this scenario
            </div>
        </div>""", unsafe_allow_html=True)

    # Anomaly summary table
    st.markdown('<div class="section-header">Flagged anomaly events</div>',
                unsafe_allow_html=True)
    anomaly_df = risk_f[
        risk_f["settlement_fails_anomaly"] |
        risk_f["fraud_rate_bps_anomaly"]
    ][["date", "settlement_fails", "system_downtime",
       "fraud_rate_bps", "concentration", "risk_score"]].copy()

    if len(anomaly_df) > 0:
        anomaly_df["date"] = anomaly_df["date"].dt.strftime("%Y-%m")
        anomaly_df.columns = ["Month", "Settlement fails", "Downtime (h)",
                               "Fraud (bps)", "HHI", "Risk score"]
        st.dataframe(anomaly_df, use_container_width=True)
    else:
        st.success("No anomalies detected in the selected period.")

    csv = risk_f.drop(columns=[c for c in risk_f.columns if "anomaly" in c]).to_csv(index=False).encode("utf-8")
    st.download_button("Download risk indicator data (CSV)", data=csv,
                       file_name="payment_risk_indicators.csv", mime="text/csv")
