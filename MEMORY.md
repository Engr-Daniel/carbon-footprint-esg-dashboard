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

## Current results snapshot (Phase 4: scope-correct grid factor + Cat 3)
- Total 2023–2025: **13,525 tCO2e** (S1 3,572 · S2 2,848 · S3 7,105). Scope 3 is 53% and includes Cat 3 (~11%)
- 2025: 4,283 tCO2e, **−9.4% vs 2023**
- Top hotspot: Cat 1 purchased goods (29%), then grid electricity (21%) and diesel (~18%). Port Harcourt = 56%
- The Python engine and the SQL view give identical totals (tested in CI)

## Scenario results snapshot
- Physical abatement ~887 tCO2e/yr (−21% vs 2025); with renewable contracts, ~1,114
- Capex $424k; net annualised saving ~$124k/yr (min ~$52k/yr across sensitivities); 4 cost-negative levers deliver 52% of abatement
- L2 Port Harcourt solar hybrid: ~266 t/yr, ~2-yr payback
- 2030 (phased): market-based gap −135 t (range −367 to +153 t); location-based +115 t ❌. 2035: both miss

## Decision log
| Date | Decision | Reason |
|---|---|---|
| 2026-11-04 | External review (6 findings) addressed in Phase 4 | Grid scope split, instrument checks, ramp/uncertainty, CI, docs. Scope 3 category mapping is pending the EPA CSV |
| 2026-11-04 | Nigeria grid factor **derived**: S2 0.417 (gas share 67.3% × DESNZ gas 0.20434/kWh NCV ÷ 33% efficiency); Cat 3 WTT 0.075, T&D 0.039 | Ember is lifecycle (mixes scopes); IEA is paid; DESNZ dropped overseas factors. Total 0.530 ≈ Ember 0.456 within uncertainty |
| 2026-11-04 | Factors keyed by activity_type + **component** (primary / wtt / td_losses); WTT added for all fuels | Cat 3 reported consistently; one activity → several scopes |
| 2026-11-04 | Market-based Scope 2 only counts instruments passing GHG Protocol Scope 2 Quality Criteria | Prevents unsupported zero-emission claims |
| 2026-11-04 | Levers ramp up linearly (`ramp_years`) with low/high effectiveness ranges; one-at-a-time sensitivity | Realism and transparency on uncertainty |
| 2026-11-04 | Regression test pins headline numbers; CI runs tests, dashboard smoke test and notebooks | Catch silent drift before publication |
| 2026-11-04 | All DESNZ factors verified cell-by-cell against the official 2026 full-set workbook (uploaded by Daniel). Waste corrected 497.29 → **520.58** kgCO2e/t | 497.29 was *household residual* waste; a company should use *Commercial and industrial waste* → Landfill (Waste disposal!I52). Total +11 tCO2e; no conclusion changed |
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
- Does Nigeria's DNA/NCCC publish an official national grid factor? If so, prefer it to Ember.
- Add a Power BI version too, for recruiters who expect it?
- Should we replace synthetic data with a real public company's disclosed data (e.g. a Nigerian listed company's sustainability report)?

## Lessons learned
- ReportLab's built-in fonts have no ₦ glyph (it renders as a black box). Use "NGN" in PDFs.
- Generate notebook findings text from code (IPython Markdown) so the numbers can't go stale.
- Secondary-source reproductions can map to the wrong row (household vs commercial waste). Always verify against the primary workbook and record the cell reference.
- An earlier README claimed the company was "off track". With a linear pathway it is actually slightly ahead. Always check claims against the chart.
- Plotly hotspot bars coloured by scope need `update_yaxes(categoryorder="total ascending")` to stay sorted.
- Streamlit ≥1.50: use `width="stretch"` instead of the deprecated `use_container_width=True`.
