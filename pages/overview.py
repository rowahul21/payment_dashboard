"""
pages/overview.py
─────────────────
Executive overview — 4 KPI cards, trend sparklines, key insights.
This is the first page a Bank Indonesia analyst sees.
"""

import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data.data_loader import (
    get_qris_data, get_payment_system_data,
    get_risk_indicators, get_provincial_inclusion,
)
from utils.metrics import compute_payment_risk_score, risk_label_color
from utils.charts import line_chart, area_chart


def metric_card(label: str, value: str, delta: str = "", delta_positive: bool = True):
    delta_class = "delta-up" if delta_positive else "delta-down"
    delta_html = f'<div class="metric-delta {delta_class}">{delta}</div>' if delta else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def render(year_range):
    st.markdown('<div class="section-header">Executive Overview — Indonesia Payment System</div>',
                unsafe_allow_html=True)
    st.caption("Data: Bank Indonesia · BIS CPMI · World Bank Findex · OJK")

    # ── Load data ─────────────────────────────────────────────────────────────
    qris   = get_qris_data()
    ps     = get_payment_system_data()
    risk   = get_risk_indicators()
    prov   = get_provincial_inclusion()

    # Filter ps by year range
    ps_f = ps[(ps["year"] >= year_range[0]) & (ps["year"] <= year_range[1])]

    latest_qris    = qris.iloc[-1]
    prev_qris      = qris.iloc[-13] if len(qris) > 13 else qris.iloc[0]
    latest_risk    = risk.iloc[-1]

    risk_score, _ = compute_payment_risk_score(
        settlement_fails=latest_risk["settlement_fails"],
        downtime_hours=latest_risk["system_downtime"],
        fraud_rate_bps=latest_risk["fraud_rate_bps"],
        concentration=latest_risk["concentration"],
        interop_score=latest_risk["interop_score"],
    )
    risk_lbl, risk_color = risk_label_color(risk_score)

    # ── KPI Row ───────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        merch_m = latest_qris["merchants"] / 1e6
        prev_m  = prev_qris["merchants"] / 1e6
        metric_card(
            "QRIS merchants",
            f"{merch_m:.1f}M",
            f"+{merch_m - prev_m:.1f}M YoY",
            True,
        )

    with c2:
        txn_bn = latest_qris["txn_volume"] / 1e9
        prev_txn_bn = prev_qris["txn_volume"] / 1e9
        metric_card(
            "Monthly transactions",
            f"{txn_bn:.2f}B",
            f"+{(txn_bn/prev_txn_bn - 1)*100:.0f}% YoY",
            True,
        )

    with c3:
        dig_share = ps_f["digital_share_pct"].iloc[-1] if len(ps_f) else 68
        prev_dig  = ps_f["digital_share_pct"].iloc[-2] if len(ps_f) > 1 else 59
        metric_card(
            "Digital payment share",
            f"{dig_share:.1f}%",
            f"+{dig_share - prev_dig:.1f}pp vs prior year",
            True,
        )

    with c4:
        nat_fii = prov["fii"].mean()
        metric_card(
            "National inclusion index",
            f"{nat_fii:.1f}/100",
            f"{prov[prov['fii'] < 50]['province'].count()} provinces below 50",
            False,
        )

    with c5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">System risk level</div>
            <div style="margin-top:6px">
                <span class="badge" style="background:{risk_color}20;color:{risk_color};
                font-size:14px;padding:4px 14px;border-radius:8px;font-weight:700">
                    {risk_lbl}
                </span>
            </div>
            <div class="metric-delta" style="margin-top:6px;color:#64748b">
                Score: {risk_score:.0f}/100
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts row ────────────────────────────────────────────────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        # Payment mix evolution
        ps_plot = ps_f.copy()
        fig = area_chart(
            ps_plot, x="year",
            y_cols=["mobile_txn_bn", "e_money_txn_bn", "card_txn_bn", "atm_txn_bn"],
            labels={
                "mobile_txn_bn": "Mobile banking",
                "e_money_txn_bn": "E-money / QRIS",
                "card_txn_bn": "Cards",
                "atm_txn_bn": "ATM",
            },
            title="Payment channel mix (billion transactions)",
            y_suffix="B txn",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        # QRIS merchant + user growth
        qris_annual = qris.copy()
        qris_annual["year"] = qris_annual["date"].dt.year
        qris_annual = qris_annual.groupby("year").last().reset_index()
        fig2 = line_chart(
            qris_annual, x="year",
            y_cols=["merchants", "users"],
            labels={"merchants": "Registered merchants", "users": "Registered users"},
            title="QRIS cumulative adoption",
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Insights ──────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Key surveillance insights</div>',
                unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown("""
        <div class="insight-box">
            <strong>Digital acceleration on track</strong><br>
            Mobile and e-money channels now account for the majority of retail
            transaction volume, with ATM usage in structural decline since 2019.
            QRIS merchant density in Java is approaching saturation — growth
            momentum is shifting to Eastern Indonesia.
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown("""
        <div class="insight-box">
            <strong>Inclusion gap: Eastern provinces</strong><br>
            Papua, NTT, and Maluku show financial inclusion index scores
            below 30/100 — more than 40 points below the national average.
            QRIS merchant density in these provinces is 10x lower than Java.
            Priority area for BI inclusion policy intervention.
        </div>
        """, unsafe_allow_html=True)

    with col_c:
        st.markdown("""
        <div class="insight-box">
            <strong>Risk: improving trajectory</strong><br>
            Operational risk score has declined steadily as system infrastructure
            matures. Fraud rate has halved since 2020. Key remaining risk is
            payment market concentration — top 3 providers still control
            ~65% of e-money transaction volume.
        </div>
        """, unsafe_allow_html=True)
