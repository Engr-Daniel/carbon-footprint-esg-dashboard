# MEMORY.md

Long-term project memory: context, decisions and lessons. Add new entries at the top of the Decision Log, and keep them short.

## Project context
- **Owner:** Daniel Oyewale (Data Analyst · Data Strategist · Sustainability Researcher, Petgrave.io)
- **Purpose:** Portfolio project showing end-to-end carbon accounting, data modelling, dashboarding and decarbonisation strategy
- **Audience:** Recruiters, ESG consulting clients, sustainability and data teams
- **Repo visibility:** Private during the build. Make it public once real factors are verified and the dashboard is deployed.

## Fictional case company
- **EcoNaija Manufacturing Ltd**, Nigeria
- Sites: Lagos HQ, Abuja Office, Port Harcourt Plant (the plant is the largest emitter and the only site using natural gas)
- Data: monthly activity data for 2023–2025, synthetic and generated with a fixed random seed (42), with a built-in downward trend (2024: −4%, 2025: −9%)

## Current results snapshot (synthetic)
- Total 2023–2025: ~13,023 tCO2e (S1 ≈ 3,590 · S2 ≈ 2,938 · S3 ≈ 6,495)
- 2025 vs 2023 baseline: −9.8%
- Top hotspot: Scope 3 Cat 1 purchased goods & services (spend-based)

## Decision log
| Date | Decision | Reason |
|---|---|---|
| 2026-11-04 | Use the GHG Protocol, operational control approach, 2023 baseline | Industry standard, and simplest for a single-entity case |
| 2026-11-04 | Scope 2 location-based only (for now) | No PPA or REC data in the case; market-based is on the roadmap |
| 2026-11-04 | Spend-based method for Scope 3 Cat 1 | Typical first step for SMEs without supplier data |
| 2026-11-04 | Emission factors in a CSV with a `source` column | Transparent, auditable, easy for non-coders to update |
| 2026-11-04 | Streamlit for the dashboard (not Power BI) | Free hosting, code-based, reproducible, and the repo stays self-contained |
| 2026-11-04 | Calculation engine raises errors on missing factors and unit mismatches | Prevents silent errors that would undermine credibility |

## Open questions
- Which official Nigeria grid emission factor and year should we use? (IFI Harmonised vs IEA vs national source)
- Add a Power BI version too, for recruiters who expect it?
- Should we replace synthetic data with a real public company's disclosed data (e.g. a Nigerian listed company's sustainability report)?

## Lessons learned
- Streamlit ≥1.50: use `width="stretch"` instead of the deprecated `use_container_width=True`.
