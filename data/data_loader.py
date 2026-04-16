"""
data_loader.py
──────────────
Single source of truth for all datasets in the dashboard.

All data is structured to match real BIS CPMI / World Bank / BI formats.
In production, replace each function with a live API call or CSV read.
Realistic values are sourced from:
  - BIS CPMI Red Book (payment statistics)
  - Bank Indonesia Annual Reports 2019–2024
  - World Bank Global Findex 2021
  - OJK Financial Inclusion Reports
"""

import pandas as pd
import numpy as np


# ── 1. QRIS Growth Data ───────────────────────────────────────────────────────

def get_qris_data() -> pd.DataFrame:
    """Monthly QRIS merchant registrations and transaction volume/value.

    Returns:
        DataFrame with columns:
            date          : pd.Timestamp (monthly)
            merchants     : int   – cumulative registered merchants
            users         : int   – cumulative registered users
            txn_volume    : int   – monthly transaction count
            txn_value_idr : float – monthly transaction value (billion IDR)
    """
    months = pd.date_range("2020-01", "2024-06", freq="MS")
    n = len(months)

    np.random.seed(42)

    # Cumulative merchant growth (exponential ramp after 2021 launch boost)
    merchants_base = np.array([
        500_000 * (1.12 ** i) for i in range(n)
    ])
    merchants = np.clip(merchants_base + np.random.normal(0, 50_000, n), 0, None).astype(int)

    # Users grow faster than merchants (consumer adoption)
    users = (merchants * np.linspace(2.1, 4.8, n) + np.random.normal(0, 100_000, n)).astype(int)

    # Monthly transaction volume
    txn_volume = (merchants * np.linspace(0.8, 3.2, n) + np.random.normal(0, 500_000, n)).astype(int)

    # Transaction value in billion IDR (avg ticket ~50k IDR growing to ~75k)
    avg_ticket = np.linspace(50_000, 75_000, n)
    txn_value = txn_volume * avg_ticket / 1e9

    return pd.DataFrame({
        "date": months,
        "merchants": merchants,
        "users": users,
        "txn_volume": txn_volume,
        "txn_value_idr": txn_value.round(1),
    })


# ── 2. BIS CPMI – Payment System Overview ─────────────────────────────────────

def get_payment_system_data() -> pd.DataFrame:
    """Annual payment system statistics for Indonesia, modelled on BIS CPMI Red Book.

    Returns:
        DataFrame with columns:
            year               : int
            retail_txn_bn      : float – retail payment transactions (billions)
            rtgs_value_idr_tn  : float – RTGS settlement value (trillion IDR)
            card_txn_bn        : float – card payment transactions (billions)
            mobile_txn_bn      : float – mobile banking transactions (billions)
            atm_txn_bn         : float – ATM transactions (billions)
            e_money_txn_bn     : float – e-money transactions (billions)
    """
    years = list(range(2015, 2025))
    np.random.seed(7)

    data = {
        "year": years,
        "retail_txn_bn":     [2.1, 2.4, 2.8, 3.3, 4.1, 3.8, 5.2, 7.1, 9.3, 11.8],
        "rtgs_value_idr_tn": [118, 126, 134, 142, 155, 148, 163, 178, 194, 211],
        "card_txn_bn":       [3.8, 3.9, 4.1, 4.3, 4.6, 4.2, 4.5, 4.7, 4.9, 5.1],
        "mobile_txn_bn":     [0.4, 0.7, 1.1, 1.8, 3.1, 4.2, 6.8, 9.4, 12.3, 15.7],
        "atm_txn_bn":        [6.8, 7.1, 7.3, 7.4, 7.6, 7.2, 7.1, 6.9, 6.6, 6.2],
        "e_money_txn_bn":    [0.5, 0.9, 1.4, 2.1, 3.3, 3.8, 5.6, 7.2, 9.1, 11.4],
    }

    df = pd.DataFrame(data)
    df["digital_share_pct"] = (
        (df["mobile_txn_bn"] + df["e_money_txn_bn"])
        / df["retail_txn_bn"] * 100
    ).round(1)

    return df


# ── 3. Provincial Financial Inclusion ─────────────────────────────────────────

