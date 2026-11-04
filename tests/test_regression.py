"""Regression checks: headline results must not drift silently.

If a deliberate change to data, factors or method moves these numbers, update the expected
values here AND the README / MEMORY.md / executive summary in the same commit.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from carbon import calculate_emissions, load_activity, load_factors, summarise  # noqa: E402
from carbon.scenarios import (apply_levers, baseline_activity, load_cost_assumptions, load_levers,  # noqa: E402
                              pathway_range)

EXPECTED = {
    "total_2023_2025": 17312.7,
    "scope1": 3572.4,
    "scope2": 2848.1,
    "scope3": 10892.2,
    "y2025": 5383.8,
    "physical_abatement": 967.5,
    "net_saving_usd": 124152.0,
    "gap_2030_market": -173.5,
}
REL = 0.005  # 0.5% tolerance


@pytest.fixture(scope="module")
def results():
    act, f = load_activity(), load_factors()
    em = calculate_emissions(act, f)
    a, lev = load_cost_assumptions(), load_levers()
    base = baseline_activity(act, 2025)
    res, _ = apply_levers(base, lev, f, a, 2025)
    p = pathway_range(em, base, lev, f, a)
    p30 = p[p.year == 2030].iloc[0]
    scope = summarise(em, ["scope"]).set_index("scope")["tco2e"]
    return {
        "total_2023_2025": em.tco2e.sum(),
        "scope1": scope[1], "scope2": scope[2], "scope3": scope[3],
        "y2025": em.loc[em.year == 2025, "tco2e"].sum(),
        "physical_abatement": res.loc[res.accounting == "location", "abatement_tco2e"].sum(),
        "net_saving_usd": -res.annualised_cost_usd.sum(),
        "gap_2030_market": p30.with_levers_market - p30.sbti_target,
    }


@pytest.mark.parametrize("key", EXPECTED)
def test_headline_numbers_stable(results, key):
    assert results[key] == pytest.approx(EXPECTED[key], rel=REL, abs=1.0)
