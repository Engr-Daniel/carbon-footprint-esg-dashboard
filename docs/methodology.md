# Methodology

## 1. Standard
This project follows the **GHG Protocol Corporate Accounting and Reporting Standard** and the **Corporate Value Chain (Scope 3) Standard**.

## 2. Organisational boundary
- **Approach:** Operational control
- **Entity:** EcoNaija Manufacturing Ltd (fictional)
- **Sites:** Lagos HQ, Abuja Office, Port Harcourt Plant

## 3. Reporting period
- Calendar years 2023, 2024 and 2025, with monthly activity data
- **Baseline year:** 2023

## 4. Operational boundary
| Scope | Category | Activity type | Unit | Method |
|---|---|---|---|---|
| 1 | Stationary & mobile combustion | diesel | litre | Activity-based |
| 1 | Mobile combustion | petrol | litre | Activity-based |
| 1 | Stationary combustion | natural_gas, lpg | m3, litre | Activity-based |
| 1 | Fugitive emissions | refrigerant_r410a | kg | Mass-balance (leakage × GWP) |
| 2 | Purchased electricity | grid_electricity_ng (`primary`) | kWh | Location-based (combustion-only) + market-based |
| 3 | Cat 3 – Fuel- & energy-related activities | diesel, petrol, natural_gas, lpg, grid (`wtt`, `td_losses`) | as activity | Upstream (WTT) + T&D losses |
| 3 | Cat 1 – Purchased goods & services | purchased_steel, _plastic_resin, _corrugated_packaging, _plastic_film, _chemicals, _machinery_repair, _it_services, _consulting, _cleaning_services | USD → 2022 USD | Spend-based (EEIO), category-specific |
| 3 | Cat 4 – Upstream transportation | upstream_freight_trucking | USD → 2022 USD | Spend-based (EEIO) |
| 3 | Cat 5 – Waste | waste_landfill | tonne | Waste-type specific |
| 3 | Cat 6 – Business travel | air short/long-haul | passenger_km | Distance-based |
| 3 | Cat 7 – Employee commuting | employee_commute_car | km | Distance-based |

## 5. Calculation
```
kgCO2e = quantity × emission_factor (kgCO2e per unit)
tCO2e  = kgCO2e / 1000
```
One activity can carry several factor **components**, each with its own scope and category. For example, a litre of diesel gives Scope 1 combustion (`primary`) **and** Scope 3 Cat 3 upstream supply (`wtt`). The engine joins one activity row to all of its components.

The engine (`src/carbon/emissions.py`) **fails loudly** in these cases:
- an activity type has no emission factor
- the activity unit doesn't match the factor unit
- quantities are negative

## 6. Emission factors
Stored in `data/reference/emission_factors.csv`. Each row is keyed by `activity_type` + `component` and has a `factor_year`, `gwp_basis`, `source`, `source_url` and a `verification` status (with the DESNZ workbook cell reference).

| Activity | Factor | Unit | Source |
|---|---|---|---|
| Diesel (100% mineral) | 2.66155 | kgCO2e/litre | DESNZ 2026 |
| Petrol (100% mineral) | 2.35372 | kgCO2e/litre | DESNZ 2026 |
| Natural gas (100% mineral blend) | 2.04987 | kgCO2e/m³ | DESNZ 2026 |
| LPG | 1.55713 | kgCO2e/litre | DESNZ 2026 |
| R-410A refrigerant | 1,924 | kgCO2e/kg | IPCC AR5 GWP100 (DESNZ 2026) |
| Nigeria grid electricity: Scope 2 (combustion) | 0.41686 | kgCO2e/kWh | Derived (see below) |
| Nigeria grid: Cat 3 upstream (WTT) | 0.07461 | kgCO2e/kWh | Derived |
| Nigeria grid: Cat 3 T&D losses | 0.03863 | kgCO2e/kWh | Derived |
| WTT diesel / petrol / natural gas / LPG | 0.62409 / 0.60664 / 0.3366 / 0.18551 | per litre / litre / m³ / litre | DESNZ 2026 (WTT- fuels) |
| Domestic flight (with RF) | 0.22928 | kgCO2e/passenger-km | DESNZ 2026 |
| Long-haul economy flight (with RF) | 0.11704 | kgCO2e/passenger-km | DESNZ 2026 |
| Average petrol car | 0.16152 | kgCO2e/km | DESNZ 2026 |
| Commercial & industrial waste to landfill | 520.58 | kgCO2e/tonne | DESNZ 2026 |
| Steel (NAICS 331110) / plastic resin (325211) | 0.787 / 1.045 | kgCO2e per 2022 USD | US EPA Supply Chain Factors v1.3 (with margins) |
| Corrugated boxes (322211) / plastic film (326112) / chemicals (325998) | 0.479 / 0.544 / 0.500 | kgCO2e per 2022 USD | US EPA v1.3 |
| Machinery repair (811310) / IT services (541512) / consulting (541611) / cleaning (561720) | 0.136 / 0.089 / 0.078 / 0.214 | kgCO2e per 2022 USD | US EPA v1.3 |
| Freight trucking, Cat 4 (484121) | 0.595 | kgCO2e per 2022 USD | US EPA v1.3 |

