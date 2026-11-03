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

## Current results snapshot (synthetic activity data, real factors as of Phase 2)
- Total 2023–2025: **12,270 tCO2e** (S1 ≈ 3,572 · S2 ≈ 3,116 · S3 ≈ 5,582)
- 2025: 3,881 tCO2e, **−9.6% vs the 2023 baseline**, slightly ahead of the linear −30%-by-2030 path (−8.6% by 2025)
- Top hotspot: Scope 3 Cat 1 purchased goods (32%), then grid electricity (25%) and diesel (20%)
- Port Harcourt Plant = 56% of the total
- The Python engine and the SQL view give identical totals (12,270.2 tCO2e)

## Scenario results snapshot (Phase 3)
- 9 levers: physical abatement ~800 tCO2e/yr (−21% vs 2025); with the PPA, ~1,048 (−27%)
- Capex $424k; net annualised saving ~$124k/yr; 4 cost-negative levers deliver 48% of abatement
- L2 Port Harcourt solar hybrid: ~215 t/yr, ~2-yr payback (3.2 yrs even at ₦1,200/L diesel)
- 2030: market-based 3,128 vs SBTi target 3,264 ✅; location-based 3,402 ❌. 2035: both miss (growth +2%/yr)

## Decision log
| Date | Decision | Reason |
|---|---|---|
| 2026-11-04 | Levers applied sequentially to residual activity | Avoids double-counting overlapping levers (efficiency, then solar) |
| 2026-11-04 | SBTi target split: S1+2 4.2%/yr, S3 2.5%/yr from 2023 | SBTi near-term criteria; S3 ≥40% of the total, so a S3 target is required |
| 2026-11-04 | Discount rate 12% real USD; BAU growth 2%/yr; FX ₦1,350/$ | Reflects Nigerian cost of capital. All three are adjustable in the dashboard |
| 2026-11-04 | Cost inputs sourced to Oct 2026 market data (diesel ₦1,900/L depot, Band A ₦209.5/kWh) | Credibility. Capex/opex per lever remain labelled assumptions |
| 2026-11-04 | PPA/I-REC lever (L9) affects market-based Scope 2 only | GHG Protocol Scope 2 dual reporting |
| 2026-11-04 | Replace indicative factors with DESNZ 2026, Ember 2025 (Nigeria grid) and EPA Supply Chain v1.3 | Phase 2: credibility. Every factor now has a year, a source URL and a verification status |
| 2026-11-04 | Use **100% mineral** diesel and petrol factors, not the UK average biofuel blend | Nigerian AGO and PMS have no biofuel blend |
| 2026-11-04 | Nigeria grid = 0.456 kgCO2e/kWh (Ember 2025, lifecycle) | Latest open, country-specific average. IFI factors (395/477 g, v2.0 2019) are *combined-margin* factors for RE projects, not inventory averages |
| 2026-11-04 | Flights include radiative forcing. Renamed `business_travel_air_shorthaul` → `business_travel_air_domestic` | DESNZ recommends RF. Nigerian domestic flights best match the DESNZ "domestic" factor |
| 2026-11-04 | Spend proxy = 0.2819 kgCO2e/USD (mean of non-zero EPA v1.3 commodity factors) | Primary-sourced generic proxy until spend is mapped to NAICS codes |
| 2026-11-04 | Default factor policy `latest` (newest factors applied to all years); `matching` also available | Like-for-like trend, consistent with GHG Protocol base-year recalculation |
| 2026-11-04 | Use the GHG Protocol, operational control approach, 2023 baseline | Industry standard, and simplest for a single-entity case |
| 2026-11-04 | Scope 2 location-based only (for now) | No PPA or REC data in the case; market-based is on the roadmap |
| 2026-11-04 | Spend-based method for Scope 3 Cat 1 | Typical first step for SMEs without supplier data |
| 2026-11-04 | Emission factors in a CSV with a `source` column | Transparent, auditable, easy for non-coders to update |
| 2026-11-04 | Streamlit for the dashboard (not Power BI) | Free hosting, code-based, reproducible, and the repo stays self-contained |
| 2026-11-04 | Calculation engine raises errors on missing factors and unit mismatches | Prevents silent errors that would undermine credibility |

## Open questions
- Confirm the factors marked "Secondary source" against the official DESNZ 2026 full-set workbook. It can't be downloaded from the build environment, so open it in a browser.
- Does Nigeria's DNA/NCCC publish an official national grid factor? If so, prefer it to Ember.
- Add a Power BI version too, for recruiters who expect it?
- Should we replace synthetic data with a real public company's disclosed data (e.g. a Nigerian listed company's sustainability report)?

## Lessons learned
- An earlier README claimed the company was "off track". With a linear pathway it is actually slightly ahead. Always check claims against the chart.
- Plotly hotspot bars coloured by scope need `update_yaxes(categoryorder="total ascending")` to stay sorted.
- Streamlit ≥1.50: use `width="stretch"` instead of the deprecated `use_container_width=True`.
