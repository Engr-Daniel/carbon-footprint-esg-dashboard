"""EcoNaija carbon footprint & decarbonisation dashboard.

Run:  streamlit run app/streamlit_app.py
UI only - all calculations live in src/carbon (see AGENTS.md).
"""
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from carbon import calculate_emissions, load_activity, load_factors, reduction_vs_baseline, summarise  # noqa: E402
from carbon.scenarios import (  # noqa: E402
    apply_levers,
    baseline_activity,
    eligible_kwh_by_year,
    intensity_metrics,
    load_cost_assumptions,
    load_instruments,
    load_levers,
    load_profile,
    pathway_range,
    scope2_dual,
    sensitivity_analysis,
    validate_instruments,
)

# ----------------------------------------------------------------------------- design tokens
SURFACE, CARD, BORDER, GRID = "#fcfcfb", "#ffffff", "#e7e5e0", "#ecebe7"
INK, INK2, INK3 = "#0b0b0b", "#52514e", "#8a8984"
SCOPE = {"Scope 1": "#2a78d6", "Scope 2": "#eb6834", "Scope 3": "#1baf7a"}  # validated categorical slots 1-3
SITE = {"Port Harcourt Plant": "#104281", "Lagos HQ": "#2a78d6", "Abuja Office": "#86b6ef"}  # one-hue ramp
GOOD, CRITICAL, WARN = "#0ca30c", "#d03b3b", "#fab219"
TARGET = "#d03b3b"
REPO = "https://github.com/Engr-Daniel/carbon-footprint-esg-dashboard"
NICE = {
    "diesel": "Diesel (generators & fleet)", "petrol": "Petrol (fleet)", "natural_gas": "Natural gas",
    "lpg": "LPG", "refrigerant_r410a": "Refrigerant leaks (R-410A)", "grid_electricity_ng": "Grid electricity",
    "business_travel_air_domestic": "Domestic flights", "business_travel_air_longhaul": "Long-haul flights",
    "employee_commute_car": "Employee commuting", "waste_landfill": "Waste to landfill",
    "purchased_steel": "Steel", "purchased_plastic_resin": "Plastic resin",
    "purchased_corrugated_packaging": "Corrugated packaging", "purchased_plastic_film": "Plastic film",
    "purchased_chemicals": "Chemicals", "purchased_machinery_repair": "Machinery repair",
    "purchased_it_services": "IT services", "purchased_consulting": "Consulting",
    "purchased_cleaning_services": "Cleaning services", "upstream_freight_trucking": "Freight trucking",
}

st.set_page_config(page_title="EcoNaija · Carbon & ESG Dashboard", page_icon="🌍", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown(f"""
<style>
  .block-container {{padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1320px;}}
  h1, h2, h3 {{letter-spacing: -0.01em;}}
  .hero {{padding: 4px 0 14px 0; border-bottom: 1px solid {BORDER}; margin-bottom: 18px;}}
  .hero h1 {{font-size: 1.9rem; margin: 0 0 4px 0; padding: 0;}}
  .hero p {{color: {INK2}; margin: 0; font-size: 0.98rem;}}
  .badge {{display:inline-block; font-size:0.74rem; padding:3px 9px; border-radius:999px; margin:8px 6px 0 0;
           background:#eef4fc; color:#184f95; border:1px solid #d5e5f8;}}
  .badge.warn {{background:#fff6e5; color:#7a5200; border-color:#f6e1b3;}}
  .kpi {{background:{CARD}; border:1px solid {BORDER}; border-radius:14px; padding:16px 18px 14px; min-height:142px;}}
  .kpi .label {{font-size:0.74rem; color:{INK2}; text-transform:uppercase; letter-spacing:0.05em; font-weight:600;}}
  .kpi .value {{font-size:1.75rem; font-weight:700; color:{INK}; line-height:1.25; margin-top:4px;}}
  .kpi .unit {{font-size:0.95rem; font-weight:500; color:{INK2};}}
  .kpi .sub {{font-size:0.8rem; color:{INK2}; margin-top:2px;}}
  .chip {{display:inline-block; font-size:0.78rem; font-weight:600; padding:2px 9px; border-radius:999px; margin-top:6px;}}
  .chip.good {{background:#e8f6e8; color:#0a6b0a;}}
  .chip.bad {{background:#fbeaea; color:#9b2626;}}
  .chip.neutral {{background:#f1f0ec; color:{INK2};}}
  .insight {{background:{CARD}; border:1px solid {BORDER}; border-left:4px solid #2a78d6; border-radius:12px;
             padding:14px 16px; height:100%;}}
  .insight .t {{font-weight:700; font-size:0.95rem; margin-bottom:4px; color:{INK};}}
  .insight .b {{font-size:0.86rem; color:{INK2}; line-height:1.45;}}
  .section-note {{color:{INK2}; font-size:0.88rem; margin:-6px 0 10px 0;}}
  div[data-testid="stTabs"] button p {{font-size:0.95rem; font-weight:600;}}
  div[data-testid="stExpander"] details {{border-radius:12px;}}
  .foot {{color:{INK3}; font-size:0.78rem; margin-top:28px; border-top:1px solid {BORDER}; padding-top:10px;}}
</style>""", unsafe_allow_html=True)


# ----------------------------------------------------------------------------- helpers
def kpi(col, label, value, unit="", sub="", chip=None):
    chip_html = f'<div class="chip {chip[1]}">{chip[0]}</div>' if chip else ""
    col.markdown(f'<div class="kpi"><div class="label">{label}</div><div class="value">{value} '
                 f'<span class="unit">{unit}</span></div><div class="sub">{sub}</div>{chip_html}</div>',
                 unsafe_allow_html=True)


def insight(col, icon, title, body, accent="#2a78d6"):
    col.markdown(f'<div class="insight" style="border-left-color:{accent}"><div class="t">{icon} {title}</div>'
                 f'<div class="b">{body}</div></div>', unsafe_allow_html=True)


def style(fig, title=None, height=380, legend=True, ytitle=None, xtitle=None):
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>" if title else None, font=dict(size=15, color=INK), x=0, xanchor="left"),
        height=height, margin=dict(l=8, r=16, t=48 if title else 12, b=70 if legend else 8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Source Sans Pro, Inter, sans-serif", size=12.5, color=INK2),
        legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="left", x=0, title=None, traceorder="normal",
                    font=dict(size=12, color=INK2)) if legend else None,
        showlegend=legend, hoverlabel=dict(bgcolor="white", bordercolor=BORDER, font=dict(color=INK, size=12.5)),
        barcornerradius=4, bargap=0.38,
    )
    fig.update_xaxes(showgrid=False, linecolor=BORDER, tickcolor=BORDER, title=xtitle, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, gridwidth=1, zeroline=False, title=ytitle, tickformat=",")
    return fig


