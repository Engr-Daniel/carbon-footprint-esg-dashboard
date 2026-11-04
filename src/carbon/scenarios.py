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
INSTRUMENTS_PATH = ROOT / "data" / "sample" / "contractual_instruments.csv"

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
        # Commuting is paid by employees; supplier engagement lowers emissions per dollar, not spend.
        # Any activity not listed here (e.g. purchased_* spend) has zero direct cost saving.
        "employee_commute_car": 0.0,
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
    return select_factors(factors, [year])[["activity_type", "component", "scope", "kgco2e_per_unit"]]


def apply_levers(
    baseline: pd.DataFrame,
    levers: pd.DataFrame,
    factors: pd.DataFrame,
    assumptions: dict[str, float],
    year: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply levers sequentially. Returns (lever results, residual activity).

    Abatement counts every factor component of the avoided activity (e.g. avoided diesel cuts
    Scope 1 combustion *and* Scope 3 Cat 3 upstream). Market-based levers only remove the
    Scope 2 component, because contractual instruments do not change physical supply chains.
    """
    fmap = _factor_map(factors, year)
    missing = set(baseline["activity_type"]) - set(fmap["activity_type"])
    if missing:
        raise ValueError(f"Baseline contains activity types without emission factors: {sorted(missing)}")
    residual = baseline.copy()
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
        avoided = residual.loc[mask, ["activity_type"]].assign(qty=residual.loc[mask, "quantity"] * lev.reduction_pct)
        comp = avoided.merge(fmap, on="activity_type")
        if lev.accounting == "market":
            comp = comp[comp["scope"] == 2]
        elif lev.accounting != "location":
            raise ValueError(f"Unknown accounting type '{lev.accounting}' for {lev.lever_id}.")
        comp_t = comp["qty"] * comp["kgco2e_per_unit"] / 1000
        ab_s12 = float(comp_t[comp["scope"].isin([1, 2])].sum())
        ab_s3 = float(comp_t[comp["scope"] == 3].sum())
        if lev.accounting == "location":
            savings = float(sum(q * costs.get(t, 0.0) for q, t in zip(avoided["qty"], avoided["activity_type"])))
            residual.loc[mask, "quantity"] -= avoided["qty"]
        else:
            savings = 0.0  # contractual instrument: activity unchanged, premium sits in opex
        abatement_t = ab_s12 + ab_s3
        primary_scope = int(fmap.loc[fmap["activity_type"].isin(types) & (fmap["component"] == "primary"), "scope"].min())
        annualised = lev.capex_usd * crf(rate, int(lev.lifetime_years)) + lev.annual_opex_usd - savings
        rows.append({
            "lever_id": lev.lever_id,
            "lever": lev.lever,
            "accounting": lev.accounting,
            "start_year": int(lev.start_year),
            "ramp_years": int(getattr(lev, "ramp_years", 1) or 1),
            "scope": primary_scope,
            "abatement_tco2e": abatement_t,
            "abatement_s12": ab_s12,
            "abatement_s3": ab_s3,
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
    Levers phase in linearly over `ramp_years` from `start_year` (1 = full effect immediately).
    Columns are given for the total and for Scope 1+2 ("_s12") and Scope 3 ("_s3").
    """
    em = emissions.assign(group=emissions["scope"].map({1: "s12", 2: "s12", 3: "s3"}))
    hist = em.groupby(["year", "group"])["tco2e"].sum().unstack()
    lr = lever_results
    rates = {"s12": SBTI_RATE_S12, "s3": SBTI_RATE_S3}
    rows = []
    for y in range(base_year, end_year + 1):
        row = {"year": y}
        g = (1 + growth) ** (y - baseline_year)
        active = lr[lr["start_year"] <= y]
        ramp = ramp_fraction(active, y)
        for grp in ("s12", "s3"):
            row[f"actual_{grp}"] = hist[grp].get(y, float("nan"))
            row[f"sbti_target_{grp}"] = hist.loc[base_year, grp] * max(0.0, 1 - rates[grp] * (y - base_year))
            if y >= baseline_year:
                col = f"abatement_{grp}"
                eff = active[col] * ramp
                loc = eff[active["accounting"] == "location"].sum() * g
                mkt = eff[active["accounting"] == "market"].sum() * g
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


def ramp_fraction(lever_results: pd.DataFrame, year: int) -> pd.Series:
    """Share of each lever's full abatement achieved in `year` (linear ramp-up)."""
    ramp = lever_results.get("ramp_years", pd.Series(1, index=lever_results.index)).clip(lower=1)
    return ((year - lever_results["start_year"] + 1) / ramp).clip(lower=0, upper=1)


def pathway_range(
    emissions: pd.DataFrame,
    baseline: pd.DataFrame,
    levers: pd.DataFrame,
    factors: pd.DataFrame,
    assumptions: dict[str, float],
    base_year: int = 2023,
    baseline_year: int = 2025,
    end_year: int = 2035,
) -> pd.DataFrame:
    """Central pathway plus low/high bands from each lever's reduction_pct_low/high."""
    out = None
    for case, col in (("central", "reduction_pct"), ("low", "reduction_pct_low"), ("high", "reduction_pct_high")):
        lev = levers.assign(reduction_pct=levers[col]) if col in levers else levers
        res, _ = apply_levers(baseline, lev, factors, assumptions, baseline_year)
        p = pathway(emissions, res, base_year, baseline_year, end_year, assumptions["bau_growth_rate"])
        if out is None:
            out = p.copy()
        else:
            for c in ("with_levers_location", "with_levers_market"):
                # "low" abatement case gives the HIGHER emissions bound
                out[f"{c}_{'upper' if case == 'low' else 'lower'}"] = p[c]
    return out


def sensitivity_analysis(
    activity: pd.DataFrame,
    emissions: pd.DataFrame,
    levers: pd.DataFrame,
    factors: pd.DataFrame,
    assumptions: dict[str, float],
    baseline_year: int = 2025,
    target_year: int = 2030,
    capex_range: float = 0.25,
) -> pd.DataFrame:
    """One-at-a-time (tornado) sensitivity of net annual saving and target-year gap."""
    base = baseline_activity(activity, baseline_year)

    def run(a=assumptions, lev=levers):
        res, _ = apply_levers(base, lev, factors, a, baseline_year)
        p = pathway(emissions, res, 2023, baseline_year, target_year, a["bau_growth_rate"])
        row = p[p.year == target_year].iloc[0]
        return -res["annualised_cost_usd"].sum(), row.with_levers_market - row.sbti_target

    cases = {
        "Diesel price ±30%": ("diesel_price_ngn_per_litre", 0.7, 1.3),
        "FX (₦/USD) ±25%": ("fx_ngn_per_usd", 0.75, 1.25),
        "Grid tariff ±30%": ("grid_tariff_ngn_per_kwh", 0.7, 1.3),
        "Discount rate 8% / 18%": ("discount_rate", 0.08 / assumptions["discount_rate"], 0.18 / assumptions["discount_rate"]),
        "BAU growth 0% / 4%": ("bau_growth_rate", 0.0, 2.0),
    }
    rows = []
    for name, (key, lo, hi) in cases.items():
        s_lo, g_lo = run({**assumptions, key: assumptions[key] * lo})
        s_hi, g_hi = run({**assumptions, key: assumptions[key] * hi})
        rows.append({"parameter": name, "net_saving_low": s_lo, "net_saving_high": s_hi, "gap_low": g_lo, "gap_high": g_hi})
    for name, lev in (("Lever capex ±25%", None), ("Lever effectiveness low / high", "eff")):
        if lev is None:
            lo_l = levers.assign(capex_usd=levers.capex_usd * (1 - capex_range))
            hi_l = levers.assign(capex_usd=levers.capex_usd * (1 + capex_range))
        else:
            lo_l = levers.assign(reduction_pct=levers.get("reduction_pct_low", levers.reduction_pct))
            hi_l = levers.assign(reduction_pct=levers.get("reduction_pct_high", levers.reduction_pct))
        s_lo, g_lo = run(lev=lo_l)
        s_hi, g_hi = run(lev=hi_l)
        rows.append({"parameter": name, "net_saving_low": s_lo, "net_saving_high": s_hi, "gap_low": g_lo, "gap_high": g_hi})
    out = pd.DataFrame(rows)
    out["saving_swing"] = (out.net_saving_high - out.net_saving_low).abs()
    return out.sort_values("saving_swing", ascending=False).reset_index(drop=True)


def intensity_metrics(emissions: pd.DataFrame, profile: pd.DataFrame) -> pd.DataFrame:
    """tCO2e per employee, per USD million revenue and kgCO2e per tonne of product."""
    yearly = summarise(emissions, ["year"]).merge(profile, on="year", how="inner")
    yearly["tco2e_per_employee"] = yearly["tco2e"] / yearly["employees"]
    yearly["tco2e_per_usd_m_revenue"] = yearly["tco2e"] / yearly["revenue_usd_m"]
    yearly["kgco2e_per_tonne_product"] = yearly["tco2e"] * 1000 / yearly["production_tonnes"]
    return yearly


def load_instruments(path: Path | str = INSTRUMENTS_PATH) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"registry": str}, keep_default_na=False)


