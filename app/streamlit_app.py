"""Interactive ESG / carbon footprint dashboard.

Run:  streamlit run app/streamlit_app.py
"""
import sys
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from carbon import calculate_emissions, load_activity, load_factors, reduction_vs_baseline, summarise  # noqa: E402
from carbon.scenarios import (  # noqa: E402
    apply_levers,
    baseline_activity,
    intensity_metrics,
    load_cost_assumptions,
    load_levers,
    load_profile,
    pathway,
    scope2_dual,
)

st.set_page_config(page_title="Carbon Footprint & ESG Dashboard", page_icon="🌍", layout="wide")
st.title("🌍 Carbon Footprint & ESG Dashboard")
SCOPE_COLORS = {"Scope 1": "#2a6f97", "Scope 2": "#f4a261", "Scope 3": "#2a9d8f"}
st.caption("Scope 1, 2 & 3 GHG emissions (GHG Protocol). Demo uses SYNTHETIC activity data for a fictional "
           "company (EcoNaija Manufacturing Ltd) with real DESNZ 2026 / Ember 2025 / US EPA emission factors.")


@st.cache_data
def get_data():
    activity, factors = load_activity(), load_factors()
    return activity, factors, calculate_emissions(activity, factors)


activity, factors, df = get_data()
years = sorted(df["year"].unique())
sites = sorted(df["site"].unique())

tab_fp, tab_scen, tab_int = st.tabs(["📊 Footprint", "🛠️ Decarbonisation scenarios", "📐 Intensity & Scope 2"])

# --------------------------------------------------------------------------- Footprint
with tab_fp:
    fc1, fc2, fc3 = st.columns([2, 2, 1])
    sel_years = fc1.multiselect("Year", years, default=years)
    sel_sites = fc2.multiselect("Site", sites, default=sites)
    target_pct = fc3.slider("Target vs baseline (%)", 0, 60, 30)

    f = df[df["year"].isin(sel_years) & df["site"].isin(sel_sites)]
    if f.empty:
        st.warning("No data for the selected filters.")
    else:
        total = f["tco2e"].sum()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total emissions", f"{total:,.0f} tCO2e")
        for col, scope in zip((c2, c3, c4), (1, 2, 3)):
            v = f.loc[f["scope"] == scope, "tco2e"].sum()
            col.metric(f"Scope {scope}", f"{v:,.0f} tCO2e")
            col.caption(f"{v / total:.0%} of total")

        left, right = st.columns(2)
        by_scope_year = summarise(f, ["year", "scope"])
        by_scope_year["scope"] = "Scope " + by_scope_year["scope"].astype(str)
        left.plotly_chart(
            px.bar(by_scope_year, x="year", y="tco2e", color="scope", title="Emissions by scope and year",
                   color_discrete_map=SCOPE_COLORS, category_orders={"scope": list(SCOPE_COLORS)},
                   labels={"tco2e": "tCO2e", "year": "Year"}),
            width="stretch",
        )
        by_cat = summarise(f, ["category", "scope"]).sort_values("tco2e")
        by_cat["scope"] = "Scope " + by_cat["scope"].astype(str)
        hot_fig = px.bar(by_cat, x="tco2e", y="category", orientation="h", title="Emissions hotspots by category",
                         color="scope", color_discrete_map=SCOPE_COLORS,
                         category_orders={"scope": list(SCOPE_COLORS)}, labels={"tco2e": "tCO2e", "category": ""})
        hot_fig.update_yaxes(categoryorder="total ascending")
        right.plotly_chart(hot_fig, width="stretch")

        monthly = summarise(f, ["period", "site"])
        st.plotly_chart(px.line(monthly, x="period", y="tco2e", color="site", title="Monthly emissions by site",
                                labels={"tco2e": "tCO2e", "period": ""}), width="stretch")

        st.subheader("🎯 Progress against reduction target")
        site_f = df[df["site"].isin(sel_sites)]
        base_year = min(years)
        progress = reduction_vs_baseline(site_f, base_year)
        target_value = progress.loc[progress["year"] == base_year, "tco2e"].iloc[0] * (1 - target_pct / 100)
        fig = px.line(progress, x="year", y="tco2e", markers=True, labels={"tco2e": "tCO2e", "year": "Year"},
                      title=f"Actual vs {target_pct}% reduction target (baseline {base_year})")
        fig.add_hline(y=target_value, line_dash="dash", annotation_text="Target", line_color="#e76f51")
        fig.update_xaxes(dtick=1)
        st.plotly_chart(fig, width="stretch")
        st.dataframe(progress.style.format({"tco2e": "{:,.1f}", "pct_change_vs_baseline": "{:+.1f}%"}),
                     width="stretch")

    with st.expander("Emission factors used"):
        st.dataframe(factors, width="stretch")
        st.info("Sources: DESNZ 2026 conversion factors, Ember 2025 (Nigeria grid), US EPA Supply Chain Factors v1.3. "
                "Factors marked 'Secondary source' should be confirmed in the official workbook.")

