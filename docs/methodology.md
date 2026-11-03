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
Stored in `data/reference/emission_factors.csv`, with the source and notes for each factor. **All current values are indicative.** Before real-world use, replace them with:
- the latest DEFRA/DESNZ conversion factors (fuels, travel, waste)
- a current Nigeria grid emission factor (IFI Harmonised / IEA / national data)
- EEIO spend-based factors (EXIOBASE / USEEIO) for Scope 3 Cat 1

## 7. Limitations & assumptions
- Synthetic data is used to demonstrate the method.
- Scope 2 is location-based only. Market-based reporting is not yet included.
- Spend-based Scope 3 is highly uncertain. It should be replaced by supplier-specific data over time.
- Some Scope 3 categories (e.g. Cat 4 transport, Cat 11 use of sold products) are excluded for now.