def validate_instruments(
    instruments: pd.DataFrame, consumption_country: str = "NG", vintage_tolerance_years: int = 0
) -> pd.DataFrame:
    """Check contractual instruments against GHG Protocol Scope 2 Quality Criteria.

    An instrument may only carry a zero (or supplier-specific) factor in market-based Scope 2 if it:
      1. conveys the energy-attribute claim (certificates bundled or unbundled; a bare PPA does not)
      2. is uniquely claimed: retired/cancelled on behalf of the reporting company
      3. is tracked and redeemed in a recognised registry
      4. has a generation vintage matching the reporting year (within the tolerance)
      5. comes from the same market (grid/country) as the consumption
      6. is not double counted (unique instrument ID)
    Returns the table with a pass/fail per criterion, an `eligible` flag and the failure reasons.
    """
    df = instruments.copy()
    truthy = lambda c: df[c].astype(str).str.lower().isin(["true", "1", "yes"])  # noqa: E731
    checks = {
        "conveys_attributes_ok": truthy("conveys_attributes"),
        "retired_ok": truthy("retired_for_company"),
        "registry_ok": df["registry"].astype(str).str.strip().ne(""),
        "vintage_ok": (df["reporting_year_claimed"] - df["generation_year"]).abs() <= vintage_tolerance_years,
        "market_ok": df["generation_country"].eq(consumption_country),
        "unique_ok": ~df["instrument_id"].duplicated(keep="first"),
    }
    reasons = {
        "conveys_attributes_ok": "no attribute claim", "retired_ok": "not retired for company",
        "registry_ok": "no registry", "vintage_ok": "vintage mismatch", "market_ok": "different market",
        "unique_ok": "duplicate ID",
    }
    for k, v in checks.items():
        df[k] = v
    df["eligible"] = pd.concat(checks.values(), axis=1).all(axis=1)
    df["failure_reasons"] = df.apply(lambda r: "; ".join(reasons[k] for k in checks if not r[k]), axis=1)
    return df


