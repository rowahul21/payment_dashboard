"""
utils/metrics.py
────────────────
Financial analytics functions for payment system surveillance.
All functions are pure (no side effects) and unit-testable.
"""

import pandas as pd
import numpy as np
from typing import Tuple, List, Dict


# ── 1. Financial Inclusion Index ──────────────────────────────────────────────

def compute_fii(
    bank_account_pct: float,
    digital_pay_pct: float,
    qris_merchant_den: float,
    branch_per_100k: float,
    weights: Tuple[float, float, float, float] = (0.35, 0.30, 0.20, 0.15),
) -> float:
    """Composite Financial Inclusion Index (0–100).

    Methodology adapted from World Bank G20 Financial Inclusion Framework.

    Args:
        bank_account_pct   : % adults with formal bank account
        digital_pay_pct    : % adults using digital payments
        qris_merchant_den  : QRIS merchants per 1,000 adults
        branch_per_100k    : bank branches per 100,000 adults
        weights            : (w_bank, w_digital, w_qris, w_branch) — must sum to 1.0

    Returns:
        FII score 0–100 (higher = more inclusive)
    """
    assert abs(sum(weights) - 1.0) < 1e-6, "Weights must sum to 1.0"

    # Normalise components to 0–100
    bank_score    = min(bank_account_pct, 100)
    digital_score = min(digital_pay_pct, 100)
    qris_score    = min(qris_merchant_den / 50 * 100, 100)   # 50/1000 = saturation benchmark
    branch_score  = min(branch_per_100k / 45 * 100, 100)     # 45/100k = ASEAN median

    w1, w2, w3, w4 = weights
    fii = (
        bank_score    * w1
        + digital_score * w2
        + qris_score    * w3
        + branch_score  * w4
    )
    return round(fii, 1)


# ── 2. Payment System Concentration ───────────────────────────────────────────

def herfindahl_index(market_shares: List[float]) -> float:
    """Herfindahl-Hirschman Index (HHI) for payment market concentration.

    Args:
        market_shares: list of market shares as decimals (must sum to ~1.0)

    Returns:
        HHI 0–1 (0 = perfect competition, 1 = monopoly)
        BIS threshold: > 0.25 = concentrated market
    """
    return round(sum(s ** 2 for s in market_shares), 4)


def concentration_label(hhi: float) -> str:
    """Map HHI to BIS/DoJ concentration category."""
    if hhi < 0.15:
        return "Competitive"
    elif hhi < 0.25:
        return "Moderately concentrated"
    else:
        return "Highly concentrated"


# ── 3. Anomaly Detection ──────────────────────────────────────────────────────

def detect_anomalies(
    series: pd.Series,
    window: int = 6,
    z_threshold: float = 2.5,
) -> pd.Series:
    """Flag statistical anomalies using rolling z-score.

    A point is flagged when its value deviates > z_threshold standard
    deviations from the rolling mean. Suitable for monthly operational
    risk indicators (downtime, settlement failures, fraud rate).

    Args:
        series      : time series of values
        window      : rolling window size (months)
        z_threshold : z-score threshold for flagging (default 2.5σ)

    Returns:
        Boolean Series — True where anomaly detected
    """
    rolling_mean = series.rolling(window=window, min_periods=3).mean()
    rolling_std  = series.rolling(window=window, min_periods=3).std()
    z_scores = (series - rolling_mean) / rolling_std.replace(0, np.nan)
    return z_scores.abs() > z_threshold


# ── 4. QRIS Growth Metrics ────────────────────────────────────────────────────

def compute_cagr(start: float, end: float, periods: int) -> float:
    """Compound Annual Growth Rate.

    Args:
        start   : starting value
        end     : ending value
        periods : number of periods (years)

    Returns:
        CAGR as a percentage (e.g. 42.3 for 42.3%)
    """
    if start <= 0 or periods <= 0:
        return 0.0
    return round(((end / start) ** (1 / periods) - 1) * 100, 1)


def mom_growth(series: pd.Series) -> pd.Series:
    """Month-over-month percentage change."""
    return series.pct_change() * 100


def yoy_growth(series: pd.Series, periods: int = 12) -> pd.Series:
    """Year-over-year percentage change (12-month lag for monthly data)."""
    return series.pct_change(periods=periods) * 100


# ── 5. Payment System Risk Score ──────────────────────────────────────────────

def compute_payment_risk_score(
    settlement_fails: float,
    downtime_hours: float,
    fraud_rate_bps: float,
    concentration: float,
    interop_score: float,
    # Benchmark thresholds (BIS CPMI operational risk guidelines)
    fail_threshold: float = 200.0,
    downtime_threshold: float = 2.0,
    fraud_threshold: float = 5.0,
    conc_threshold: float = 0.25,
) -> Tuple[float, dict]:
    """Composite Payment System Risk Score (0–100, lower = safer).

    Methodology:
        Each component is normalised against its threshold.
        Scores > 100 are capped at 100 (extreme stress).
        Interoperability reduces overall risk (inverse component).

    Returns:
        Tuple of (composite_score, component_scores_dict)
    """
    fail_score  = min((settlement_fails / fail_threshold) * 25, 25)
    down_score  = min((downtime_hours / downtime_threshold) * 25, 25)
    fraud_score = min((fraud_rate_bps / fraud_threshold) * 25, 25)
    conc_score  = min((concentration / conc_threshold) * 15, 15)
    interop_relief = (interop_score / 100) * 10  # good interop reduces risk

    composite = round(
        fail_score + down_score + fraud_score + conc_score - interop_relief, 1
    )
    composite = max(0, min(composite, 100))

    return composite, {
        "Settlement failures": round(fail_score, 1),
        "System downtime":     round(down_score, 1),
        "Fraud rate":          round(fraud_score, 1),
        "Concentration":       round(conc_score, 1),
        "Interop relief":      round(-interop_relief, 1),
    }


def risk_label_color(score: float) -> Tuple[str, str]:
    """Map composite risk score to label and hex color.

    Returns:
        (label, hex_color)
    """
    if score >= 60:
        return "HIGH RISK", "#dc2626"
    elif score >= 35:
        return "ELEVATED", "#d97706"
    elif score >= 15:
        return "MODERATE", "#2563eb"
    else:
        return "NORMAL", "#16a34a"


# ── 6. Inclusion Gap Analysis ─────────────────────────────────────────────────

def compute_inclusion_gap(df: pd.DataFrame) -> pd.DataFrame:
    """Add gap columns vs national average for each province.

    Args:
        df: provincial inclusion DataFrame (output of get_provincial_inclusion)

    Returns:
        DataFrame with additional *_gap columns
    """
    df = df.copy()
    for col in ["bank_account_pct", "digital_pay_pct", "fii"]:
        national_avg = df[col].mean()
        df[f"{col}_gap"] = (df[col] - national_avg).round(1)
    return df
