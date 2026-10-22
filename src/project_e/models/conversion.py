"""Energy-conversion models with explicit, physically grounded limits.

Every function either cites a standard analytical relation (Carnot, TEG optimum
efficiency, Stefan-Boltzmann, detailed balance) or takes a measured/literature
efficiency as an explicitly labelled parameter. No generic "conversion efficiency"
constant is hidden inside the code.
"""

from __future__ import annotations

from dataclasses import dataclass

from .validation import fraction, nonnegative, positive, require, temperature_k

# Lower heating values, kWh per unit. Standard reference values.
LHV_H2_KWH_PER_KG = 33.33
LHV_DIESEL_KWH_PER_L = 9.94
LHV_METHANE_KWH_PER_KG = 13.89


def carnot_efficiency(t_hot_k: float, t_cold_k: float) -> float:
    """Maximum thermodynamic efficiency between two reservoirs."""
    th = temperature_k("t_hot_k", t_hot_k)
    tc = temperature_k("t_cold_k", t_cold_k)
    require(th > tc, f"hot reservoir ({th} K) must be hotter than cold ({tc} K)")
    return 1.0 - tc / th


def teg_efficiency(t_hot_k: float, t_cold_k: float, zt: float) -> float:
    """Optimum TEG efficiency for average figure of merit ZT.

    eta = eta_C * (sqrt(1+ZT) - 1) / (sqrt(1+ZT) + Tc/Th)
    (standard constant-property result; ZT is the device-average value).
    """
    th = temperature_k("t_hot_k", t_hot_k)
    tc = temperature_k("t_cold_k", t_cold_k)
    z = nonnegative("zt", zt, "-")
    eta_c = carnot_efficiency(th, tc)
    root = (1.0 + z) ** 0.5
    eta = eta_c * (root - 1.0) / (root + tc / th)
    return fraction("teg efficiency", eta)


def heat_engine_efficiency(
    t_hot_k: float, t_cold_k: float, carnot_fraction: float
) -> float:
    """Real heat engine: fraction of Carnot actually achieved.

    carnot_fraction is an engineering estimate (small Stirling/ORC typically
    0.35-0.55 of Carnot) and must be supplied with its provenance by the caller.
    """
    eta_c = carnot_efficiency(t_hot_k, t_cold_k)
    f = fraction("carnot_fraction", carnot_fraction)
    return eta_c * f


def tpv_efficiency(t_emitter_k: float, t_cell_k: float, measured_efficiency: float) -> float:
    """TPV conversion efficiency as a measured parameter, with a Carnot sanity guard.

    The literature anchor (S01) reports >40% for tandem III-V cells at 1900-2400 C
    emitter temperature. Efficiency does not extrapolate: below the characterized
    temperature the value must come from measurement, not from this function.
    """
    eta = fraction("measured_efficiency", measured_efficiency)
    eta_c = carnot_efficiency(t_emitter_k, t_cell_k)
    require(eta <= 0.95 * eta_c,
            f"TPV efficiency {eta:.3f} exceeds 0.95*Carnot ({0.95 * eta_c:.3f}); check units/claims")
    return eta


def pv_efficiency(eta_stc: float, temp_coefficient_per_k: float, cell_temp_c: float) -> float:
    """Single-junction PV efficiency with linear temperature correction.

    eta = eta_stc * (1 + gamma*(T_cell - 25 C)), gamma typically -0.003 to -0.005 /K.
    """
    eta0 = fraction("eta_stc", eta_stc)
    require(temp_coefficient_per_k <= 0,
            "PV temperature coefficient must be <= 0 (efficiency falls with temperature)")
    require(abs(temp_coefficient_per_k) <= 0.02,
            f"PV temperature coefficient magnitude implausible: {temp_coefficient_per_k} /K")
    require(-60.0 <= cell_temp_c <= 200.0, f"cell_temp_c outside credible range: {cell_temp_c}")
    eta = eta0 * (1.0 + temp_coefficient_per_k * (cell_temp_c - 25.0))
    require(eta > 0, "temperature correction produced non-positive efficiency")
    return fraction("pv efficiency", eta)


def fuel_consumption(power_kw: float, efficiency: float, lhv_kwh_per_unit: float) -> float:
    """Fuel mass/volume flow (unit per hour) for a given electrical output."""
    p = positive("power_kw", power_kw, "kW")
    eta = fraction("efficiency", efficiency)
    lhv = positive("lhv_kwh_per_unit", lhv_kwh_per_unit, "kWh/unit")
    return p / (eta * lhv)


@dataclass(frozen=True)
class SensibleHeatStore:
    """Sensible thermal storage: E = m*cp*(T_max - T_min)."""

    mass_kg: float
    cp_j_kg_k: float
    t_min_k: float
    t_max_k: float
    insulation_ua_w_k: float = 0.0

    def __post_init__(self) -> None:
        positive("mass_kg", self.mass_kg, "kg")
        positive("cp_j_kg_k", self.cp_j_kg_k, "J/kg/K")
        temperature_k("t_min_k", self.t_min_k)
        temperature_k("t_max_k", self.t_max_k)
        require(self.t_max_k > self.t_min_k, "t_max_k must exceed t_min_k")
        nonnegative("insulation_ua_w_k", self.insulation_ua_w_k, "W/K")

    @property
    def capacity_kwh(self) -> float:
        return self.mass_kg * self.cp_j_kg_k * (self.t_max_k - self.t_min_k) / 3.6e6

    def standby_loss_kwh(self, ambient_k: float, hours: float) -> float:
        ambient = temperature_k("ambient_k", ambient_k)
        h = nonnegative("hours", hours, "h")
        mean_t = 0.5 * (self.t_min_k + self.t_max_k)
        return self.insulation_ua_w_k * max(mean_t - ambient, 0.0) * h / 1000.0

    @property
    def mass_for_kwh(self) -> float:
        return self.mass_kg / self.capacity_kwh if self.capacity_kwh > 0 else float("inf")
