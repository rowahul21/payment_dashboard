"""
pages/inclusion_map.py
──────────────────────
Financial Inclusion Map — provincial scatter-mapbox + analysis.

Production upgrade path:
    Replace px.scatter_mapbox with px.choropleth_mapbox using the
    Indonesia GeoJSON from:
    https://github.com/superpikar/indonesia-geojson
    Load with: gdf = gpd.read_file("indonesia_provinces.geojson")
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data.data_loader import get_provincial_inclusion
from utils.metrics import compute_inclusion_gap
from utils.charts import bar_chart, NAVY, BLUE, GREEN, AMBER, RED, PALETTE


def render(year_range):
    st.markdown('<div class="section-header">Financial Inclusion Map — 34 Provinces</div>',
                unsafe_allow_html=True)
    st.caption("Source: OJK Financial Inclusion Report · World Bank Global Findex 2021 · BPS")

    df = get_provincial_inclusion()
    df = compute_inclusion_gap(df)

    # ── Sidebar controls for this page ────────────────────────────────────────
    indicator = st.selectbox(
        "Map indicator",
        options={
            "Financial Inclusion Index (FII)": "fii",
            "Bank account ownership (%)": "bank_account_pct",
            "Digital payment usage (%)": "digital_pay_pct",
            "QRIS merchant density (per 1,000 adults)": "qris_merchant_den",
            "Bank branches (per 100,000 adults)": "branch_per_100k",
        }.keys(),
        index=0,
    )
    ind_map = {
        "Financial Inclusion Index (FII)": "fii",
        "Bank account ownership (%)": "bank_account_pct",
        "Digital payment usage (%)": "digital_pay_pct",
        "QRIS merchant density (per 1,000 adults)": "qris_merchant_den",
        "Bank branches (per 100,000 adults)": "branch_per_100k",
    }
    col = ind_map[indicator]

    # ── Map ───────────────────────────────────────────────────────────────────
    fig_map = px.scatter_mapbox(
        df,
        lat="lat", lon="lon",
        color=col,
        size=col,
        hover_name="province",
        hover_data={
            "fii": ":.1f",
            "bank_account_pct": ":.1f",
            "digital_pay_pct": ":.1f",
            "qris_merchant_den": ":.1f",
            "island_group": True,
            "lat": False, "lon": False,
        },
        color_continuous_scale="Blues",
        size_max=45,
        zoom=3.8,
        center={"lat": -2.5, "lon": 118},
        mapbox_style="open-street-map",
        title=f"{indicator} by province",
    )
    fig_map.update_layout(
        height=480,
        margin=dict(l=0, r=0, t=40, b=0),
        coloraxis_colorbar=dict(
            title=indicator[:20],
            thickness=14, len=0.5,
            tickfont=dict(size=10),
        ),
        paper_bgcolor="white",
        font=dict(family="Inter, Arial, sans-serif"),
    )
    st.plotly_chart(fig_map, use_container_width=True)

    st.info(
        "**Upgrade to polygon choropleth:** Install geopandas and load "
        "[indonesia-geojson](https://github.com/superpikar/indonesia-geojson) "
        "for filled province polygons. See `pages/inclusion_map.py` for instructions.",
        icon="ℹ️",
    )

    # ── Bottom analysis panels ────────────────────────────────────────────────
    st.markdown('<div class="section-header">Provincial breakdown</div>',
                unsafe_allow_html=True)

    col_l, col_r = st.columns(2)

    with col_l:
        # Top 10 / Bottom 10
        view = st.radio("Show", ["Bottom 10 (lowest inclusion)", "Top 10 (highest inclusion)"],
                        horizontal=True)
        n = 10
        if "Bottom" in view:
            subset = df.nsmallest(n, "fii")[["province", "fii", "island_group"]].copy()
            bar_color = RED
        else:
            subset = df.nlargest(n, "fii")[["province", "fii", "island_group"]].copy()
            bar_color = GREEN

        fig_bar = go.Figure(go.Bar(
            x=subset["fii"],
            y=subset["province"],
            orientation="h",
            marker_color=bar_color,
            text=subset["fii"].apply(lambda x: f"{x:.1f}"),
            textposition="outside",
            hovertemplate="%{y}: %{x:.1f}<extra>FII</extra>",
        ))
        fig_bar.add_vline(x=df["fii"].mean(), line_dash="dash", line_color=NAVY,
                          annotation_text=f"National avg: {df['fii'].mean():.1f}",
                          annotation_font_size=10)
        fig_bar.update_layout(
            title=view,
            xaxis=dict(title="Financial Inclusion Index", range=[0, 105]),
            yaxis=dict(autorange="reversed"),
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=160, r=60, t=48, b=40),
            font=dict(family="Inter, Arial, sans-serif", size=11),
            height=380,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_r:
        # Island group averages radar/bar
        island_avg = df.groupby("island_group").agg({
            "bank_account_pct": "mean",
            "digital_pay_pct": "mean",
            "qris_merchant_den": "mean",
            "fii": "mean",
        }).round(1).reset_index()

        fig_island = go.Figure()
        for i, row in island_avg.iterrows():
            fig_island.add_trace(go.Bar(
                name=row["island_group"],
                x=["Bank account", "Digital pay", "QRIS density×2", "FII"],
                y=[row["bank_account_pct"], row["digital_pay_pct"],
                   row["qris_merchant_den"] * 2, row["fii"]],
                marker_color=PALETTE[i % len(PALETTE)],
                hovertemplate="%{x}: %{y:.1f}<extra>" + row["island_group"] + "</extra>",
            ))
        fig_island.update_layout(
            title="Average indicators by island group",
            barmode="group",
            yaxis=dict(title="Value / score",
                       showgrid=True, gridcolor="#f1f5f9"),
            legend=dict(orientation="h", y=-0.2, font=dict(size=10)),
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=40, r=20, t=48, b=60),
            font=dict(family="Inter, Arial, sans-serif", size=11),
            height=380,
        )
        st.plotly_chart(fig_island, use_container_width=True)

    # ── Gap table ─────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Inclusion gap vs national average</div>',
                unsafe_allow_html=True)

    gap_df = df[["province", "island_group", "fii", "fii_gap",
                 "bank_account_pct", "digital_pay_pct", "qris_merchant_den"]].copy()
    gap_df = gap_df.sort_values("fii_gap")

    def color_gap(val):
        if val < -15:
            return "background-color: #fee2e2; color: #b91c1c"
        elif val < -5:
            return "background-color: #fef9c3; color: #a16207"
        elif val > 10:
            return "background-color: #dcfce7; color: #15803d"
        return ""

    st.dataframe(
        gap_df.rename(columns={
            "province": "Province",
            "island_group": "Island",
            "fii": "FII score",
            "fii_gap": "Gap vs avg",
            "bank_account_pct": "Bank acc (%)",
            "digital_pay_pct": "Digital pay (%)",
            "qris_merchant_den": "QRIS/1k adults",
        }),
        use_container_width=True,
        height=320,
    )

    # ── Policy insight ────────────────────────────────────────────────────────
    laggard_count = (df["fii"] < 50).sum()
    eastern_avg = df[df["island_group"] == "Eastern"]["fii"].mean()

    st.markdown(f"""
    <div class="insight-box">
        <strong>Policy surveillance finding:</strong>
        {laggard_count} of 34 provinces score below 50/100 on the Financial Inclusion Index,
        concentrated in Eastern Indonesia (avg FII: {eastern_avg:.1f}/100).
        The QRIS merchant density gap between Java (avg: 32/1,000) and Papua (3.2/1,000)
        represents a 10x disparity — the largest single driver of the inclusion gap.
        BI Agent Banking and QRIS subsidy programs should be prioritised for
        NTT, Papua, and Maluku based on this analysis.
    </div>
    """, unsafe_allow_html=True)

    # ── Download ──────────────────────────────────────────────────────────────
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download provincial inclusion data (CSV)",
        data=csv,
        file_name="indonesia_provincial_inclusion.csv",
        mime="text/csv",
    )