def eligible_kwh_by_year(validated: pd.DataFrame) -> dict[int, float]:
    """Eligible contractual kWh per reporting year (from validate_instruments output)."""
    ok = validated[validated["eligible"]]
    return (ok.groupby("reporting_year_claimed")["mwh"].sum() * 1000).to_dict()


def scope2_dual(
    emissions: pd.DataFrame,
    contractual_kwh: dict[int, float] | None = None,
    residual_mix_kg_per_kwh: float | None = None,
) -> pd.DataFrame:
    """Location- vs market-based Scope 2 by year (GHG Protocol Scope 2 Guidance).

    Pass only *validated* contractual kWh (see validate_instruments / eligible_kwh_by_year):
    these get a zero factor. Uncovered kWh use the residual mix; Nigeria has no published
    residual mix, so the grid average is the fallback (this overstates nothing but may
    double count attributes already sold - disclose it).
    """
    s2 = emissions[emissions["scope"] == 2]
    out = s2.groupby("year").agg(kwh=("quantity", "sum"), location_tco2e=("tco2e", "sum")).reset_index()
    avg_factor = out["location_tco2e"] * 1000 / out["kwh"]
    factor = residual_mix_kg_per_kwh if residual_mix_kg_per_kwh is not None else avg_factor
    covered = out["year"].map(contractual_kwh or {}).fillna(0).clip(upper=out["kwh"])
    out["contractual_kwh"] = covered
    out["market_tco2e"] = (out["kwh"] - covered) * factor / 1000
    return out
