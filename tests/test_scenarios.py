import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from carbon import calculate_emissions, load_activity, load_factors  # noqa: E402
from carbon.scenarios import (  # noqa: E402
    apply_levers,
    baseline_activity,
    crf,
    intensity_metrics,
    load_cost_assumptions,
    load_levers,
    load_profile,
    pathway,
    scope2_dual,
)

FACTORS = pd.DataFrame({
    "activity_type": ["diesel", "grid_electricity_ng"],
    "scope": [1, 2],
    "category": ["Combustion", "Electricity"],
    "unit": ["litre", "kWh"],
    "kgco2e_per_unit": [2.0, 0.5],
})
ASSUMPTIONS = {
    "fx_ngn_per_usd": 1000, "diesel_price_ngn_per_litre": 2000, "petrol_price_ngn_per_litre": 1000,
    "grid_tariff_ngn_per_kwh": 100, "flight_domestic_usd_per_pkm": 0.2, "flight_longhaul_usd_per_pkm": 0.1,
    "refrigerant_usd_per_kg": 25, "landfill_gate_fee_usd_per_tonne": 25, "discount_rate": 0.0,
    "bau_growth_rate": 0.0,
}
BASELINE = pd.DataFrame({
    "site": ["A", "A", "B"],
    "activity_type": ["diesel", "grid_electricity_ng", "grid_electricity_ng"],
    "unit": ["litre", "kWh", "kWh"],
    "quantity": [1000.0, 10000.0, 10000.0],
})


def lever(**kw):
    base = dict(lever_id="X", order=1, lever="x", activity_types="diesel", sites="All", reduction_pct=0.5,
                start_year=2026, capex_usd=0, annual_opex_usd=0, lifetime_years=10, accounting="location")
    base.update(kw)
    return base


def test_crf():
    assert crf(0.0, 10) == pytest.approx(0.1)
    assert crf(0.12, 15) == pytest.approx(0.14682, rel=1e-4)
    with pytest.raises(ValueError):
        crf(0.1, 0)


def test_single_lever_abatement_and_savings():
    levers = pd.DataFrame([lever(capex_usd=10000, lifetime_years=10)])
    res, residual = apply_levers(BASELINE, levers, FACTORS, ASSUMPTIONS, 2025)
    r = res.iloc[0]
    assert r.abatement_tco2e == pytest.approx(1.0)          # 500 L x 2 kg / 1000
    assert r.annual_savings_usd == pytest.approx(1000.0)     # 500 L x USD 2
    assert r.annualised_cost_usd == pytest.approx(0.0)       # 10000/10 - 1000
    assert residual.loc[residual.activity_type == "diesel", "quantity"].iloc[0] == pytest.approx(500)


def test_levers_are_sequential_no_double_counting():
    levers = pd.DataFrame([
        lever(lever_id="L1", order=1, activity_types="grid_electricity_ng", reduction_pct=0.5),
        lever(lever_id="L2", order=2, activity_types="grid_electricity_ng", reduction_pct=0.5),
    ])
    res, _ = apply_levers(BASELINE, levers, FACTORS, ASSUMPTIONS, 2025)
    assert res.abatement_tco2e.tolist() == pytest.approx([5.0, 2.5])  # second lever acts on residual


def test_site_filter():
    levers = pd.DataFrame([lever(activity_types="grid_electricity_ng", sites="B", reduction_pct=1.0)])
    res, _ = apply_levers(BASELINE, levers, FACTORS, ASSUMPTIONS, 2025)
    assert res.abatement_tco2e.iloc[0] == pytest.approx(5.0)


def test_market_lever_does_not_change_activity():
    levers = pd.DataFrame([lever(activity_types="grid_electricity_ng", reduction_pct=0.5, accounting="market")])
    res, residual = apply_levers(BASELINE, levers, FACTORS, ASSUMPTIONS, 2025)
    assert res.annual_savings_usd.iloc[0] == 0
    assert residual["quantity"].sum() == pytest.approx(BASELINE["quantity"].sum())


def test_lever_matching_nothing_raises():
    levers = pd.DataFrame([lever(activity_types="petrol")])
    with pytest.raises(ValueError, match="matches no baseline"):
        apply_levers(BASELINE, levers, FACTORS, ASSUMPTIONS, 2025)


def test_scope2_dual():
    em = calculate_emissions(load_activity(), load_factors())
    out = scope2_dual(em, {2025: 1e12})  # over-coverage is capped at total kWh
    row = out[out.year == 2025].iloc[0]
    assert row.market_tco2e == pytest.approx(0)
    assert out[out.year == 2023].iloc[0].market_tco2e == pytest.approx(out[out.year == 2023].iloc[0].location_tco2e)


def test_full_model_runs_and_pathway_is_consistent():
    act, f = load_activity(), load_factors()
    em = calculate_emissions(act, f)
    a = load_cost_assumptions()
    res, _ = apply_levers(baseline_activity(act, 2025), load_levers(), f, a, 2025)
    p = pathway(em, res, 2023, 2025, 2035, a["bau_growth_rate"])
    assert p.loc[p.year == 2023, "sbti_target"].iloc[0] == pytest.approx(p.loc[p.year == 2023, "actual"].iloc[0])
    later = p[p.year > 2027]
    assert (later.with_levers_market <= later.with_levers_location).all()
    assert (later.with_levers_location < later.bau).all()
    ints = intensity_metrics(em, load_profile())
    assert (ints.tco2e_per_employee > 0).all()