### Key factor choices
- **100% mineral fuel factors** are used for diesel and petrol, not the UK pump "average biofuel blend". Nigerian AGO and PMS carry no biofuel blend.
- **Nigeria grid (scope-correct split):** open factors such as Ember (0.456) are *lifecycle* and mix Scope 2 with upstream emissions. The IEA combustion-only factor is paid, and DESNZ no longer publishes overseas factors (its *Overseas electricity* tab says so). The factor is therefore **derived transparently** in `src/carbon/grid_factor.py`:
  - Scope 2 = gas share of generation **67.3%** (NERC 2025: 26,386 of 39,194 GWh, via NRGI 2026) × DESNZ 2026 natural-gas combustion **0.20434 kgCO2e/kWh NCV** (`Fuels!D45`) ÷ fleet efficiency **33%** (OCGT-dominated fleet; Nigerian studies report 25–39%) = **0.417**
  - Cat 3 WTT = gas share × DESNZ WTT natural gas **0.03347** (`WTT- fuels!D44`) ÷ efficiency, grossed up for losses = **0.075**
  - Cat 3 T&D = Scope 2 × TLF/(1−TLF), using NERC's transmission loss factor of **8.48%** = **0.039** (distribution losses aren't published, so this is likely understated)
  - **This is an estimate, not an official national factor.** Replace it with an official Nigerian (NCCC/DNA) or IEA combustion factor if one becomes available.
  - The components total **0.530**, which is consistent with Ember's lifecycle 0.456 given the uncertainty. The efficiency range of 28–38% gives a Scope 2 factor of 0.362–0.491. A test checks that the CSV values equal the derivation.
- **Cat 3 for fuels:** DESNZ WTT factors are added for every Scope 1 fuel, so upstream emissions are reported consistently for fuels and electricity.
- **Flights** include radiative forcing (RF), following DESNZ's recommendation. The DESNZ "domestic" factor stands in for short Nigerian domestic flights (e.g. Lagos–Abuja, ~520 km).
- **Spend-based Cat 1 and Cat 4 are category-specific.** Spend is split into 10 categories, each mapped to a NAICS-6 commodity in the official **US EPA Supply Chain GHG Emission Factors v1.3** CSV. The factors are *with margins* (purchaser price, cradle-to-shelf). The spend-weighted factor is **0.593** kgCO2e/USD, more than double the previous generic proxy (0.2819, the mean of all non-zero commodity factors). Materials (steel, resin) dominate.
- **Deflation:** EPA factors are per **2022 USD**, so nominal spend is converted with US CPI-U annual averages (`usd_deflators.csv`: 2023 ×1/1.041, 2024 ×1/1.072, 2025 ×1/1.100) before the factors are applied. The engine refuses to combine nominal `USD` with `USD2022` factors (unit check). The SQL view applies the same deflation.
- **Caveat:** these are US-economy factors applied to Nigerian purchases. They are a common screening practice, but supplier-specific or regional EEIO data (e.g. EXIOBASE Rest-of-Africa) would be more representative.

### Factor-year policy
`calculate_emissions(..., policy="latest")` (the default) applies the most recent factor set to **all** years. This gives a like-for-like trend, consistent with the GHG Protocol's guidance to recalculate the base year when methodology changes. `policy="matching"` uses the factor year that matches each reporting year, falling back to the closest earlier year (this mirrors statutory year-by-year reporting).

### Verification status
All DESNZ factors were **verified cell-by-cell against the official `ghg-conversion-factors-2026-full-set.xlsx`** on 2026-11-04. The `verification` column records each cell reference (e.g. `Fuels!D76`). This check corrected one factor: waste moved from *household residual waste* (497.29) to **commercial and industrial waste → landfill (520.58)**, which is the right category for a company. The Nigeria grid factor is not in DESNZ (UK-only), so it is derived from verified DESNZ inputs plus NERC data (above). The spend-based factors were verified against the official EPA v1.3 CSV (NAICS code recorded in the `verification` column).

**Optional refinement:** DESNZ also publishes *International, to/from non-UK* flight factors (economy with RF: 0.10916, `Business travel- air!E33`). These may suit Nigerian international routes that don't touch the UK better than the *long-haul to/from UK* factor used here.