PLOT_CFG = {"displayModeBar": False}


def show(container, fig):
    container.plotly_chart(fig, width="stretch", config=PLOT_CFG)


def fmt_t(v):
    return f"{v:,.0f}"


# ----------------------------------------------------------------------------- data
@st.cache_data
def get_data():
    activity, factors = load_activity(), load_factors()
    em = calculate_emissions(activity, factors)
    em["scope_label"] = "Scope " + em["scope"].astype(str)
    suffix = em["component"].map({"wtt": " · upstream supply", "td_losses": " · grid losses"}).fillna("")
    em["source"] = em["activity_type"].map(NICE).fillna(em["activity_type"]) + suffix
    return activity, factors, em


@st.cache_data(show_spinner="Running scenario model…")
def run_scenarios(assumption_items: tuple, chosen: tuple):
    a = dict(assumption_items)
    levers = load_levers()
    sel = levers[levers.lever_id.isin(chosen)]
    base = baseline_activity(activity, 2025)
    res, _ = apply_levers(base, sel, factors, a, 2025)
    return res, pathway_range(df, base, sel, factors, a), sensitivity_analysis(activity, df, sel, factors, a)


activity, factors, df = get_data()
YEARS, SITES = sorted(df["year"].unique()), sorted(df["site"].unique())
A0, LEVERS = load_cost_assumptions(), load_levers()
res0, path0, sens0 = run_scenarios(tuple(sorted(A0.items())), tuple(LEVERS.lever_id))
yearly = summarise(df, ["year"]).set_index("year")["tco2e"]

# ----------------------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown("### 🌍 EcoNaija Manufacturing Ltd")
    st.caption("Fictional Nigerian manufacturer · 3 sites · 2023–2025")
    st.markdown("**Sites:** Lagos HQ, Abuja Office, Port Harcourt Plant")
    st.markdown("**Standard:** GHG Protocol Corporate & Scope 3 · AR5 GWP100 · operational control")
    st.divider()
    st.markdown("**Emission factors**")
    st.caption("DESNZ 2026 (verified cell-by-cell) · Nigeria grid **estimated** from NERC 2025 generation mix "
               "(33% fleet efficiency, range 28–38%) · "
               "US EPA Supply Chain v1.3 (2022 USD)")
    st.markdown("**Scenario prices (Oct 2026)**")
    st.caption("Diesel ₦1,900/L · Band A ₦209.5/kWh · ₦1,350/USD · 12% discount rate")
    st.divider()
    pdf = ROOT / "reports" / "executive_summary.pdf"
    if pdf.exists():
        st.download_button("📄 Executive summary (PDF)", pdf.read_bytes(), "EcoNaija_executive_summary.pdf",
                           "application/pdf", width="stretch")
    st.link_button("💻 Code & methodology on GitHub", REPO, width="stretch")
    st.caption("Built by **Daniel Oyewale** · Petgrave.io")

