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
| 2 | Purchased electricity | grid_electricity_ng | kWh | Location-based |
| 3 | Cat 1 – Purchased goods & services | purchased_goods_spend | USD | Spend-based (EEIO) |
| 3 | Cat 5 – Waste | waste_landfill | tonne | Waste-type specific |
| 3 | Cat 6 – Business travel | air short/long-haul | passenger_km | Distance-based |
| 3 | Cat 7 – Employee commuting | employee_commute_car | km | Distance-based |

## 5. Calculation
```
kgCO2e = quantity × emission_factor (kgCO2e per unit)
tCO2e  = kgCO2e / 1000
```
The engine (`src/carbon/emissions.py`) **fails loudly** in these cases:
- an activity type has no emission factor
- the activity unit doesn't match the factor unit
- quantities are negative

## 6. Emission factors
Stored in `data/reference/emission_factors.csv`. Each row has a `factor_year`, `gwp_basis`, `source`, `source_url` and a `verification` status.

| Activity | Factor | Unit | Source |
|---|---|---|---|
| Diesel (100% mineral) | 2.66155 | kgCO2e/litre | DESNZ 2026 |
| Petrol (100% mineral) | 2.35372 | kgCO2e/litre | DESNZ 2026 |
| Natural gas (100% mineral blend) | 2.04987 | kgCO2e/m³ | DESNZ 2026 |
| LPG | 1.55713 | kgCO2e/litre | DESNZ 2026 |
| R-410A refrigerant | 1,924 | kgCO2e/kg | IPCC AR5 GWP100 (DESNZ 2026) |
| Nigeria grid electricity | 0.456 | kgCO2e/kWh | Ember 2025 |
| Domestic flight (with RF) | 0.22928 | kgCO2e/passenger-km | DESNZ 2026 |
| Long-haul economy flight (with RF) | 0.11704 | kgCO2e/passenger-km | DESNZ 2026 |
| Average petrol car | 0.16152 | kgCO2e/km | DESNZ 2026 |
| Mixed municipal waste to landfill | 497.29 | kgCO2e/tonne | DESNZ 2026 |
| Purchased goods (generic spend proxy) | 0.2819 | kgCO2e/USD (2022) | US EPA Supply Chain Factors v1.3 |

### Key factor choices
- **100% mineral fuel factors** are used for diesel and petrol, not the UK pump "average biofuel blend". Nigerian AGO and PMS carry no biofuel blend.
- **Nigeria grid:** Ember's intensity is *lifecycle* (it includes upstream emissions), so Scope 2 is slightly conservative (overstated). A combustion-only national factor is preferable once one is published.
- **Flights** include radiative forcing (RF), following DESNZ's recommendation. The DESNZ "domestic" factor stands in for short Nigerian domestic flights (e.g. Lagos–Abuja, ~520 km).
- **Spend-based Cat 1** uses the mean of non-zero US commodity factors as a generic proxy. It is US-economy and USD-2022 based, so it is the **most uncertain** line.

### Factor-year policy
`calculate_emissions(..., policy="latest")` (the default) applies the most recent factor set to **all** years. This gives a like-for-like trend, consistent with the GHG Protocol's guidance to recalculate the base year when methodology changes. `policy="matching"` uses the factor year that matches each reporting year, falling back to the closest earlier year (this mirrors statutory year-by-year reporting).

### Verification status
DESNZ values were taken from published reproductions of the 2026 workbook. Values marked `Cross-checked` agree across at least two independent sources. Values marked `Secondary source – confirm in workbook` should be checked against the official `ghg-conversion-factors-2026-full-set.xlsx` before any external use.

## 7. Limitations & assumptions
- Activity data is synthetic and only demonstrates the method.
- DESNZ factors reflect UK conditions. Landfill, commuting and spend factors are proxies for Nigeria and likely **understate** local emissions (open dumpsites, older vehicle fleet).
- Scope 2 is location-based only. Market-based reporting is not yet included.
- Spend-based Scope 3 is highly uncertain. It should be replaced by supplier-specific data over time.
- Some Scope 3 categories (e.g. Cat 4 transport, Cat 11 use of sold products) are excluded for now.