## 7. Scenario modelling
Code: `src/carbon/scenarios.py`. Inputs: `data/reference/reduction_levers.csv` and `data/reference/cost_assumptions.csv`.

- **Baseline:** 2025 annual activity by site and activity type.
- **Sequential application:** levers run in `order` on the *residual* activity, so efficiency (L1) reduces the load before rooftop solar (L3) is sized. Abatement is never double-counted.
- **Location vs market levers:** physical levers reduce activity, and their abatement counts **every factor component** (avoided diesel cuts Scope 1 *and* Cat 3 upstream). Contractual instruments (PPA / I-RECs, L9) leave activity unchanged and reduce **market-based Scope 2 only** (they don't change physical supply chains, so there is no Cat 3 effect).
- **Costs:** annualised cost = capex × CRF(r, n) + opex − savings, where CRF = r(1+r)ⁿ / ((1+r)ⁿ − 1) and r = 12% real USD. Savings = avoided activity × unit price (diesel, petrol, grid, flights, refrigerant, landfill fees). Commuting and supplier levers carry no company savings.
- **Pathway:** BAU grows +2%/yr from 2025. Each lever **phases in linearly** over `ramp_years` from its `start_year` (e.g. supplier engagement takes 3 years). Abatement is scaled by growth.
- **Uncertainty:** each lever has `reduction_pct_low` / `reduction_pct_high`. `pathway_range()` produces low/high bands. `sensitivity_analysis()` runs one-at-a-time tests (diesel ±30%, FX ±25%, tariff ±30%, discount rate 8%/18%, capex ±25%, effectiveness low/high, growth 0%/4%) on the net annual saving and the 2030 target gap.
- **Target benchmark (not a validated target):** the pathway is compared with a line modelled at the SBTi Absolute Contraction Approach minimum rates from the 2023 base year: **Scope 1+2 −4.2%/yr** (1.5°C) and **Scope 3 −2.5%/yr** (well-below 2°C, required because Scope 3 is ≥40% of the total).
- **Dual Scope 2 with instrument quality checks:** `validate_instruments()` applies the **GHG Protocol Scope 2 Quality Criteria** before any instrument gets a zero factor. The instrument must (1) convey the energy-attribute claim (a bare PPA without certificates does not), (2) be retired/cancelled on behalf of the company, (3) be tracked in a registry, (4) have a vintage matching the reporting year, (5) come from the same market (Nigeria), and (6) not be double counted. Only eligible MWh reduce market-based Scope 2. Nigeria has no residual-mix factor, so uncovered kWh use the grid average (the Scope 2 Guidance fallback), and this is disclosed. Sample instruments are synthetic and include deliberate failures to show the checks working. Lever L9 assumes that future contracts meet these criteria.
- **Intensity:** tCO2e per employee, per USD m revenue and per tonne of product (synthetic company profile).

## 8. Restatements
Activity data is unchanged across versions. All changes in totals come from methodology, so all years (including the 2023 base year) are recalculated, per GHG Protocol base-year recalculation guidance: 12,270 → 12,281 (waste factor fix) → 13,525 (grid scope split + Cat 3) → **17,313 tCO2e** (category-specific spend + deflation). Grid-efficiency sensitivity (28–38%): 3-year total 17,959 to 16,836 tCO2e.

## 9. Limitations & assumptions
- Activity data is synthetic and only demonstrates the method.
- DESNZ factors reflect UK conditions. Landfill, commuting and spend factors are proxies for Nigeria and likely **understate** local emissions (open dumpsites, older vehicle fleet).
- The target line is a benchmark at SBTi minimum rates. EcoNaija (fictional) has **no SBTi-validated target**.
- Market-based Scope 2 is implemented with quality checks, but there is no Nigerian residual mix, so the grid-average fallback may double count attributes sold to others.
- The Nigeria grid factor depends on an assumed fleet efficiency (33%, range 28–38%) and only transmission (not distribution) losses.
- Spend-based Scope 3 (Cat 1 and Cat 4) uses US-economy factors and US CPI deflation. It is category-specific but still uncertain, and should be replaced by supplier-specific data over time.
- Lever capex, opex and reduction percentages are documented **assumptions**, not quotes. Fuel prices and FX are volatile, so use the dashboard inputs and the notebook's sensitivity table.
- Levers ramp up linearly and then hold constant. There is no grid decarbonisation or solar degradation. Uncertainty ranges are one-at-a-time, not a joint (Monte Carlo) distribution.
- Some Scope 3 categories (e.g. Cat 2 capital goods, Cat 9 downstream transport, Cat 11 use of sold products) are excluded for now.
