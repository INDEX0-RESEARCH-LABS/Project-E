"""Transparent lifecycle cost model.

Costs are discounted; energy is discounted with the same factor, which is the standard
levelized-cost formulation. All inputs are USD and kWh; no currency conversion is hidden.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models.validation import fraction, nonnegative, positive, require


@dataclass(frozen=True)
class CostStreams:
    capex_usd: float
    annual_energy_kwh: float
    annual_om_usd: float = 0.0
    annual_fuel_usd: float = 0.0
    replacements_usd: dict[int, float] = field(default_factory=dict)
    lifetime_years: float = 10.0
    discount_rate: float = 0.08

    def __post_init__(self) -> None:
        nonnegative("capex_usd", self.capex_usd)
        positive("annual_energy_kwh", self.annual_energy_kwh, "kWh/a")
        nonnegative("annual_om_usd", self.annual_om_usd)
        nonnegative("annual_fuel_usd", self.annual_fuel_usd)
        positive("lifetime_years", self.lifetime_years, "a")
        fraction("discount_rate", self.discount_rate)
        for year, cost in self.replacements_usd.items():
            require(isinstance(year, int) and year >= 1, f"replacement year must be int >= 1, got {year}")
            nonnegative("replacement cost", cost)

    def discounted(self) -> tuple[float, float]:
        """Return (NPV of costs, NPV of delivered energy)."""
        npv_cost = self.capex_usd
        npv_energy = 0.0
        years = int(round(self.lifetime_years))
        for year in range(1, years + 1):
            factor = (1.0 + self.discount_rate) ** -year
            npv_cost += (self.annual_om_usd + self.annual_fuel_usd) * factor
            npv_energy += self.annual_energy_kwh * factor
            npv_cost += self.replacements_usd.get(year, 0.0) * factor
        return npv_cost, npv_energy

    @property
    def lcoe_usd_per_kwh(self) -> float:
        npv_cost, npv_energy = self.discounted()
        require(npv_energy > 0, "no discounted energy delivered")
        return npv_cost / npv_energy

    @property
    def simple_cost_per_kwh(self) -> float:
        """Undiscounted total cost divided by undiscounted delivered energy."""
        total = (
            self.capex_usd
            + (self.annual_om_usd + self.annual_fuel_usd) * self.lifetime_years
            + sum(self.replacements_usd.values())
        )
        energy = self.annual_energy_kwh * self.lifetime_years
        return total / energy