# ----------------------------------------------------------------------------- hero
st.markdown(f"""
<div class="hero">
  <h1>Carbon Footprint &amp; Decarbonisation Strategy</h1>
  <p>Where EcoNaija's emissions come from, what it would cost to cut them, and whether the plan keeps pace with
     SBTi's minimum reduction rates.</p>
  <span class="badge warn">⚠️ Synthetic activity data, real 2026 factors &amp; prices</span>
  <span class="badge">GHG Protocol · Scopes 1–3</span><span class="badge">DESNZ 2026 verified</span>
  <span class="badge">Tested in CI</span>
</div>""", unsafe_allow_html=True)

t_over, t_fp, t_scen, t_s2, t_meth = st.tabs(
    ["Overview", "Footprint", "Decarbonisation scenarios", "Scope 2 & intensity", "Method & data"])

# ============================================================================= OVERVIEW
with t_over:
    p30 = path0[path0.year == 2030].iloc[0]
    gap = p30.with_levers_market - p30.sbti_target
    gap_loc = p30.with_levers_location - p30.sbti_target
    s3_share = df.loc[df.scope == 3, "tco2e"].sum() / df.tco2e.sum()
    chg = yearly[2025] / yearly[2023] - 1
    phys = res0[res0.accounting == "location"]

    c = st.columns(5)
    kpi(c[0], "2025 emissions", fmt_t(yearly[2025]), "tCO₂e", f"{chg:+.1%} vs 2023 baseline",
        ("▼ Falling", "good") if chg < 0 else ("▲ Rising", "bad"))
    kpi(c[1], "3-year footprint", fmt_t(df.tco2e.sum()), "tCO₂e", "2023–2025, Scopes 1–3")
    kpi(c[2], "Value chain share", f"{s3_share:.0%}", "Scope 3", "led by steel & resin")
    kpi(c[3], "Lever plan pays back", f"${-res0.annualised_cost_usd.sum()/1000:,.0f}k", "/ yr",
        f"net, on ${res0.capex_usd.sum()/1000:,.0f}k capex")
    kpi(c[4], "2030 vs SBTi-rate path", f"{gap:+,.0f}", "tCO₂e", "gap with renewable contracts",
        ("✓ On track", "good") if gap <= 0 else ("✕ Shortfall", "bad"))
    st.write("")

    left, right = st.columns([1, 1.25], gap="large")
    sy = summarise(df, ["year", "scope_label"])
    fig = go.Figure()
    for sc, colr in SCOPE.items():
        d = sy[sy.scope_label == sc]
        fig.add_bar(x=d.year.astype(str), y=d.tco2e, name=sc, marker=dict(color=colr, line=dict(color=SURFACE, width=2)),
                    hovertemplate=f"{sc}<br>%{{x}}: %{{y:,.0f}} tCO₂e<extra></extra>")
    fig.update_layout(barmode="stack")
    for y, v in yearly.items():
        fig.add_annotation(x=str(y), y=v, text=f"<b>{v:,.0f}</b>", showarrow=False, yshift=12,
                           font=dict(color=INK, size=12.5))
    show(left, style(fig, "Emissions by scope (tCO₂e)", height=400))

    pf = go.Figure()
    pf.add_scatter(x=path0.year, y=path0.with_levers_market_upper, line=dict(width=0), mode="lines", showlegend=False, hoverinfo="skip")
    pf.add_scatter(x=path0.year, y=path0.with_levers_market_lower, fill="tonexty", fillcolor="rgba(27,175,122,0.12)",
                   line=dict(width=0), mode="lines", name="Plan range", hoverinfo="skip")
    pf.add_scatter(mode="lines", x=path0.year, y=path0.bau, name="Business as usual", line=dict(color=INK3, width=2, dash="dot"),
                   hovertemplate="BAU %{x}: %{y:,.0f}<extra></extra>")
    pf.add_scatter(mode="lines", x=path0.year, y=path0.with_levers_market, name="With lever plan", line=dict(color="#1baf7a", width=2.5),
                   hovertemplate="Plan %{x}: %{y:,.0f}<extra></extra>")
    pf.add_scatter(mode="lines", x=path0.year, y=path0.sbti_target, name="Path at SBTi minimum rates", line=dict(color=TARGET, width=2, dash="dash"),
                   hovertemplate="Target %{x}: %{y:,.0f}<extra></extra>")
    pf.add_scatter(x=path0.year, y=path0.actual, name="Actual", mode="lines+markers",
                   line=dict(color=INK, width=2.5), marker=dict(size=9, line=dict(color=SURFACE, width=2)),
                   hovertemplate="Actual %{x}: %{y:,.0f}<extra></extra>")
    pf.add_vline(x=2030, line=dict(color=BORDER, width=1))
    pf.add_annotation(x=2030, y=p30.with_levers_market, text=f"<b>2030 gap {gap:+,.0f} t</b>", showarrow=True,
                      arrowhead=0, ax=0, ay=60, font=dict(color=INK, size=12), arrowcolor=INK3,
                      bgcolor="white", bordercolor=BORDER, borderpad=4)
    pf.update_yaxes(rangemode="tozero")
    pf.update_layout(hovermode="x unified")
    show(right, style(pf, "Pathway to 2035 vs SBTi-rate benchmark (tCO₂e)", height=400))
    right.caption("Benchmark modelled at SBTi minimum rates (Scope 1+2 −4.2%/yr, Scope 3 −2.5%/yr). "
                  "Not an SBTi-validated target.")

    st.markdown("#### What this means")
    i1, i2, i3 = st.columns(3, gap="medium")
    top_src = summarise(df, ["source"]).sort_values("tco2e", ascending=False)
    l2 = res0.set_index("lever_id").loc["L2"]
    insight(i1, "🏭", "Materials drive the footprint",
            f"Steel and plastic resin alone are <b>{top_src.set_index('source').tco2e[['Steel','Plastic resin']].sum()/df.tco2e.sum():.0%}</b> "
            "of emissions. Supplier data and low-carbon procurement for these two inputs matter more than anything on site.",
            "#1baf7a")
    insight(i2, "☀️", "Solar beats diesel on cost",
            f"A solar-battery hybrid at Port Harcourt cuts <b>{l2.abatement_tco2e:,.0f} tCO₂e/yr</b> and pays back in "
            f"<b>~{l2.simple_payback_years:.0f} years</b>. It is one of {int((res0.cost_per_tco2e_usd < 0).sum())} levers that save money.",
            "#2a78d6")
    insight(i3, "⚡", "2030 hinges on clean power contracts",
            f"Physical measures alone leave a <b>{gap_loc:+,.0f} t</b> gap in 2030. Quality-assured renewable contracts close it "
            f"(<b>{gap:+,.0f} t</b>). Growth erodes the gains by 2035, so a second wave is needed.", "#eb6834")

