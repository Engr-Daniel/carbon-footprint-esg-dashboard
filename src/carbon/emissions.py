"""Core GHG emissions calculation engine (GHG Protocol, activity-based method).

emissions (kgCO2e) = activity quantity x emission factor (kgCO2e per unit)
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
FACTORS_PATH = ROOT / "data" / "reference" / "emission_factors.csv"
SAMPLE_PATH = ROOT / "data" / "sample" / "activity_data_sample.csv"

REQUIRED_ACTIVITY_COLS = {"period", "site", "activity_type", "quantity", "unit"}


def load_factors(path: Path | str = FACTORS_PATH) -> pd.DataFrame:
    """Load the emission factor reference table."""
    return pd.read_csv(path)


def load_activity(path: Path | str = SAMPLE_PATH) -> pd.DataFrame:
    """Load and validate activity data."""
    df = pd.read_csv(path)
    missing = REQUIRED_ACTIVITY_COLS - set(df.columns)
    if missing:
        raise ValueError(f"Activity data is missing columns: {sorted(missing)}")
    if (df["quantity"] < 0).any():
        raise ValueError("Activity quantities must be non-negative.")
    df["period"] = pd.to_datetime(df["period"], format="%Y-%m")
    df["year"] = df["period"].dt.year
    return df


FACTOR_COLS = ["activity_type", "scope", "category", "unit", "kgco2e_per_unit"]


def select_factors(factors: pd.DataFrame, years: list[int], policy: str = "latest") -> pd.DataFrame:
    """Pick one factor per activity type and reporting year.

    policy="latest"   -> apply the most recent factor set to every year (like-for-like trend;
                         the GHG Protocol recalculates the base year when methodology changes).
    policy="matching" -> use the factor_year matching each reporting year; if none, fall back
                         to the latest factor_year <= that year, else the earliest available.
    Tables without a factor_year column are applied to all years unchanged.
    """
    if policy not in {"latest", "matching"}:
        raise ValueError("policy must be 'latest' or 'matching'.")
    if "factor_year" not in factors.columns:
        return pd.concat([factors[FACTOR_COLS].assign(year=y) for y in years], ignore_index=True)

    picked = []
    for activity_type, grp in factors.groupby("activity_type"):
        grp = grp.sort_values("factor_year")
        for y in years:
            if policy == "latest":
                row = grp.iloc[-1]
            else:
                eligible = grp[grp["factor_year"] <= y]
                row = eligible.iloc[-1] if not eligible.empty else grp.iloc[0]
            picked.append({**row[FACTOR_COLS + ["factor_year"]].to_dict(), "year": y})
    return pd.DataFrame(picked)


def calculate_emissions(
    activity: pd.DataFrame, factors: pd.DataFrame, policy: str = "latest"
) -> pd.DataFrame:
    """Join activity data to factors and compute kgCO2e and tCO2e per row."""
    if "year" not in activity.columns:
        activity = activity.assign(year=pd.to_datetime(activity["period"]).dt.year)
    selected = select_factors(factors, sorted(activity["year"].unique()), policy)
    merged = activity.merge(
        selected,
        on=["activity_type", "year"],
        how="left",
        suffixes=("", "_factor"),
    )
    unmatched = merged.loc[merged["kgco2e_per_unit"].isna(), "activity_type"].unique()
    if len(unmatched):
        raise ValueError(f"No emission factor for activity types: {list(unmatched)}")
    unit_mismatch = merged["unit"] != merged["unit_factor"]
    if unit_mismatch.any():
        bad = merged.loc[unit_mismatch, ["activity_type", "unit", "unit_factor"]].drop_duplicates()
        raise ValueError(f"Unit mismatch between activity data and factors:\n{bad}")
    merged = merged.drop(columns="unit_factor")
    merged["kgco2e"] = merged["quantity"] * merged["kgco2e_per_unit"]
    merged["tco2e"] = merged["kgco2e"] / 1000
    return merged


def summarise(emissions: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Total tCO2e grouped by the given columns."""
    return (
        emissions.groupby(by, as_index=False)["tco2e"].sum().sort_values(by).reset_index(drop=True)
    )


def intensity(total_tco2e: float, denominator: float) -> float:
    """Emissions intensity, e.g. tCO2e per employee or per USD million revenue."""
    if denominator <= 0:
        raise ValueError("Denominator must be positive.")
    return total_tco2e / denominator


def reduction_vs_baseline(emissions: pd.DataFrame, baseline_year: int) -> pd.DataFrame:
    """Year-on-year totals with % change versus the baseline year."""
    yearly = summarise(emissions, ["year"])
    base = yearly.loc[yearly["year"] == baseline_year, "tco2e"]
    if base.empty:
        raise ValueError(f"Baseline year {baseline_year} not in data.")
    yearly["pct_change_vs_baseline"] = (yearly["tco2e"] / base.iloc[0] - 1) * 100
    return yearly
