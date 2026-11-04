"""Derivation of Nigeria grid electricity factors, split by GHG Protocol scope.

Why: open lifecycle factors (e.g. Ember, 0.456 kgCO2e/kWh) bundle generation-stage
combustion (Scope 2) with upstream fuel supply (Scope 3 Cat 3). The IEA combustion-only
factor is paid, and DESNZ no longer publishes overseas factors. This module derives each
component transparently from sourced inputs, so the split is reproducible and auditable.

  Scope 2          = gas share x combustion factor of gas (per kWh fuel, NCV) / fleet efficiency
  Cat 3 WTT        = gas share x WTT factor of gas / efficiency, grossed up for T&D losses
  Cat 3 T&D losses = Scope 2 factor x TLF / (1 - TLF)
Hydro (the rest of the grid mix) has zero combustion and no fuel supply chain.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GridInputs:
    gas_share: float = 26386 / 39194      # NERC 2025 generation: gas 26,386 of 39,194 GWh (via NRGI, Jul 2026)
    efficiency: float = 0.33              # Net LHV efficiency; OCGT-dominated fleet, studies show 25-39%
    gas_comb_ncv: float = 0.20434         # DESNZ 2026 Fuels!D45 natural gas (100% mineral), kgCO2e/kWh NCV
    gas_wtt_ncv: float = 0.03347          # DESNZ 2026 WTT- fuels!D44 natural gas (100% mineral), kgCO2e/kWh NCV
    tlf: float = 0.0848                   # NERC Q1 2024 transmission loss factor (8.48%)


def derive(inp: GridInputs = GridInputs()) -> dict[str, float]:
    """Return kgCO2e per kWh consumed for each component."""
    if not (0 < inp.efficiency <= 1 and 0 <= inp.gas_share <= 1 and 0 <= inp.tlf < 1):
        raise ValueError("Invalid grid inputs.")
    scope2 = inp.gas_share * inp.gas_comb_ncv / inp.efficiency
    loss_multiplier = inp.tlf / (1 - inp.tlf)
    wtt = inp.gas_share * inp.gas_wtt_ncv / inp.efficiency * (1 + loss_multiplier)
    td = scope2 * loss_multiplier
    return {"primary": scope2, "wtt": wtt, "td_losses": td, "total": scope2 + wtt + td}


def sensitivity(effs: tuple[float, ...] = (0.28, 0.33, 0.38)) -> dict[float, dict[str, float]]:
    """Factor components across a plausible fleet-efficiency range."""
    return {e: derive(GridInputs(efficiency=e)) for e in effs}


if __name__ == "__main__":
    for e, d in sensitivity().items():
        print(f"efficiency {e:.0%}: " + ", ".join(f"{k}={v:.5f}" for k, v in d.items()))