# ============================================================================= FOOTPRINT
with t_fp:
    f1, f2, f3 = st.columns([1.2, 1.6, 1.2])
    sel_years = f1.multiselect("Years", YEARS, default=YEARS)
    sel_sites = f2.multiselect("Sites", SITES, default=SITES)
    sel_scopes = f3.multiselect("Scopes", list(SCOPE), default=list(SCOPE))
    f = df[df.year.isin(sel_years) & df.site.isin(sel_sites) & df.scope_label.isin(sel_scopes)]
    if f.empty:
        st.info("No data for this selection. Widen the filters above.")
    else:
        total = f.tco2e.sum()
        c = st.columns(4)
        kpi(c[0], "Selected total", fmt_t(total), "tCO₂e", f"{len(sel_years)} yr · {len(sel_sites)} site(s)")
        for col, sc in zip(c[1:], SCOPE):
            v = f.loc[f.scope_label == sc, "tco2e"].sum()
            kpi(col, sc, fmt_t(v), "tCO₂e", f"{v/total:.0%} of selection")
        st.write("")

        a, b = st.columns([1.35, 1], gap="large")
        cat = summarise(f, ["category", "scope_label"]).sort_values("tco2e")
        fig = go.Figure()
        for sc, colr in SCOPE.items():
            d = cat[cat.scope_label == sc]
            if not d.empty:
                fig.add_bar(y=d.category, x=d.tco2e, orientation="h", name=sc, marker_color=colr,
                            text=[f"{v:,.0f}  ({v/total:.0%})" for v in d.tco2e], textposition="outside",
                            textfont=dict(color=INK2, size=11.5), cliponaxis=False,
                            hovertemplate="%{y}<br>%{x:,.0f} tCO₂e<extra></extra>")
        fig.update_yaxes(categoryorder="total ascending", gridcolor="rgba(0,0,0,0)")
        fig.update_xaxes(showgrid=True, gridcolor=GRID, range=[0, cat.tco2e.max() * 1.38])
        show(a, style(fig, "Hotspots by GHG Protocol category", height=470))

        top = summarise(f, ["source", "scope_label"]).sort_values("tco2e", ascending=False).head(10)
        top["share"] = top.tco2e / total
        b.markdown("**Top 10 emission sources**")
        b.dataframe(top.rename(columns={"source": "Source", "scope_label": "Scope", "tco2e": "tCO₂e", "share": "Share"}),
                    hide_index=True, width="stretch", height=420,
                    column_config={"tCO₂e": st.column_config.NumberColumn(format="%,.0f"),
                                   "Share": st.column_config.ProgressColumn(format="percent", min_value=0,
                                                                           max_value=float(top.share.max()))})

        a, b = st.columns([1, 1.35], gap="large")
        ss = summarise(f, ["site", "scope_label"])
        fig = go.Figure()
        for sc, colr in SCOPE.items():
            d = ss[ss.scope_label == sc]
            fig.add_bar(y=d.site, x=d.tco2e, orientation="h", name=sc,
                        marker=dict(color=colr, line=dict(color=SURFACE, width=2)),
                        hovertemplate=f"{sc}<br>%{{y}}: %{{x:,.0f}} tCO₂e<extra></extra>")
        fig.update_layout(barmode="stack")
        fig.update_yaxes(categoryorder="total ascending")
        fig.update_xaxes(showgrid=True, gridcolor=GRID)
        show(a, style(fig, "By site (tCO₂e)", height=330))

        m = summarise(f, ["period", "site"])
        fig = go.Figure()
        for site in SITES:
            d = m[m.site == site]
            if d.empty:
                continue
            fig.add_scatter(x=d.period, y=d.tco2e, name=site, mode="lines", line=dict(color=SITE[site], width=2),
                            hovertemplate=f"{site}<br>%{{x|%b %Y}}: %{{y:,.0f}} tCO₂e<extra></extra>")
            fig.add_annotation(x=d.period.iloc[-1], y=d.tco2e.iloc[-1], text=site.split()[0], xanchor="left",
                               showarrow=False, xshift=6, font=dict(color=INK2, size=11.5))
        fig.update_yaxes(rangemode="tozero")
        fig.update_layout(hovermode="x unified")
        show(b, style(fig, "Monthly emissions by site (tCO₂e)", height=330))

        prog = reduction_vs_baseline(df[df.site.isin(sel_sites)], min(YEARS))
        with st.expander("View data: yearly progress & filtered emissions"):
            st.dataframe(prog.rename(columns={"tco2e": "tCO₂e", "pct_change_vs_baseline": "% vs 2023"}),
                         hide_index=True, column_config={"tCO₂e": st.column_config.NumberColumn(format="%,.0f"),
                                                         "% vs 2023": st.column_config.NumberColumn(format="%+.1f%%")})
            out = f[["period", "site", "scope", "category", "source", "component", "quantity", "unit", "tco2e"]]
            st.download_button("⬇️ Download filtered emissions (CSV)", out.to_csv(index=False).encode(),
                               "econaija_emissions.csv", "text/csv")

