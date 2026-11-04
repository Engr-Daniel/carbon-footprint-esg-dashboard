# TASK.md

Roadmap and task tracker. Status: `[x]` done · `[ ]` to do · `[~]` in progress

## ✅ Phase 1: Foundation (done)
- [x] Repo setup, folder structure, .gitignore, requirements
- [x] Synthetic activity dataset (3 sites, 2023–2025, monthly)
- [x] Emission factor library with sources
- [x] Calculation engine (`src/carbon/emissions.py`) with validation
- [x] Unit tests (pytest)
- [x] SQL schema and emissions view
- [x] Exploratory notebook with findings
- [x] Streamlit dashboard: KPIs, scope breakdown, hotspots, site trends, target tracking
- [x] README, methodology, AGENTS.md, MEMORY.md, TASK.md

## ✅ Phase 2: Credibility (done, 2026-11-04)
- [x] Replace indicative factors with **DESNZ 2026** values (fuels, travel, waste, refrigerant)
- [x] Apply a current **Nigeria grid factor**: 0.456 kgCO2e/kWh (Ember 2025)
- [x] Replace the placeholder spend factor with a primary-sourced **EPA Supply Chain v1.3** proxy
- [x] Add `factor_year`, `gwp_basis`, `source_url` and `verification` columns, plus year-specific factor support (`policy="latest" | "matching"`)
- [x] Export key charts to `reports/figures/` and embed them in the README
- [x] Add a dashboard screenshot to the README
- [x] Update the SQL schema to support multiple factor years; check SQL total = Python total
- [x] Verify all DESNZ factors against the official 2026 workbook (cell refs in the CSV); waste factor corrected to commercial & industrial (520.58)
- [ ] Map purchased-goods spend to NAICS categories and use commodity-specific EPA factors (split the synthetic spend into e.g. raw materials, packaging, IT and services)

## ✅ Phase 3: Strategy & insight (done, 2026-11-04)
- [x] Scenario engine (`src/carbon/scenarios.py`) with 9 sourced and costed levers
- [x] Scenario notebook `02_decarbonisation_scenarios.ipynb` (levers, MACC, pathway, diesel-price sensitivity, recommendations)
- [x] Marginal abatement cost curve (static + interactive)
- [x] Intensity metrics: tCO2e per employee, per USD m revenue, per tonne of product
- [x] SBTi-aligned pathway (S1+2 4.2%/yr, S3 2.5%/yr) vs BAU and with-lever scenarios to 2035
- [x] Market-based Scope 2 (PPA / I-RECs) with dual reporting
- [x] Dashboard tabs: Scenarios (editable prices/FX/levers) and Intensity & Scope 2
- [ ] Second-wave levers (fleet CNG/EV, larger supplier programme, more solar) to close the 2035 gap
- [x] Add lever ramp-up to the pathway
- [ ] Solar degradation, grid decarbonisation, Monte Carlo joint uncertainty (backlog)

## 🚀 Phase 4: Review fixes, deploy & publish
### External review fixes
- [x] Scope-correct Nigeria grid factor (S2 combustion-only; WTT + T&D → Cat 3) with derivation module + test
- [x] Cat 3 upstream (WTT) factors for all Scope 1 fuels
- [x] Scope 2 contractual instrument quality checks (GHG Protocol Scope 2 Quality Criteria)
- [x] Lever ramp-up, low/high effectiveness bands, one-at-a-time sensitivity (+ tornado chart)
- [x] Methodology limitations updated (market-based is implemented)
- [x] Map purchased-goods spend to 10 category-specific EPA v1.3 factors (incl. Cat 4 freight), CPI-deflated to 2022 USD
### Delivery
- [x] GitHub Actions CI: unit + regression + SQL-parity tests, dashboard smoke test, notebook execution
- [x] Executive summary PDF generated from live numbers (`reports/executive_summary.pdf`)
- [x] Publishing checklist + LinkedIn draft (`docs/PUBLISHING.md`)
- [x] Make the repo **public** (pin it on your profile: *you*)
- [x] Deploy to Streamlit Community Cloud (https://carbon-footprint-esg-dashboard.streamlit.app/) and add the URL to the README
- [ ] Post on LinkedIn *(you)*

## 💭 Ideas / backlog
- Power BI version of the dashboard
- Use a real Nigerian listed company's disclosed sustainability data
- IFRS S2 disclosure template auto-filled from the results