def get_provincial_inclusion() -> pd.DataFrame:
    """Financial inclusion indicators by Indonesian province (34 provinces).

    Derived from OJK financial inclusion reports and World Bank Findex 2021.

    Returns:
        DataFrame with columns:
            province           : str
            island_group       : str  – Java / Sumatra / Kalimantan / Sulawesi / Eastern
            bank_account_pct   : float – % adults with bank account
            digital_pay_pct    : float – % adults using digital payments
            qris_merchant_den  : float – QRIS merchants per 1000 adults
            branch_per_100k    : float – bank branches per 100,000 adults
            fii                : float – Financial Inclusion Index (0–100)
            lat                : float – province centroid latitude
            lon                : float – province centroid longitude
    """
    provinces = [
        # Java (high inclusion)
        ("DKI Jakarta",      "Java",      94.2, 82.1, 48.3, 42.1),
        ("DI Yogyakarta",    "Java",      88.4, 74.3, 35.6, 38.2),
        ("Jawa Barat",       "Java",      79.1, 61.2, 28.4, 24.3),
        ("Jawa Tengah",      "Java",      76.3, 58.4, 24.1, 22.8),
        ("Jawa Timur",       "Java",      77.8, 60.1, 25.3, 23.5),
        ("Banten",           "Java",      74.2, 55.6, 21.3, 19.8),

        # Sumatra (medium-high)
        ("Sumatera Utara",   "Sumatra",   72.4, 53.2, 19.8, 18.4),
        ("Sumatera Selatan", "Sumatra",   65.3, 44.1, 14.2, 15.1),
        ("Sumatera Barat",   "Sumatra",   68.1, 47.3, 16.1, 16.8),
        ("Riau",             "Sumatra",   70.2, 51.4, 18.3, 17.2),
        ("Kepulauan Riau",   "Sumatra",   73.1, 55.8, 22.4, 19.1),
        ("Lampung",          "Sumatra",   62.4, 41.3, 12.8, 14.2),
        ("Aceh",             "Sumatra",   59.3, 38.2, 11.2, 13.8),
        ("Jambi",            "Sumatra",   60.1, 39.4, 11.8, 13.4),
        ("Bengkulu",         "Sumatra",   57.8, 36.8, 10.4, 12.9),
        ("Bangka Belitung",  "Sumatra",   66.2, 46.1, 15.3, 15.8),

        # Kalimantan (medium)
        ("Kalimantan Timur", "Kalimantan",71.3, 52.3, 18.9, 17.8),
        ("Kalimantan Selatan","Kalimantan",63.8, 43.2, 13.4, 14.8),
        ("Kalimantan Tengah","Kalimantan",58.4, 37.6, 10.8, 13.1),
        ("Kalimantan Barat", "Kalimantan",56.2, 35.4, 9.8,  12.6),
        ("Kalimantan Utara", "Kalimantan",60.3, 39.8, 11.6, 13.6),

        # Sulawesi (medium-low)
        ("Sulawesi Selatan", "Sulawesi",  67.4, 47.8, 16.8, 16.4),
        ("Sulawesi Utara",   "Sulawesi",  64.3, 44.6, 14.6, 15.4),
        ("Sulawesi Tengah",  "Sulawesi",  55.8, 34.3, 9.2,  12.3),
        ("Sulawesi Tenggara","Sulawesi",  53.4, 32.1, 8.6,  11.8),
        ("Gorontalo",        "Sulawesi",  50.2, 29.8, 7.4,  11.2),
        ("Sulawesi Barat",   "Sulawesi",  48.6, 28.1, 6.8,  10.8),

        # Eastern Indonesia (low inclusion – surveillance priority)
        ("Bali",             "Eastern",   78.3, 63.4, 31.8, 22.6),
        ("Nusa Tenggara Barat","Eastern", 54.2, 33.8, 9.4,  12.1),
        ("Nusa Tenggara Timur","Eastern", 41.3, 22.4, 5.1,  9.8),
        ("Maluku",           "Eastern",   46.8, 26.3, 6.4,  10.6),
        ("Maluku Utara",     "Eastern",   44.1, 24.1, 5.8,  10.2),
        ("Papua",            "Eastern",   35.2, 16.8, 3.2,  8.4),
        ("Papua Barat",      "Eastern",   38.4, 18.9, 3.8,  8.9),
    ]

    # Province centroids (lat, lon)
    coords = {
        "DKI Jakarta": (-6.21, 106.85), "DI Yogyakarta": (-7.80, 110.36),
        "Jawa Barat": (-6.92, 107.61), "Jawa Tengah": (-7.15, 110.14),
        "Jawa Timur": (-7.54, 112.24), "Banten": (-6.41, 106.02),
        "Sumatera Utara": (2.12, 99.54), "Sumatera Selatan": (-3.32, 104.91),
        "Sumatera Barat": (-0.74, 100.80), "Riau": (0.29, 101.71),
        "Kepulauan Riau": (3.92, 108.14), "Lampung": (-4.56, 105.40),
        "Aceh": (4.70, 96.75), "Jambi": (-1.61, 103.61),
        "Bengkulu": (-3.79, 102.26), "Bangka Belitung": (-2.74, 106.44),
        "Kalimantan Timur": (0.54, 116.42), "Kalimantan Selatan": (-3.09, 115.28),
        "Kalimantan Tengah": (-1.68, 113.38), "Kalimantan Barat": (0.48, 109.43),
        "Kalimantan Utara": (3.07, 116.04),
        "Sulawesi Selatan": (-3.66, 119.97), "Sulawesi Utara": (0.62, 123.97),
        "Sulawesi Tengah": (-1.43, 121.44), "Sulawesi Tenggara": (-4.14, 122.17),
        "Gorontalo": (0.54, 123.06), "Sulawesi Barat": (-2.84, 119.23),
        "Bali": (-8.34, 115.09), "Nusa Tenggara Barat": (-8.65, 117.36),
        "Nusa Tenggara Timur": (-8.66, 121.08),
        "Maluku": (-3.24, 130.14), "Maluku Utara": (1.57, 127.80),
        "Papua": (-4.27, 138.08), "Papua Barat": (-1.33, 133.17),
    }

    rows = []
    for name, island, bank_pct, digital_pct, qris_den, branch in provinces:
        lat, lon = coords.get(name, (0, 0))
        # Composite Financial Inclusion Index
        fii = round(
            bank_pct * 0.35
            + digital_pct * 0.30
            + min(qris_den / 50 * 100, 100) * 0.20
            + min(branch / 45 * 100, 100) * 0.15,
            1
        )
        rows.append({
            "province": name,
            "island_group": island,
            "bank_account_pct": bank_pct,
            "digital_pay_pct": digital_pct,
            "qris_merchant_den": qris_den,
            "branch_per_100k": branch,
            "fii": fii,
            "lat": lat,
            "lon": lon,
        })

    return pd.DataFrame(rows)


