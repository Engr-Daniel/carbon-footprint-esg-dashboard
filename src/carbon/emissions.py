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


def calculate_emissions(activity: pd.DataFrame, factors: pd.DataFrame) -> pd.DataFrame:
    """Join activity data to factors and compute kgCO2e and tCO2e per row."""
    merged = activity.merge(
        factors[["activity_type", "scope", "category", "unit", "kgco2e_per_unit"]],
        on="activity_type",
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
