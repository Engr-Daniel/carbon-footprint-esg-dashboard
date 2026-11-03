"""Interactive ESG / carbon footprint dashboard.

Run:  streamlit run app/streamlit_app.py
"""
import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from carbon import calculate_emissions, load_activity, load_factors, reduction_vs_baseline, summarise  # noqa: E402

st.set_page_config(page_title="Carbon Footprint & ESG Dashboard", page_icon="🌍", layout="wide")
st.title("🌍 Carbon Footprint & ESG Dashboard")
st.caption("Scope 1, 2 & 3 GHG emissions (GHG Protocol). Demo uses SYNTHETIC data for a fictional company.")


@st.cache_data
def get_data():
    return calculate_emissions(load_activity(), load_factors())


df = get_data()

# Sidebar filters
st.sidebar.header("Filters")
years = sorted(df["year"].unique())
sel_years = st.sidebar.multiselect("Year", years, default=years)
sites = sorted(df["site"].unique())
sel_sites = st.sidebar.multiselect("Site", sites, default=sites)
target_pct = st.sidebar.slider("Reduction target vs baseline (%)", 0, 60, 30)

f = df[df["year"].isin(sel_years) & df["site"].isin(sel_sites)]
if f.empty:
    st.warning("No data for the selected filters.")
    st.stop()

# KPI tiles
total = f["tco2e"].sum()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total emissions", f"{total:,.0f} tCO2e")
for col, scope in zip((c2, c3, c4), (1, 2, 3)):
    v = f.loc[f["scope"] == scope, "tco2e"].sum()
    col.metric(f"Scope {scope}", f"{v:,.0f} tCO2e", f"{v / total:.0%} of total", delta_color="off")

left, right = st.columns(2)
by_scope_year = summarise(f, ["year", "scope"])
by_scope_year["scope"] = "Scope " + by_scope_year["scope"].astype(str)
left.plotly_chart(
    px.bar(by_scope_year, x="year", y="tco2e", color="scope", title="Emissions by scope and year",
           labels={"tco2e": "tCO2e", "year": "Year"}),
    width="stretch",
)
by_cat = summarise(f, ["category"]).sort_values("tco2e")
right.plotly_chart(
    px.bar(by_cat, x="tco2e", y="category", orientation="h", title="Emissions hotspots by category",
           labels={"tco2e": "tCO2e", "category": ""}),
    width="stretch",
)

monthly = summarise(f, ["period", "site"])
st.plotly_chart(
    px.line(monthly, x="period", y="tco2e", color="site", title="Monthly emissions by site",
            labels={"tco2e": "tCO2e", "period": ""}),
    width="stretch",
)

# Target tracking
st.subheader("🎯 Progress against reduction target")
site_f = df[df["site"].isin(sel_sites)]
base_year = min(years)
progress = reduction_vs_baseline(site_f, base_year)
target_value = progress.loc[progress["year"] == base_year, "tco2e"].iloc[0] * (1 - target_pct / 100)
fig = px.line(progress, x="year", y="tco2e", markers=True, labels={"tco2e": "tCO2e", "year": "Year"},
              title=f"Actual vs {target_pct}% reduction target (baseline {base_year})")
fig.add_hline(y=target_value, line_dash="dash", annotation_text="Target")
st.plotly_chart(fig, width="stretch")
st.dataframe(progress.style.format({"tco2e": "{:,.1f}", "pct_change_vs_baseline": "{:+.1f}%"}),
             width="stretch")

with st.expander("Emission factors used"):
    st.dataframe(load_factors(), width="stretch")
    st.info("Factors are indicative. Verify against the latest DEFRA/DESNZ, IPCC and national grid sources.")
