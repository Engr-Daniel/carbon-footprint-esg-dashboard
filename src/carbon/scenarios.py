"""Decarbonisation scenario modelling: reduction levers, MACC, pathways, intensity and dual Scope 2.

Method
------
1. Baseline = annual activity in the latest actual year (default 2025), by site and activity type.
2. Levers are applied **in order** to the *residual* activity, so overlapping levers are not
   double-counted (e.g. efficiency first, then solar on the reduced load).
3. Physical ("location") levers reduce activity. Contractual ("market") levers (PPAs, I-RECs)
   leave activity unchanged and only reduce market-based Scope 2.
4. Annualised cost = capex x CRF(discount rate, lifetime) + annual opex - annual energy/fuel savings.
   Cost per tCO2e = annualised cost / annual abatement  (negative = saves money).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .emissions import ROOT, select_factors, summarise

LEVERS_PATH = ROOT / "data" / "reference" / "reduction_levers.csv"
COSTS_PATH = ROOT / "data" / "reference" / "cost_assumptions.csv"
PROFILE_PATH = ROOT / "data" / "sample" / "company_profile.csv"

# SBTi Corporate Near-Term Criteria (Absolute Contraction Approach), minimum linear annual rates:
SBTI_RATE_S12 = 0.042  # Scope 1+2, 1.5C-aligned
SBTI_RATE_S3 = 0.025   # Scope 3, well-below-2C (required when Scope 3 >= 40% of total)


def load_levers(path: Path | str = LEVERS_PATH) -> pd.DataFrame:
    return pd.read_csv(path).sort_values("order").reset_index(drop=True)


def load_cost_assumptions(path: Path | str = COSTS_PATH) -> dict[str, float]:
    df = pd.read_csv(path)
    return dict(zip(df["parameter"], df["value"].astype(float)))


def load_profile(path: Path | str = PROFILE_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def unit_costs_usd(a: dict[str, float]) -> dict[str, float]:
    """Cost in USD per unit of avoided activity (what the company stops paying for)."""
    fx = a["fx_ngn_per_usd"]
    return {
        "diesel": a["diesel_price_ngn_per_litre"] / fx,
        "petrol": a["petrol_price_ngn_per_litre"] / fx,
        "grid_electricity_ng": a["grid_tariff_ngn_per_kwh"] / fx,
        "business_travel_air_domestic": a["flight_domestic_usd_per_pkm"],
        "business_travel_air_longhaul": a["flight_longhaul_usd_per_pkm"],
        "refrigerant_r410a": a["refrigerant_usd_per_kg"],
        "waste_landfill": a["landfill_gate_fee_usd_per_tonne"],
        # Commuting is paid by employees; supplier engagement does not reduce spend.
        "employee_commute_car": 0.0,
        "purchased_goods_spend": 0.0,
    }


def crf(rate: float, years: int) -> float:
    """Capital recovery factor: converts an upfront capex into an equivalent annual cost."""
    if years <= 0:
        raise ValueError("Lifetime must be positive.")
    if rate == 0:
        return 1 / years
    return rate * (1 + rate) ** years / ((1 + rate) ** years - 1)


def baseline_activity(activity: pd.DataFrame, year: int) -> pd.DataFrame:
    """Annual activity totals for one year, by site and activity type."""
    base = activity[activity["year"] == year]
    if base.empty:
        raise ValueError(f"No activity data for baseline year {year}.")
    return base.groupby(["site", "activity_type", "unit"], as_index=False)["quantity"].sum()


def _factor_map(factors: pd.DataFrame, year: int) -> pd.DataFrame:
    return select_factors(factors, [year])[["activity_type", "scope", "kgco2e_per_unit"]]


def apply_levers(
    baseline: pd.DataFrame,
    levers: pd.DataFrame,
    factors: pd.DataFrame,
    assumptions: dict[str, float],
    year: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply levers sequentially. Returns (lever results, residual activity)."""
    fmap = _factor_map(factors, year)
    residual = baseline.merge(fmap, on="activity_type", how="left")
    if residual["kgco2e_per_unit"].isna().any():
        raise ValueError("Baseline contains activity types without emission factors.")
    costs = unit_costs_usd(assumptions)
    rate = assumptions["discount_rate"]
    rows = []
    for lev in levers.itertuples(index=False):
        types = str(lev.activity_types).split(";")
        mask = residual["activity_type"].isin(types)
        if lev.sites != "All":
            mask &= residual["site"].isin(str(lev.sites).split(";"))
        if not mask.any():
            raise ValueError(f"Lever {lev.lever_id} matches no baseline activity.")
        avoided = residual.loc[mask, "quantity"] * lev.reduction_pct
        abatement_t = float((avoided * residual.loc[mask, "kgco2e_per_unit"]).sum() / 1000)
        if lev.accounting == "location":
            savings = float(sum(q * costs.get(t, 0.0) for q, t in zip(avoided, residual.loc[mask, "activity_type"])))
            residual.loc[mask, "quantity"] -= avoided
        elif lev.accounting == "market":
            savings = 0.0  # contractual instrument: activity unchanged, premium sits in opex
        else:
            raise ValueError(f"Unknown accounting type '{lev.accounting}' for {lev.lever_id}.")
        annualised = lev.capex_usd * crf(rate, int(lev.lifetime_years)) + lev.annual_opex_usd - savings
        rows.append({
            "lever_id": lev.lever_id,
            "lever": lev.lever,
            "accounting": lev.accounting,
            "start_year": int(lev.start_year),
            "scope": int(residual.loc[mask, "scope"].iloc[0]),
            "abatement_tco2e": abatement_t,
            "capex_usd": float(lev.capex_usd),
            "annual_savings_usd": savings,
            "annualised_cost_usd": annualised,
            "cost_per_tco2e_usd": annualised / abatement_t if abatement_t else float("nan"),
            "simple_payback_years": (lev.capex_usd / (savings - lev.annual_opex_usd)
                                     if savings > lev.annual_opex_usd and lev.capex_usd > 0 else float("nan")),
        })
    return pd.DataFrame(rows), residual