# --------------------------------------------------------------------------- Scenarios
with tab_scen:
    st.markdown("Model reduction levers against the **2025 baseline**. Levers are applied in order to the residual "
                "activity, so overlaps are not double-counted. Costs are **modelled assumptions** - change them below.")
    A = load_cost_assumptions()
    levers_all = load_levers()
    s1, s2, s3, s4, s5 = st.columns(5)
    A["diesel_price_ngn_per_litre"] = s1.number_input("Diesel (₦/L)", 500, 5000, int(A["diesel_price_ngn_per_litre"]), 50)
    A["grid_tariff_ngn_per_kwh"] = s2.number_input("Grid tariff (₦/kWh)", 50.0, 500.0, float(A["grid_tariff_ngn_per_kwh"]), 5.0)
    A["fx_ngn_per_usd"] = s3.number_input("FX (₦ per USD)", 500, 3000, int(A["fx_ngn_per_usd"]), 25)
    A["discount_rate"] = s4.slider("Discount rate", 0.0, 0.30, float(A["discount_rate"]), 0.01)
    A["bau_growth_rate"] = s5.slider("BAU growth / yr", 0.0, 0.08, float(A["bau_growth_rate"]), 0.005)
    labels = {r.lever_id: f"{r.lever_id} – {r.lever}" for r in levers_all.itertuples()}
    chosen = st.multiselect("Levers included", list(labels), default=list(labels), format_func=labels.get)
    if not chosen:
        st.warning("Select at least one lever.")
    else:
        res, _ = apply_levers(baseline_activity(activity, 2025), levers_all[levers_all.lever_id.isin(chosen)],
                              factors, A, 2025)
        path = pathway(df, res, 2023, 2025, 2035, A["bau_growth_rate"])
        base_2025 = df.loc[df.year == 2025, "tco2e"].sum()
        loc_ab = res.loc[res.accounting == "location", "abatement_tco2e"].sum()
        y30 = path[path.year == 2030].iloc[0]
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Physical abatement", f"{loc_ab:,.0f} tCO2e/yr", f"{-loc_ab / base_2025:.0%} vs 2025", delta_color="inverse")
        k2.metric("Total capex", f"${res.capex_usd.sum():,.0f}")
        net = -res.annualised_cost_usd.sum()
        k3.metric("Net annual saving" if net >= 0 else "Net annual cost", f"${abs(net):,.0f}/yr")
        gap = y30.with_levers_market - y30.sbti_target
        k4.metric("2030 gap to SBTi target (market-based)", f"{gap:+,.0f} tCO2e",
                  "on track" if gap <= 0 else "shortfall", delta_color="normal" if gap <= 0 else "inverse")

        # MACC as variable-width bars
        m = res.sort_values("cost_per_tco2e_usd").reset_index(drop=True)
        m["x0"] = m.abatement_tco2e.cumsum() - m.abatement_tco2e
        colors = ["#2a9d8f" if c < 0 else "#e9c46a" if c <= 100 else "#e76f51" for c in m.cost_per_tco2e_usd]
        macc = go.Figure(go.Bar(
            x=m.x0 + m.abatement_tco2e / 2, y=m.cost_per_tco2e_usd, width=m.abatement_tco2e,
            marker_color=colors, marker_line_color="white", text=m.lever_id, textposition="outside",
            customdata=m[["lever", "abatement_tco2e", "capex_usd", "accounting"]],
            hovertemplate="<b>%{customdata[0]}</b><br>%{y:,.0f} USD/tCO2e<br>%{customdata[1]:,.0f} tCO2e/yr"
                          "<br>Capex $%{customdata[2]:,.0f}<br>%{customdata[3]}-based<extra></extra>",
        ))
        macc.update_layout(title="Marginal abatement cost curve (hover for details)",
                           xaxis_title="Cumulative annual abatement (tCO2e/yr)", yaxis_title="USD per tCO2e")
        st.plotly_chart(macc, width="stretch")

        pf = go.Figure()
        pf.add_scatter(x=path.year, y=path.actual, name="Actual", mode="lines+markers", line=dict(color="#264653", width=3))
        pf.add_scatter(x=path.year, y=path.bau, name="Business as usual", line=dict(color="grey", dash="dot"))
        pf.add_scatter(x=path.year, y=path.with_levers_location, name="With levers (location-based)", line=dict(color="#2a6f97"))
        pf.add_scatter(x=path.year, y=path.with_levers_market, name="With levers + PPA (market-based)", line=dict(color="#2a9d8f"))
        pf.add_scatter(x=path.year, y=path.sbti_target, name="SBTi target (S1+2 4.2%/yr, S3 2.5%/yr)",
                       line=dict(color="#e76f51", dash="dash"))
        pf.update_layout(title="Decarbonisation pathway to 2035", yaxis_title="tCO2e", yaxis_rangemode="tozero")
        st.plotly_chart(pf, width="stretch")

        st.dataframe(
            res[["lever_id", "lever", "scope", "accounting", "start_year", "abatement_tco2e", "capex_usd",
                 "annual_savings_usd", "cost_per_tco2e_usd", "simple_payback_years"]]
            .style.format({"abatement_tco2e": "{:,.0f}", "capex_usd": "${:,.0f}", "annual_savings_usd": "${:,.0f}",
                           "cost_per_tco2e_usd": "{:,.0f}", "simple_payback_years": "{:.1f}"}, na_rep="–"),
            width="stretch", hide_index=True)
        with st.expander("Lever sizing notes & cost sources"):
            st.dataframe(levers_all[["lever_id", "sizing_notes", "cost_source"]], width="stretch", hide_index=True)

