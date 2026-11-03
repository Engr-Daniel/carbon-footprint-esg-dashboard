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
- [ ] Open the official DESNZ 2026 workbook and confirm the factors marked "Secondary source" *(needs a browser; **you**)*
- [ ] Map purchased-goods spend to NAICS categories and use commodity-specific EPA factors (split the synthetic spend into e.g. raw materials, packaging, IT and services)

## 📈 Phase 3: Strategy & insight
- [ ] Scenario modelling notebook (`02_decarbonisation_scenarios.ipynb`): solar hybrid, efficiency, travel policy, supplier engagement
- [ ] Marginal abatement cost curve (MACC): cost per tCO2e for each lever
- [ ] Intensity metrics: tCO2e per employee and per USD million revenue
- [ ] Net-zero pathway chart (SBTi-aligned ~4.2%/yr linear reduction)
- [ ] Market-based Scope 2 (RECs / solar PPA)

## 🚀 Phase 4: Deploy & publish
- [ ] Load data into SQLite through `sql/schema.sql` and show SQL queries in a notebook
- [ ] Add CSV upload to the dashboard so users can analyse their own data
- [ ] Deploy to **Streamlit Community Cloud** and add the live link to the README
- [ ] GitHub Actions CI: run `pytest` on every push
- [ ] Write a 1–2 page **executive summary / ESG report** (PDF) in `reports/`
- [ ] Make the repo **public**, pin it on your GitHub profile, and share a LinkedIn post

## 💭 Ideas / backlog
- Power BI version of the dashboard
- Use a real Nigerian listed company's disclosed sustainability data
- IFRS S2 disclosure template auto-filled from the results
