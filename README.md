# 🌍 Carbon Footprint & ESG Dashboard

End-to-end **Scope 1, 2 & 3 greenhouse gas (GHG) emissions analysis** and an **interactive ESG dashboard**, built on the [GHG Protocol Corporate Standard](https://ghgprotocol.org/corporate-standard). The case study is set in Nigeria.

> ⚠️ **Demo data:** The activity dataset is **synthetic** and belongs to a fictional company, *EcoNaija Manufacturing Ltd* (3 sites, 2023–2025). The **emission factors are real**: **DESNZ 2026** (fuels, travel, waste, refrigerants), **Ember 2025** (Nigeria grid) and **US EPA Supply Chain Factors v1.3** (spend-based). All DESNZ values are **verified cell-by-cell against the official 2026 workbook**. Each factor's source, year and workbook cell reference are listed in [`emission_factors.csv`](data/reference/emission_factors.csv).

![Dashboard](reports/figures/dashboard_screenshot.png)

---

## 📌 Business Problem
Investors, regulators and buyers are asking more and more for credible emissions disclosures. Examples include IFRS S2 / ISSB, the Nigerian SEC sustainability disclosure roadmap and supply-chain requirements. Many organisations, especially SMEs in Africa, lack a transparent and repeatable way to:
1. **Measure** their carbon footprint across all three scopes
2. **Identify hotspots** where reductions matter most
3. **Track progress** against reduction targets

This project provides a lightweight, auditable carbon accounting pipeline and a dashboard that answers all three questions.

## 🎯 Objectives
- Build a reusable emissions calculation engine (activity data × emission factor)
- Model the data relationally (SQL) for scalability
- Find emission hotspots by scope, category and site
- Track performance against a science-aligned reduction target
- Turn the findings into actionable decarbonisation recommendations

## 🗂️ Project Structure
```
carbon-footprint-esg-dashboard/
├── app/
│   └── streamlit_app.py          # Interactive dashboard
├── data/
│   ├── raw/                      # Raw inputs (git-ignored)
│   ├── processed/                # Cleaned outputs (git-ignored)
│   ├── reference/
│   │   ├── emission_factors.csv  # Emission factor library
│   │   ├── reduction_levers.csv  # Lever sizing, capex, opex, lifetime
│   │   └── cost_assumptions.csv  # Fuel prices, tariff, FX, discount rate (sourced)
│   └── sample/
│       ├── activity_data_sample.csv  # Synthetic activity data
│       └── company_profile.csv       # Synthetic employees / revenue / production
├── docs/
│   └── methodology.md            # Boundaries, scopes, assumptions
├── notebooks/
│   ├── 01_exploratory_analysis.ipynb
│   └── 02_decarbonisation_scenarios.ipynb   # MACC, pathway, sensitivity
├── reports/figures/              # Exported charts + dashboard screenshot
├── sql/
│   └── schema.sql                # Relational data model + views
├── src/carbon/
│   ├── emissions.py              # Calculation engine
│   ├── scenarios.py              # Levers, MACC, pathway, intensity, dual Scope 2
│   └── report_figures.py         # Exports report charts
├── tests/
│   ├── test_emissions.py         # Unit tests (pytest)
│   └── test_scenarios.py
├── AGENTS.md                     # Guide for AI coding agents / collaborators
├── MEMORY.md                     # Project decisions & context log
├── TASK.md                       # Roadmap & task tracker
└── requirements.txt
```

## 🧮 Methodology (summary)
| Scope | What it covers | Activities in this project |
|---|---|---|
| **Scope 1** | Direct emissions from owned or controlled sources | Diesel generators, fleet fuel, natural gas, LPG, refrigerant leaks |
| **Scope 2** | Indirect emissions from purchased energy | Grid electricity (Nigeria grid factor) |
| **Scope 3** | Other value-chain emissions | Purchased goods (spend-based), business travel, commuting, waste |

**Formula:** `tCO2e = activity quantity × emission factor (kgCO2e/unit) ÷ 1000`

The full method is in [`docs/methodology.md`](docs/methodology.md).

## 📊 Key Findings (synthetic activity data, 2023–2025)
| Metric | Value |
|---|---|
| Total footprint (3 yrs) | **12,281 tCO2e** |
| 2025 footprint | **3,884 tCO2e** |
| Scope split | Scope 1: 29% · Scope 2: 25% · Scope 3: 45% |
| Change, 2025 vs 2023 baseline | **−9.6%** |
| Highest-emitting site | Port Harcourt Plant (56% of total) |

![Emissions by scope](reports/figures/01_emissions_by_scope_year.png)

- **Purchased goods & services (Scope 3 Cat 1) is the #1 hotspot at 32%.** It uses a generic spend-based proxy, so it is also the **most uncertain** number. Better supplier data is the top data-strategy priority.
- **Grid electricity (25%)** and **diesel generators (20%)** come next. Nigeria's grid intensity (0.456 kgCO2e/kWh) is about 3.5× the UK's, which makes on-site solar especially valuable.
- **Progress:** −9.6% by 2025 is slightly **ahead** of the straight-line path to −30% by 2030 (−8.6% by 2025). The remaining 20 percentage points still need structural changes, not just efficiency gains.

<p float="left">
  <img src="reports/figures/02_emission_hotspots.png" width="49%" />
  <img src="reports/figures/03_target_progress.png" width="49%" />
</p>

## 🛠️ Decarbonisation Strategy (scenario model)
Nine reduction levers were sized against the 2025 baseline and costed with **2026 Nigerian market prices**: diesel ₦1,900/L, Band A grid tariff ₦209.5/kWh, ₦1,350/USD. Each lever is ranked on a **marginal abatement cost curve (MACC)**.

| Result | Value |
|---|---|
| Physical abatement (8 levers) | **~800 tCO2e/yr (−21% vs 2025)** |
| + Renewable PPA (market-based) | ~1,050 tCO2e/yr (−27%) |
| Total capex | **$424k** |
| Net annualised saving | **~$124k/yr** (the portfolio pays for itself) |
| Port Harcourt solar-battery hybrid | ~215 tCO2e/yr, **~2-year payback** |
| 2030 vs SBTi-aligned target | ✅ Met **only with the PPA** (market-based); ❌ missed on a location basis |

![MACC](reports/figures/05_macc_curve.png)
![Pathway](reports/figures/06_decarbonisation_pathway.png)

**So what?** The first wave of levers is cost-negative and should be funded now. Growth of +2%/yr erodes the gains after 2027, though, so a **second wave** is needed by ~2029 to stay on an SBTi path to 2035: deeper supplier engagement, fleet conversion and more on-site solar. Explore it interactively in the dashboard's **Scenarios** tab, where you can change the diesel price, FX, discount rate, growth and lever selection.

## 💡 Recommendations
0. **Fund the cost-negative levers first:** travel policy, the Port Harcourt solar-battery hybrid, efficiency, rooftop solar (see [notebook 02](notebooks/02_decarbonisation_scenarios.ipynb)).
1. **Supplier engagement:** collect primary data from the top suppliers. Move from a generic spend proxy to category-level (NAICS-mapped) factors, then to supplier-specific data.
2. **Solar + battery hybrid systems** at Port Harcourt Plant to cut diesel and grid dependence.
3. **Energy efficiency:** HVAC upgrades and refrigerant leak management.
4. **Travel policy:** virtual-first meetings and fewer long-haul flights.
5. **Set a formal target** aligned with SBTi, and report annually using this pipeline.

## 🚀 Getting Started
```bash
git clone https://github.com/Engr-Daniel/carbon-footprint-esg-dashboard.git
cd carbon-footprint-esg-dashboard
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run the dashboard
streamlit run app/streamlit_app.py

# Run tests
pytest -q

# Regenerate report charts
python src/carbon/report_figures.py
```

## 🛠️ Tech Stack
Python (pandas, plotly, matplotlib) · Streamlit · SQL · Jupyter · pytest

## 📚 Data Sources & References
- [GHG Protocol](https://ghgprotocol.org/) – Corporate Standard & Scope 3 Standard
- [UK DESNZ – GHG Conversion Factors 2026](https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026) (published June 2026, AR5 GWP100)
- [Ember – Yearly Electricity Data](https://ember-energy.org/data/yearly-electricity-data/) (Nigeria grid intensity 2025, CC BY 4.0)
- [US EPA – Supply Chain GHG Emission Factors v1.3](https://doi.org/10.23719/1531143) (USD 2022)
- [SBTi Corporate Near-Term Criteria](https://sciencebasedtargets.org/) – 4.2%/yr (Scope 1+2), 2.5%/yr (Scope 3) minimum rates
- Cost data: NBS / depot diesel and petrol prices (2026), NERC Band A tariff, 2026 Nigerian solar market pricing
- IPCC AR5 – Global Warming Potentials
- IFRS S2 – Climate-related Disclosures

## 👤 Author
**Daniel Oyewale**, Data Analyst · Data Strategist · Sustainability Researcher at [Petgrave.io](https://petgrave.io)

## 📄 License
MIT. See [LICENSE](LICENSE).