# ============================================================================= SCENARIOS
with t_scen:
    st.markdown('<p class="section-note">Nine reduction levers sized against the 2025 baseline and applied in order, so '
                'overlaps are never double-counted. Change the assumptions to stress-test the plan.</p>',
                unsafe_allow_html=True)
    A = dict(A0)
    with st.container(border=True):
        s1, s2, s3, s4, s5 = st.columns(5)
        A["diesel_price_ngn_per_litre"] = s1.number_input("Diesel (₦/L)", 500, 5000, int(A0["diesel_price_ngn_per_litre"]), 50)
        A["grid_tariff_ngn_per_kwh"] = s2.number_input("Grid tariff (₦/kWh)", 50.0, 500.0, float(A0["grid_tariff_ngn_per_kwh"]), 5.0)
        A["fx_ngn_per_usd"] = s3.number_input("FX (₦ per USD)", 500, 3000, int(A0["fx_ngn_per_usd"]), 25)
        A["discount_rate"] = s4.slider("Discount rate", 0.0, 0.30, float(A0["discount_rate"]), 0.01, format="%.2f")
        A["bau_growth_rate"] = s5.slider("Business growth / yr", 0.0, 0.08, float(A0["bau_growth_rate"]), 0.005, format="%.3f")
        short = {"L1": "Efficiency", "L2": "PH solar hybrid", "L3": "Rooftop solar", "L4": "Refrigerant leaks",
                 "L5": "Travel policy", "L6": "Hybrid working", "L7": "Recycling", "L8": "Supplier engagement",
                 "L9": "Renewable contracts"}
        chosen = st.pills("Levers in the plan (click to toggle)", list(short), selection_mode="multi",
                          default=list(short), format_func=lambda k: f"{k} · {short[k]}") or []
    if not chosen:
        st.warning("Select at least one lever.")
    else:
        res, path, sens = run_scenarios(tuple(sorted(A.items())), tuple(chosen))
        y30 = path[path.year == 2030].iloc[0]
        g = y30.with_levers_market - y30.sbti_target
        loc_ab = res.loc[res.accounting == "location", "abatement_tco2e"].sum()
        net = -res.annualised_cost_usd.sum()
        st.write("")
        c = st.columns(4)
        kpi(c[0], "Physical abatement", fmt_t(loc_ab), "tCO₂e/yr", f"{loc_ab/yearly[2025]:.0%} of 2025 emissions")
        kpi(c[1], "Capex", f"${res.capex_usd.sum()/1000:,.0f}k", "", f"{len(res)} levers")
        kpi(c[2], "Net annual saving" if net >= 0 else "Net annual cost", f"${abs(net)/1000:,.0f}k", "/ yr",
            "annualised capex + opex − energy savings")
        kpi(c[3], "2030 gap vs SBTi-rate path", f"{g:+,.0f}", "tCO₂e",
            f"range {y30.with_levers_market_lower - y30.sbti_target:+,.0f} to {y30.with_levers_market_upper - y30.sbti_target:+,.0f}",
            ("✓ On track", "good") if g <= 0 else ("✕ Shortfall", "bad"))
        st.write("")

        mc = res.sort_values("cost_per_tco2e_usd").reset_index(drop=True)
        mc["x0"] = mc.abatement_tco2e.cumsum() - mc.abatement_tco2e
        colors = ["#1baf7a" if v < 0 else ("#eda100" if v <= 100 else "#eb6834") for v in mc.cost_per_tco2e_usd]
        fig = go.Figure(go.Bar(
            x=mc.x0 + mc.abatement_tco2e / 2, y=mc.cost_per_tco2e_usd, width=mc.abatement_tco2e * 0.97,
            marker=dict(color=colors, line=dict(color=SURFACE, width=0)), text=mc.lever_id,
            textposition="outside", textfont=dict(color=INK, size=12), cliponaxis=False,
            customdata=mc[["lever", "abatement_tco2e", "capex_usd", "simple_payback_years", "accounting"]],
            hovertemplate="<b>%{customdata[0]}</b><br>%{y:,.0f} USD per tCO₂e<br>%{customdata[1]:,.0f} tCO₂e/yr"
                          "<br>Capex $%{customdata[2]:,.0f}<br>Payback %{customdata[3]:.1f} yr"
                          "<br>%{customdata[4]}-based<extra></extra>"))
        fig.add_hline(y=0, line=dict(color=INK3, width=1))
        fig.update_layout(barcornerradius=3)
        st_fig = style(fig, "Marginal abatement cost curve: cheapest cuts first", height=420, legend=False,
                       ytitle="USD per tCO₂e (annualised)", xtitle="Cumulative abatement (tCO₂e/yr)")
        show(st, st_fig)
        st.caption("Bar width = tonnes cut per year · height = cost per tonne. 🟩 saves money · 🟨 under \\$100/t · "
                   "🟧 over \\$100/t. Hover a bar for capex and payback.")

        a, b = st.columns([1.35, 1], gap="large")
        pf = go.Figure()
        pf.add_scatter(x=path.year, y=path.with_levers_market_upper, line=dict(width=0), mode="lines", showlegend=False, hoverinfo="skip")
        pf.add_scatter(x=path.year, y=path.with_levers_market_lower, fill="tonexty", fillcolor="rgba(27,175,122,0.12)",
                       line=dict(width=0), mode="lines", name="Range (lever effectiveness)", hoverinfo="skip")
        pf.add_scatter(mode="lines", x=path.year, y=path.bau, name="Business as usual", line=dict(color=INK3, width=2, dash="dot"))
        pf.add_scatter(mode="lines", x=path.year, y=path.with_levers_location, name="Plan (location-based)", line=dict(color="#2a78d6", width=2))
        pf.add_scatter(mode="lines", x=path.year, y=path.with_levers_market, name="Plan + renewable contracts", line=dict(color="#1baf7a", width=2.5))
        pf.add_scatter(mode="lines", x=path.year, y=path.sbti_target, name="Path at SBTi minimum rates", line=dict(color=TARGET, width=2, dash="dash"))
        pf.add_scatter(x=path.year, y=path.actual, name="Actual", mode="lines+markers", line=dict(color=INK, width=2.5),
                       marker=dict(size=9, line=dict(color=SURFACE, width=2)))
        pf.update_yaxes(rangemode="tozero")
        pf.update_layout(hovermode="x unified")
        pf.update_traces(hovertemplate="%{y:,.0f}")
        show(a, style(pf, "Phased pathway with uncertainty (tCO₂e)", height=420))

        sv = sens[sens.saving_swing > 0].iloc[::-1]
        lo = sv[["net_saving_low", "net_saving_high"]].min(axis=1)
        hi = sv[["net_saving_low", "net_saving_high"]].max(axis=1)
        fig = go.Figure(go.Bar(y=sv.parameter, x=(hi - lo) / 1000, base=lo / 1000, orientation="h",
                               marker_color="#2a78d6", text=[f"${l/1000:,.0f}k – ${h/1000:,.0f}k" for l, h in zip(lo, hi)],
                               textposition="outside", textfont=dict(color=INK2, size=11.5), cliponaxis=False,
                               hovertemplate="%{y}<br>%{base:,.0f}k to %{x:,.0f}k span<extra></extra>"))
        fig.add_vline(x=net / 1000, line=dict(color=INK, width=1, dash="dash"))
        fig.update_xaxes(showgrid=True, gridcolor=GRID, range=[0, hi.max() / 1000 * 1.75], ticksuffix="k")
        show(b, style(fig, "What moves the savings? ($/yr)", height=420, legend=False))

        st.markdown("**Lever detail**")
        tbl = res[["lever_id", "lever", "start_year", "abatement_tco2e", "capex_usd",
                   "annual_savings_usd", "cost_per_tco2e_usd", "simple_payback_years"]].sort_values("cost_per_tco2e_usd")
        tbl["simple_payback_years"] = tbl["simple_payback_years"].map(lambda x: f"{x:.1f}" if x == x else "–")
        st.dataframe(tbl, hide_index=True, width="stretch", column_config={
            "lever_id": "ID", "lever": st.column_config.TextColumn("Lever", width="medium"),
            "start_year": st.column_config.NumberColumn("Start", format="%d"),
            "abatement_tco2e": st.column_config.ProgressColumn("tCO₂e/yr", format="%.0f", min_value=0,
                                                               max_value=float(res.abatement_tco2e.max())),
            "capex_usd": st.column_config.NumberColumn("Capex", format="$%,.0f"),
            "annual_savings_usd": st.column_config.NumberColumn("Savings/yr", format="$%,.0f"),
            "cost_per_tco2e_usd": st.column_config.NumberColumn("USD/tCO₂e", format="%,.0f"),
            "simple_payback_years": st.column_config.TextColumn("Payback (yr)")})
        with st.expander("How each lever was sized & costed"):
            st.dataframe(LEVERS[["lever_id", "sizing_notes", "cost_source"]], hide_index=True, width="stretch")

