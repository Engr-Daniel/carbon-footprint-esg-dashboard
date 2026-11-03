"""Export report-ready charts to reports/figures/.

Run:  python -m carbon.report_figures   (from the src/ directory)
  or: python src/carbon/report_figures.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from carbon.emissions import (  # noqa: E402
    ROOT,
    calculate_emissions,
    load_activity,
    load_factors,
    reduction_vs_baseline,
    summarise,
)

FIG_DIR = ROOT / "reports" / "figures"
SCOPE_COLORS = {1: "#2a6f97", 2: "#f4a261", 3: "#2a9d8f"}
SCEN_NOTE = "Lever costs are modelled assumptions (see data/reference/*.csv). "
FOOTNOTE = "Synthetic data: EcoNaija Manufacturing Ltd (fictional). Factors: DESNZ 2026, Ember 2025, US EPA v1.3."


def _style(ax, title: str, ylabel: str = "tCO2e"):
    ax.set_title(title, loc="left", fontsize=13, fontweight="bold")
    ax.set_ylabel(ylabel)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.3)


def _save(fig, name: str):
    fig.text(0.01, 0.01, FOOTNOTE, fontsize=7, color="grey")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    path = FIG_DIR / name
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def scope_by_year(em):
    pivot = summarise(em, ["year", "scope"]).pivot(index="year", columns="scope", values="tco2e")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bottom = None
    for scope in pivot.columns:
        ax.bar(pivot.index.astype(str), pivot[scope], bottom=bottom, label=f"Scope {scope}",
               color=SCOPE_COLORS[scope])
        bottom = pivot[scope] if bottom is None else bottom + pivot[scope]
    for x, total in zip(pivot.index.astype(str), pivot.sum(axis=1)):
        ax.text(x, total, f"{total:,.0f}", ha="center", va="bottom", fontsize=9)
    ax.legend(frameon=False)
    _style(ax, "Emissions by scope and year")
    return _save(fig, "01_emissions_by_scope_year.png")


def hotspots(em):
    hot = summarise(em, ["category", "scope"]).groupby(["category", "scope"], as_index=False)["tco2e"].sum()
    hot = hot.sort_values("tco2e")
    total = hot["tco2e"].sum()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(hot["category"], hot["tco2e"], color=[SCOPE_COLORS[s] for s in hot["scope"]])
    for y, v in enumerate(hot["tco2e"]):
        ax.text(v, y, f"  {v / total:.0%}", va="center", fontsize=8)
    _style(ax, "Emission hotspots by category (2023-2025)", "")
    ax.set_xlabel("tCO2e")
    ax.grid(axis="x", alpha=0.3)
    ax.grid(axis="y", visible=False)
    return _save(fig, "02_emission_hotspots.png")


def target_progress(em, baseline_year=2023, target_pct=30, target_year=2030):
    prog = reduction_vs_baseline(em, baseline_year)
    base = prog.loc[prog["year"] == baseline_year, "tco2e"].iloc[0]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(prog["year"], prog["tco2e"], marker="o", color="#264653", label="Actual")
    ax.plot([baseline_year, target_year], [base, base * (1 - target_pct / 100)], linestyle="--",
            color="#e76f51", label=f"{target_pct}% by {target_year} pathway")
    for _, r in prog.iterrows():
        ax.annotate(f"{r['pct_change_vs_baseline']:+.1f}%", (r["year"], r["tco2e"]),
                    textcoords="offset points", xytext=(0, 8), ha="center", fontsize=9)
    ax.set_ylim(0, base * 1.15)
    ax.legend(frameon=False)
    _style(ax, f"Progress vs {target_pct}% reduction target (baseline {baseline_year})")
    return _save(fig, "03_target_progress.png")


def site_breakdown(em):
    site = summarise(em, ["site", "scope"]).pivot(index="site", columns="scope", values="tco2e").fillna(0)
    site = site.loc[site.sum(axis=1).sort_values().index]
    fig, ax = plt.subplots(figsize=(8, 3.8))
    left = None
    for scope in site.columns:
        ax.barh(site.index, site[scope], left=left, label=f"Scope {scope}", color=SCOPE_COLORS[scope])
        left = site[scope] if left is None else left + site[scope]
    ax.legend(frameon=False, loc="lower right")
    _style(ax, "Emissions by site (2023-2025)", "")
    ax.set_xlabel("tCO2e")
    return _save(fig, "04_emissions_by_site.png")


def macc(lever_results):
    """Marginal abatement cost curve: bar width = abatement, height = cost per tCO2e."""
    df = lever_results.sort_values("cost_per_tco2e_usd").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    x = 0.0
    for r in df.itertuples():
        color = "#2a9d8f" if r.cost_per_tco2e_usd < 0 else ("#e9c46a" if r.cost_per_tco2e_usd <= 100 else "#e76f51")
        hatch = "//" if r.accounting == "market" else None
        ax.bar(x, r.cost_per_tco2e_usd, width=r.abatement_tco2e, align="edge", color=color,
               edgecolor="white", hatch=hatch)
        ypos = r.cost_per_tco2e_usd + (15 if r.cost_per_tco2e_usd >= 0 else -15)
        ax.text(x + r.abatement_tco2e / 2, ypos, r.lever_id, ha="center",
                va="bottom" if r.cost_per_tco2e_usd >= 0 else "top", fontsize=9, fontweight="bold")
        x += r.abatement_tco2e
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlim(0, x)
    _style(ax, "Marginal abatement cost curve (2025 baseline)", "USD per tCO2e (annualised)")
    ax.set_xlabel("Annual abatement (tCO2e/yr)  -  hatched = market-based only (PPA / I-RECs)")
    legend = "\n".join(f"{r.lever_id}: {(r.lever[:52] + "…") if len(r.lever) > 52 else r.lever}" for r in df.sort_values("lever_id").itertuples())
    ax.text(1.01, 1.0, legend, transform=ax.transAxes, fontsize=7.5, va="top", family="monospace")
    fig.text(0.01, 0.01, SCEN_NOTE + FOOTNOTE, fontsize=7, color="grey")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    path = FIG_DIR / "05_macc_curve.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def pathway_chart(path_df):
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(path_df.year, path_df.actual, marker="o", color="#264653", label="Actual", linewidth=2)
    ax.plot(path_df.year, path_df.bau, color="grey", linestyle=":", label="Business as usual (+2%/yr)")
    ax.plot(path_df.year, path_df.with_levers_location, color="#2a6f97", label="With levers (location-based)")
    ax.plot(path_df.year, path_df.with_levers_market, color="#2a9d8f", label="With levers + PPA (market-based)")
    ax.plot(path_df.year, path_df.sbti_target, color="#e76f51", linestyle="--",
            label="SBTi-aligned target (S1+2: 4.2%/yr, S3: 2.5%/yr)")
    ax.axvline(2030, color="lightgrey", linewidth=0.8)
    ax.set_ylim(0, path_df[["bau", "actual"]].max().max() * 1.1)
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    _style(ax, "Decarbonisation pathway to 2035")
    fig.text(0.01, 0.01, SCEN_NOTE + FOOTNOTE, fontsize=7, color="grey")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    path = FIG_DIR / "06_decarbonisation_pathway.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def main():
    from carbon.scenarios import apply_levers, baseline_activity, load_cost_assumptions, load_levers, pathway

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    act, factors = load_activity(), load_factors()
    em = calculate_emissions(act, factors)
    for fn in (scope_by_year, hotspots, target_progress, site_breakdown):
        print("saved", fn(em).relative_to(ROOT))
    a = load_cost_assumptions()
    res, _ = apply_levers(baseline_activity(act, 2025), load_levers(), factors, a, 2025)
    print("saved", macc(res).relative_to(ROOT))
    print("saved", pathway_chart(pathway(em, res, 2023, 2025, 2035, a["bau_growth_rate"])).relative_to(ROOT))


if __name__ == "__main__":
    main()