# --------------------------------------------------------------------------- Intensity & Scope 2
with tab_int:
    ints = intensity_metrics(df, load_profile())
    i1, i2, i3 = st.columns(3)
    for col, key, label in ((i1, "tco2e_per_employee", "tCO2e per employee"),
                            (i2, "tco2e_per_usd_m_revenue", "tCO2e per USD m revenue"),
                            (i3, "kgco2e_per_tonne_product", "kgCO2e per tonne product")):
        first, last = ints[key].iloc[0], ints[key].iloc[-1]
        col.metric(f"{label} ({ints.year.iloc[-1]})", f"{last:,.1f}", f"{last / first - 1:+.0%} vs {ints.year.iloc[0]}",
                   delta_color="inverse")
    st.caption("Company profile (employees, revenue, production) is synthetic.")

    st.subheader("Scope 2: location-based vs market-based")
    cover = st.slider("Share of 2025 grid kWh covered by renewable contracts (PPA / I-RECs)", 0, 100, 0, 5)
    kwh25 = df.loc[(df.scope == 2) & (df.year == 2025), "quantity"].sum()
    dual = scope2_dual(df, {2025: kwh25 * cover / 100})
    d = dual.melt(id_vars="year", value_vars=["location_tco2e", "market_tco2e"], var_name="method", value_name="tCO2e")
    d["method"] = d["method"].map({"location_tco2e": "Location-based", "market_tco2e": "Market-based"})
    st.plotly_chart(px.bar(d, x="year", y="tCO2e", color="method", barmode="group",
                           color_discrete_sequence=["#f4a261", "#2a9d8f"]).update_xaxes(dtick=1), width="stretch")
    st.info("Nigeria has no published residual-mix factor, so uncovered kWh in the market-based method fall back to "
            "the grid average (GHG Protocol Scope 2 Guidance).")