# ============================================================================= SCOPE 2 & INTENSITY
with t_s2:
    ints = intensity_metrics(df, load_profile())
    c = st.columns(3)
    for col, key, label, unit in ((c[0], "tco2e_per_employee", "Per employee", "tCO₂e"),
                                  (c[1], "tco2e_per_usd_m_revenue", "Per USD m revenue", "tCO₂e"),
                                  (c[2], "kgco2e_per_tonne_product", "Per tonne of product", "kgCO₂e")):
        first, last = ints[key].iloc[0], ints[key].iloc[-1]
        kpi(col, f"Intensity · {label}", f"{last:,.1f}", unit, f"2025 · {last/first-1:+.0%} vs 2023",
            ("▼ Improving", "good") if last < first else ("▲ Worsening", "bad"))
    st.caption("Company profile (employees, revenue, production) is synthetic.")
    st.write("")

    st.markdown("#### Market-based Scope 2: only quality-assured instruments count")
    st.markdown('<p class="section-note">GHG Protocol Scope 2 Quality Criteria: conveys the attribute claim · retired for '
                'the company · tracked in a registry · matching vintage · same market · not double counted.</p>',
                unsafe_allow_html=True)
    v = validate_instruments(load_instruments())
    vt = v[["instrument_id", "instrument_type", "generation_year", "generation_country", "mwh", "eligible", "failure_reasons"]].copy()
    vt["eligible"] = vt["eligible"].map({True: "✅ Counts", False: "❌ Rejected"})
    st.dataframe(vt.rename(columns={"instrument_id": "Instrument", "instrument_type": "Type", "generation_year": "Vintage",
                                   "generation_country": "Market", "mwh": "MWh", "eligible": "Status",
                                   "failure_reasons": "Reason"}),
                 hide_index=True, width="stretch", column_config={"Vintage": st.column_config.NumberColumn(format="%d")})
    a, b = st.columns([1.4, 1], gap="large")
    dual = scope2_dual(df, eligible_kwh_by_year(v))
    fig = go.Figure()
    fig.add_bar(x=dual.year.astype(str), y=dual.location_tco2e, name="Location-based", marker_color="#eb6834",
                hovertemplate="Location %{x}: %{y:,.0f}<extra></extra>")
    fig.add_bar(x=dual.year.astype(str), y=dual.market_tco2e, name="Market-based", marker_color="#2a78d6",
                hovertemplate="Market %{x}: %{y:,.0f}<extra></extra>")
    fig.update_layout(barmode="group", bargroupgap=0.12)
    show(a, style(fig, "Scope 2 dual reporting (tCO₂e)", height=330))
    ok_mwh = v.loc[v.eligible, "mwh"].sum()
    b.markdown(f"""
**Reading the chart**

- **Location-based** uses the Nigerian grid average for every kWh.
- **Market-based** gives a zero factor only to the **{ok_mwh:,.0f} MWh** of instruments that passed all six checks
  ({int(v.eligible.sum())} of {len(v)}). Everything else stays at the grid average.
- Nigeria has no published residual mix, so the grid average is the fallback. This is disclosed, per the Scope 2 Guidance.

*Instruments are synthetic examples.*""")

