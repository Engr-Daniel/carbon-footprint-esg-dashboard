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


@pytest.fixture
def yearly_factors():
    return pd.DataFrame(
        {
            "activity_type": ["diesel", "diesel"],
            "scope": [1, 1],
            "category": ["Combustion", "Combustion"],
            "unit": ["litre", "litre"],
            "kgco2e_per_unit": [2.0, 3.0],
            "factor_year": [2023, 2025],
        }
    )


def test_latest_policy_applies_newest_factor_to_all_years(yearly_factors):
    act = make_activity([["2023-01", "A", "diesel", 1000, "litre"], ["2024-01", "A", "diesel", 1000, "litre"]])
    out = calculate_emissions(act, yearly_factors, policy="latest")
    assert out["tco2e"].tolist() == pytest.approx([3.0, 3.0])


def test_matching_policy_uses_year_specific_factor_with_fallback(yearly_factors):
    act = make_activity(
        [["2022-01", "A", "diesel", 1000, "litre"],   # before any factor -> earliest (2023)
         ["2024-01", "A", "diesel", 1000, "litre"],   # no 2024 factor -> latest <= 2024 (2023)
         ["2025-01", "A", "diesel", 1000, "litre"]]   # exact match (2025)
    )
    out = calculate_emissions(act, yearly_factors, policy="matching")
    assert out["tco2e"].tolist() == pytest.approx([2.0, 2.0, 3.0])


def test_invalid_policy_raises(yearly_factors):
    act = make_activity([["2024-01", "A", "diesel", 1, "litre"]])
    with pytest.raises(ValueError, match="policy"):
        calculate_emissions(act, yearly_factors, policy="bogus")


def test_every_factor_has_source_and_year():
    f = load_factors()
    assert f["source"].notna().all() and (f["source"].str.len() > 0).all()
    assert f["factor_year"].notna().all()
    assert not f.duplicated(["activity_type", "component"]).any()
    assert (f.loc[f.component == "primary", "activity_type"].value_counts() == 1).all()


def test_multi_component_factors_split_by_scope():
    factors = pd.DataFrame({
        "activity_type": ["diesel", "diesel"], "component": ["primary", "wtt"], "scope": [1, 3],
        "category": ["Combustion", "Cat 3"], "unit": ["litre", "litre"], "kgco2e_per_unit": [2.0, 0.5],
    })
    act = make_activity([["2024-01", "A", "diesel", 1000, "litre"]])
    out = calculate_emissions(act, factors)
    assert len(out) == 2
    assert out.groupby("scope")["tco2e"].sum().to_dict() == pytest.approx({1: 2.0, 3: 0.5})


def test_grid_factor_csv_matches_derivation():
    from carbon.grid_factor import derive
    d = derive()
    f = load_factors().set_index(["activity_type", "component"])["kgco2e_per_unit"]
    for comp in ("primary", "wtt", "td_losses"):
        assert f[("grid_electricity_ng", comp)] == pytest.approx(d[comp], abs=1e-5)


def test_spend_is_deflated_to_2022_usd():
    from carbon.emissions import to_constant_usd
    defl = pd.DataFrame({"year": [2022, 2024], "cpi_u": [100.0, 110.0]})
    act = make_activity([["2024-03", "A", "purchased_steel", 1100, "USD"], ["2024-03", "A", "diesel", 5, "litre"]])
    out = to_constant_usd(act, defl)
    assert out["quantity"].tolist() == pytest.approx([1000.0, 5.0])
    assert out["unit"].tolist() == ["USD2022", "litre"]
    with pytest.raises(ValueError, match="deflator"):
        to_constant_usd(make_activity([["2030-01", "A", "x", 1, "USD"]]), defl)


def test_nominal_usd_cannot_meet_2022_usd_factor():
    factors = pd.DataFrame({"activity_type": ["purchased_steel"], "scope": [3], "category": ["Cat 1"],
                            "unit": ["USD2022"], "kgco2e_per_unit": [0.787]})
    with pytest.raises(ValueError, match="Unit mismatch"):
        calculate_emissions(make_activity([["2024-01", "A", "purchased_steel", 100, "USD"]]), factors)


def test_sample_data_runs_end_to_end():
    out = calculate_emissions(load_activity(), load_factors())
    assert out["tco2e"].sum() > 0
    assert set(out["scope"]) == {1, 2, 3}
