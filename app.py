import streamlit as st

st.set_page_config(
    page_title="Indonesia Payment System Surveillance",
    page_icon="assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #0f2044; }
    [data-testid="stSidebar"] * { color: #e8f0fe !important; }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stSlider label { color: #b0c4de !important; font-size: 13px; }
    .metric-card {
        background: #ffffff;
        border: 0.5px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 0;
    }
    .metric-label { font-size: 12px; color: #64748b; font-weight: 500; margin-bottom: 4px; }
    .metric-value { font-size: 24px; font-weight: 600; color: #0f172a; }
    .metric-delta { font-size: 12px; margin-top: 2px; }
    .delta-up   { color: #16a34a; }
    .delta-down { color: #dc2626; }
    .section-header {
        font-size: 16px; font-weight: 600; color: #0f2044;
        border-bottom: 2px solid #1e40af;
        padding-bottom: 6px; margin: 24px 0 16px 0;
    }
    .badge {
        display: inline-block; padding: 3px 10px;
        border-radius: 99px; font-size: 11px; font-weight: 600;
    }
    .badge-green  { background: #dcfce7; color: #15803d; }
    .badge-amber  { background: #fef9c3; color: #a16207; }
    .badge-red    { background: #fee2e2; color: #b91c1c; }
    .badge-blue   { background: #dbeafe; color: #1d4ed8; }
    .insight-box {
        background: #f0f7ff; border-left: 4px solid #1d4ed8;
        border-radius: 0 8px 8px 0; padding: 12px 16px;
        margin: 12px 0; font-size: 13px; color: #1e3a5f;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Indonesia Payment System")
    st.markdown("**Surveillance Dashboard**")
    st.markdown("---")

    page = st.radio(
        "Navigation",
        [
            "Overview",
            "QRIS & Digital Payments",
            "Financial Inclusion Map",
            "ASEAN Benchmarking",
            "Risk & Anomaly Detection",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    year_range = st.slider("Year range", 2015, 2024, (2018, 2024))
    st.markdown("---")
    with st.expander("Methodology"):
        st.markdown("""
**Data sources**
- BIS CPMI Red Book Statistics
- World Bank Global Findex
- Bank Indonesia QRIS statistics
- OJK financial access data
- BPS provincial statistics

**Indicators**
- Transaction volume / value trends
- QRIS merchant & user growth
- Financial inclusion index (FII)
- Payment system concentration risk
- Interoperability score

**EWS Thresholds**
Based on BIS CPMI operational risk guidelines and BI payment system oversight framework.
        """)

# ── Page router ───────────────────────────────────────────────────────────────
if page == "Overview":
    from pages.overview import render
elif page == "QRIS & Digital Payments":
    from pages.qris import render
elif page == "Financial Inclusion Map":
    from pages.inclusion_map import render
elif page == "ASEAN Benchmarking":
    from pages.asean import render
elif page == "Risk & Anomaly Detection":
    from pages.risk import render

render(year_range)