# ============================================================================= METHOD & DATA
with t_meth:
    a, b = st.columns([1, 1], gap="large")
    a.markdown("""
#### How the numbers are built
- **Emissions** = activity × emission factor, per GHG Protocol. One activity can carry several factor components:
  diesel → Scope 1 combustion **+** Scope 3 Cat 3 upstream supply.
- **Nigeria grid (Scope 2), an estimate, not an official national factor** = 67% gas share (NERC 2025) × DESNZ
  gas combustion factor ÷ 33% assumed fleet efficiency = **0.417 kgCO₂e/kWh**. Upstream gas and grid losses go to Scope 3 Cat 3.
- **Purchased goods**: 10 spend categories mapped to US EPA v1.3 NAICS factors, deflated to 2022 USD.
- **Scenarios**: levers phase in over 1–3 years, with low/high effectiveness bands; annualised cost uses a 12% discount rate.
- **Target benchmark**: a path at SBTi minimum rates from 2023 (Scope 1+2 −4.2%/yr, Scope 3 −2.5%/yr), *not an SBTi-validated target*.
- **Restatements**: activity data is unchanged; totals moved 12,270 → 17,313 t only through method improvements (all years recalculated).
""")
    b.markdown("""
#### Limitations
- Activity data and company profile are **synthetic**.
- Spend-based Scope 3 uses **US-economy** factors.
- UK proxies for landfill and car factors likely **understate** Nigerian conditions.
- The grid factor depends on the assumed fleet efficiency (range 28–38%).
- No grid decarbonisation or solar degradation is modelled.

[Full methodology →](https://github.com/Engr-Daniel/carbon-footprint-esg-dashboard/blob/master/docs/methodology.md)
""")
    st.markdown("#### How sensitive is the estimated grid factor?")
    from carbon.grid_factor import footprint_sensitivity
    gs = footprint_sensitivity(activity, factors)
    central_total = gs.loc[gs.fleet_efficiency == 0.33, "total_tco2e"].iloc[0]
    gs["vs_central"] = gs.total_tco2e / central_total - 1
    st.dataframe(gs, hide_index=True, width="stretch", column_config={
        "fleet_efficiency": st.column_config.NumberColumn("Assumed gas-fleet efficiency", format="percent"),
        "scope2_factor_kg_per_kwh": st.column_config.NumberColumn("Scope 2 factor (kgCO₂e/kWh)", format="%.3f"),
        "scope2_tco2e": st.column_config.NumberColumn("Scope 2, 2023–25 (tCO₂e)", format="%,.0f"),
        "total_tco2e": st.column_config.NumberColumn("Total, 2023–25 (tCO₂e)", format="%,.0f"),
        "vs_central": st.column_config.NumberColumn("vs central", format="percent")})
    st.caption("Nigerian open-cycle gas plants are reported at 25–39% efficiency. 33% is the central assumption. "
               "Replace with an official national or IEA factor when available.")

    st.markdown("#### Emission factor library")
    q = st.text_input("Search factors", placeholder="e.g. diesel, steel, grid…")
    ft = factors.copy()
    if q:
        ft = ft[ft.apply(lambda r: q.lower() in " ".join(map(str, r.values)).lower(), axis=1)]
    st.dataframe(ft[["activity_type", "component", "scope", "category", "unit", "kgco2e_per_unit", "factor_year",
                     "source", "verification"]], hide_index=True, width="stretch",
                 column_config={"activity_type": "Activity", "component": "Component", "scope": "Scope",
                                "category": "Category", "unit": "Unit", "verification": "Verification",
                                "kgco2e_per_unit": st.column_config.NumberColumn("kgCO₂e / unit", format="%.5f"),
                                "factor_year": st.column_config.NumberColumn("Year", format="%d"),
                                "source": st.column_config.TextColumn("Source", width="large")})

st.markdown(f'<div class="foot">Illustrative case study · synthetic activity data · not a verified GHG inventory · '
            f'<a href="{REPO}" target="_blank">source code</a></div>', unsafe_allow_html=True)
