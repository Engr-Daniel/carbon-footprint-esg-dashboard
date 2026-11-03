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

## 🔜 Phase 2: Credibility (next)
- [ ] Replace indicative factors with the **latest DEFRA/DESNZ** values (record year in `source`)
- [ ] Find and apply a current **Nigeria grid emission factor**
- [ ] Replace the placeholder spend-based factor with **EEIO factors** (EXIOBASE/USEEIO) by spend category
- [ ] Add a `valid_year` column to factors and support year-specific factors
- [ ] Export key charts to `reports/figures/` and embed them in the README
- [ ] Add a dashboard screenshot or GIF to the README

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