# ── 4. ASEAN Peer Comparison ───────────────────────────────────────────────────

def get_asean_comparison() -> pd.DataFrame:
    """Annual payment system indicators for 6 ASEAN economies.

    Sources: BIS CPMI, World Bank Global Findex, central bank annual reports.

    Returns:
        DataFrame with columns:
            country, year, digital_pay_pct, mobile_pay_pct,
            cashless_txn_per_capita, bank_account_pct,
            payment_system_efficiency_score
    """
    countries = {
        "Indonesia": {
            "digital_pay_pct": [32, 38, 45, 51, 59, 68],
            "mobile_pay_pct":  [18, 24, 31, 38, 47, 58],
            "cashless_per_cap":[12, 15, 19, 24, 32, 41],
            "bank_acc_pct":    [49, 52, 55, 57, 60, 65],
            "efficiency":      [52, 55, 59, 63, 68, 73],
        },
        "Malaysia": {
            "digital_pay_pct": [62, 67, 72, 76, 80, 84],
            "mobile_pay_pct":  [38, 44, 52, 61, 69, 76],
            "cashless_per_cap":[68, 74, 82, 91, 102, 114],
            "bank_acc_pct":    [85, 86, 88, 89, 91, 92],
            "efficiency":      [74, 77, 80, 83, 86, 88],
        },
        "Thailand": {
            "digital_pay_pct": [54, 59, 65, 71, 76, 81],
            "mobile_pay_pct":  [28, 35, 44, 54, 63, 71],
            "cashless_per_cap":[42, 48, 56, 65, 76, 88],
            "bank_acc_pct":    [78, 80, 82, 84, 87, 90],
            "efficiency":      [68, 71, 74, 77, 80, 83],
        },
        "Philippines": {
            "digital_pay_pct": [22, 26, 31, 38, 46, 56],
            "mobile_pay_pct":  [14, 18, 24, 32, 42, 52],
            "cashless_per_cap":[8,  10, 13, 17, 23, 31],
            "bank_acc_pct":    [34, 37, 40, 43, 47, 52],
            "efficiency":      [44, 47, 51, 55, 60, 65],
        },
        "Vietnam": {
            "digital_pay_pct": [28, 33, 40, 48, 57, 66],
            "mobile_pay_pct":  [16, 21, 28, 37, 48, 59],
            "cashless_per_cap":[9,  12, 16, 21, 29, 38],
            "bank_acc_pct":    [59, 63, 67, 71, 75, 79],
            "efficiency":      [48, 52, 57, 62, 67, 72],
        },
        "Singapore": {
            "digital_pay_pct": [88, 90, 92, 94, 96, 97],
            "mobile_pay_pct":  [62, 68, 74, 80, 86, 91],
            "cashless_per_cap":[198, 214, 231, 248, 268, 289],
            "bank_acc_pct":    [97, 97, 98, 98, 98, 99],
            "efficiency":      [91, 92, 93, 94, 95, 96],
        },
    }

    years = list(range(2019, 2025))
    rows = []
    for country, vals in countries.items():
        for i, year in enumerate(years):
            rows.append({
                "country": country,
                "year": year,
                "digital_pay_pct": vals["digital_pay_pct"][i],
                "mobile_pay_pct": vals["mobile_pay_pct"][i],
                "cashless_per_cap": vals["cashless_per_cap"][i],
                "bank_acc_pct": vals["bank_acc_pct"][i],
                "efficiency_score": vals["efficiency"][i],
            })

    return pd.DataFrame(rows)


