import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from carbon import calculate_emissions, intensity, load_activity, load_factors, reduction_vs_baseline  # noqa: E402


@pytest.fixture
def factors():
    return pd.DataFrame(
        {
            "activity_type": ["diesel", "grid_electricity_ng"],
            "scope": [1, 2],
            "category": ["Combustion", "Electricity"],
            "unit": ["litre", "kWh"],
            "kgco2e_per_unit": [2.5, 0.5],
        }
    )


def make_activity(rows):
    df = pd.DataFrame(rows, columns=["period", "site", "activity_type", "quantity", "unit"])
    df["period"] = pd.to_datetime(df["period"])
    df["year"] = df["period"].dt.year
    return df


def test_calculation(factors):
    act = make_activity([["2024-01", "A", "diesel", 1000, "litre"], ["2024-01", "A", "grid_electricity_ng", 2000, "kWh"]])
    out = calculate_emissions(act, factors)
    assert out["tco2e"].tolist() == pytest.approx([2.5, 1.0])


def test_missing_factor_raises(factors):
    act = make_activity([["2024-01", "A", "unknown", 1, "litre"]])
    with pytest.raises(ValueError, match="No emission factor"):
        calculate_emissions(act, factors)


def test_unit_mismatch_raises(factors):
    act = make_activity([["2024-01", "A", "diesel", 1, "kWh"]])
    with pytest.raises(ValueError, match="Unit mismatch"):
        calculate_emissions(act, factors)


def test_reduction_vs_baseline(factors):
    act = make_activity([["2023-01", "A", "diesel", 1000, "litre"], ["2024-01", "A", "diesel", 800, "litre"]])
    out = reduction_vs_baseline(calculate_emissions(act, factors), 2023)
    assert out["pct_change_vs_baseline"].tolist() == pytest.approx([0.0, -20.0])


def test_intensity():
    assert intensity(100, 50) == 2
    with pytest.raises(ValueError):
        intensity(100, 0)


def test_sample_data_runs_end_to_end():
    out = calculate_emissions(load_activity(), load_factors())
    assert out["tco2e"].sum() > 0
    assert set(out["scope"]) == {1, 2, 3}