def pathway(
    emissions: pd.DataFrame,
    lever_results: pd.DataFrame,
    base_year: int,
    baseline_year: int,
    end_year: int = 2035,
    growth: float = 0.02,
) -> pd.DataFrame:
    """Actual history, BAU projection, with-lever projections and SBTi-aligned target lines.

    base_year:     target base year (e.g. 2023)
    baseline_year: last actual year that projections start from (e.g. 2025)
    Columns are given for the total and for Scope 1+2 ("_s12") and Scope 3 ("_s3").
    """
    em = emissions.assign(group=emissions["scope"].map({1: "s12", 2: "s12", 3: "s3"}))
    hist = em.groupby(["year", "group"])["tco2e"].sum().unstack()
    lr = lever_results.assign(group=lever_results["scope"].map({1: "s12", 2: "s12", 3: "s3"}))
    rates = {"s12": SBTI_RATE_S12, "s3": SBTI_RATE_S3}
    rows = []
    for y in range(base_year, end_year + 1):
        row = {"year": y}
        g = (1 + growth) ** (y - baseline_year)
        active = lr[lr["start_year"] <= y]
        for grp in ("s12", "s3"):
            row[f"actual_{grp}"] = hist[grp].get(y, float("nan"))
            row[f"sbti_target_{grp}"] = hist.loc[base_year, grp] * max(0.0, 1 - rates[grp] * (y - base_year))
            if y >= baseline_year:
                a = active[active["group"] == grp]
                loc = a.loc[a["accounting"] == "location", "abatement_tco2e"].sum() * g
                mkt = a.loc[a["accounting"] == "market", "abatement_tco2e"].sum() * g
                start = hist.loc[baseline_year, grp]
                row[f"bau_{grp}"] = start * g
                row[f"with_levers_location_{grp}"] = start * g - loc
                row[f"with_levers_market_{grp}"] = start * g - loc - mkt
        rows.append(row)
    out = pd.DataFrame(rows)
    for col in ("actual", "sbti_target", "bau", "with_levers_location", "with_levers_market"):
        if f"{col}_s12" in out:
            out[col] = out[f"{col}_s12"] + out[f"{col}_s3"]
    return out


def intensity_metrics(emissions: pd.DataFrame, profile: pd.DataFrame) -> pd.DataFrame:
    """tCO2e per employee, per USD million revenue and kgCO2e per tonne of product."""
    yearly = summarise(emissions, ["year"]).merge(profile, on="year", how="inner")
    yearly["tco2e_per_employee"] = yearly["tco2e"] / yearly["employees"]
    yearly["tco2e_per_usd_m_revenue"] = yearly["tco2e"] / yearly["revenue_usd_m"]
    yearly["kgco2e_per_tonne_product"] = yearly["tco2e"] * 1000 / yearly["production_tonnes"]
    return yearly


def scope2_dual(
    emissions: pd.DataFrame,
    contractual_kwh: dict[int, float] | None = None,
    residual_mix_kg_per_kwh: float | None = None,
) -> pd.DataFrame:
    """Location- vs market-based Scope 2 by year (GHG Protocol Scope 2 Guidance).

    Contractual kWh (PPAs, I-RECs) get a zero factor. Uncovered kWh use the residual mix;
    Nigeria has no published residual mix, so the grid average is the fallback.
    """
    s2 = emissions[emissions["scope"] == 2]
    out = s2.groupby("year").agg(kwh=("quantity", "sum"), location_tco2e=("tco2e", "sum")).reset_index()
    avg_factor = out["location_tco2e"] * 1000 / out["kwh"]
    factor = residual_mix_kg_per_kwh if residual_mix_kg_per_kwh is not None else avg_factor
    covered = out["year"].map(contractual_kwh or {}).fillna(0).clip(upper=out["kwh"])
    out["contractual_kwh"] = covered
    out["market_tco2e"] = (out["kwh"] - covered) * factor / 1000
    return out