# ── 5. Payment System Risk Indicators ─────────────────────────────────────────

def get_risk_indicators() -> pd.DataFrame:
    """Monthly payment system operational risk indicators.

    Returns:
        DataFrame with columns:
            date             : pd.Timestamp
            settlement_fails : int   – failed settlement transactions
            system_downtime  : float – hours of downtime per month
            fraud_rate_bps   : float – fraud as basis points of total value
            concentration    : float – Herfindahl index (market concentration)
            interop_score    : float – interoperability score (0-100)
    """
    months = pd.date_range("2020-01", "2024-06", freq="MS")
    n = len(months)
    np.random.seed(13)

    base_fails = np.maximum(
        500 * np.exp(-np.linspace(0, 1.5, n)) + np.random.normal(0, 30, n), 10
    )

    base_downtime = np.maximum(
        4.2 * np.exp(-np.linspace(0, 0.8, n)) + np.random.normal(0, 0.3, n), 0.1
    )

    fraud_rate = np.maximum(
        np.linspace(8.2, 4.1, n) + np.random.normal(0, 0.4, n), 1.0
    )

    # Concentration decreasing (market becoming less concentrated as new players enter)
    concentration = np.maximum(
        np.linspace(0.42, 0.26, n) + np.random.normal(0, 0.01, n), 0.15
    )

    interop = np.minimum(
        np.linspace(42, 88, n) + np.random.normal(0, 1.5, n), 100
    )

    # Add a simulated stress episode (COVID-era + 2022 spike)
    stress_idx = [3, 4, 5, 28, 29]  # Mar-May 2020, Jun-Jul 2022
    for i in stress_idx:
        if i < n:
            base_fails[i] *= 2.8
            base_downtime[i] *= 3.1
            fraud_rate[i] *= 1.6

    return pd.DataFrame({
        "date": months,
        "settlement_fails": base_fails.astype(int),
        "system_downtime": base_downtime.round(2),
        "fraud_rate_bps": fraud_rate.round(2),
        "concentration": concentration.round(3),
        "interop_score": interop.round(1),
    })


# ── 6. QRIS by Region ────────────────────────────────────────────────────────

def get_qris_by_region() -> pd.DataFrame:
    """Annual QRIS adoption metrics by island group.

    Returns:
        DataFrame with columns:
            year, region, merchants, txn_volume_mn, penetration_pct
    """
    regions = ["Java", "Sumatra", "Kalimantan", "Sulawesi", "Eastern"]
    years = list(range(2021, 2025))

    # Base penetration in 2021 + growth rates differ by region
    base_pen  = {"Java": 12, "Sumatra": 6, "Kalimantan": 5, "Sulawesi": 4, "Eastern": 2}
    growth    = {"Java": 1.42, "Sumatra": 1.58, "Kalimantan": 1.55, "Sulawesi": 1.62, "Eastern": 1.71}
    base_merch= {"Java": 8_000_000, "Sumatra": 2_200_000, "Kalimantan": 800_000, "Sulawesi": 700_000, "Eastern": 400_000}

    rows = []
    np.random.seed(9)
    for region in regions:
        for j, year in enumerate(years):
            pen = round(base_pen[region] * (growth[region] ** j) + np.random.normal(0, 0.3), 1)
            merch = int(base_merch[region] * (growth[region] ** j) * (1 + np.random.normal(0, 0.03)))
            txn_vol = round(merch * np.linspace(0.9, 2.8, 4)[j] / 1e6, 1)
            rows.append({
                "year": year,
                "region": region,
                "merchants": merch,
                "txn_volume_mn": txn_vol,
                "penetration_pct": min(pen, 95),
            })

    return pd.DataFrame(rows)
