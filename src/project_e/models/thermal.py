"""Thermal transport reduced-order models: conduction, convection, radiation, lumped mass.

Temperature arguments are absolute kelvin and are validated as such. Celsius values
entering the API must be converted explicitly with celsius_to_kelvin(), which makes
unit errors visible at the call site.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .validation import nonnegative, positive, temperature_k

SIGMA_SB = 5.670374419e-8  # W m^-2 K^-4, CODATA


def radiation_net_w(emissivity: float, area_m2: float, t_k: float, t_amb_k: float) -> float:
    """Net radiative heat rejection of a grey body: eps*sigma*A*(T^4 - Tamb^4)."""
    from .validation import fraction

    eps = fraction("emissivity", emissivity)
    area = positive("area_m2", area_m2, "m^2")
    t = temperature_k("t_k", t_k)
    ta = temperature_k("t_amb_k", t_amb_k)
    return eps * SIGMA_SB * area * (t**4 - ta**4)


def radiation_required_area_m2(
    heat_w: float, emissivity: float, t_k: float, t_amb_k: float
) -> float:
    """Radiator area needed to reject heat_w by radiation alone."""
    heat = nonnegative("heat_w", heat_w, "W")
    if heat == 0:
        return 0.0
    per_area = radiation_net_w(emissivity, 1.0, t_k, t_amb_k)
    if per_area <= 0:
        raise ValueError("surface is not hotter than ambient; radiation cannot reject heat")
    return heat / per_area


def conduction_w(conductivity_w_mk: float, area_m2: float, thickness_m: float, dt_k: float) -> float:
    """Fourier conduction through a plane slab."""
    k = positive("conductivity_w_mk", conductivity_w_mk, "W/m/K")
    a = positive("area_m2", area_m2, "m^2")
    d = positive("thickness_m", thickness_m, "m")
    return k * a * dt_k / d


def thermal_resistance_conduction_k_w(
    conductivity_w_mk: float, area_m2: float, thickness_m: float
) -> float:
    k = positive("conductivity_w_mk", conductivity_w_mk, "W/m/K")
    a = positive("area_m2", area_m2, "m^2")
    d = positive("thickness_m", thickness_m, "m")
    return d / (k * a)


def convection_w(h_w_m2k: float, area_m2: float, dt_k: float) -> float:
    """Newton cooling. h is an effective coefficient, not a material property."""
    h = positive("h_w_m2k", h_w_m2k, "W/m^2/K")
    a = positive("area_m2", area_m2, "m^2")
    return h * a * dt_k


def required_convection_area_m2(heat_w: float, h_w_m2k: float, dt_k: float) -> float:
    h = positive("h_w_m2k", h_w_m2k, "W/m^2/K")
    if dt_k <= 0:
        raise ValueError("temperature difference must be > 0 K for convective rejection")
    return nonnegative("heat_w", heat_w, "W") / (h * dt_k)


@dataclass(frozen=True)
class LumpedThermal:
    """Single-node thermal mass: C dT/dt = Q - (T - Tamb)/R.

    Valid when Biot number is small (internal gradients negligible). The steady-state
    and step-response solutions are exact for constant Q and constant properties.
    """

    heat_capacity_j_k: float
    resistance_k_w: float
    ambient_k: float

    def __post_init__(self) -> None:
        positive("heat_capacity_j_k", self.heat_capacity_j_k, "J/K")
        positive("resistance_k_w", self.resistance_k_w, "K/W")
        temperature_k("ambient_k", self.ambient_k)

    @property
    def time_constant_s(self) -> float:
        return self.heat_capacity_j_k * self.resistance_k_w

    def steady_state_delta_t(self, heat_w: float) -> float:
        return nonnegative("heat_w", heat_w, "W") * self.resistance_k_w

    def step_response_k(self, heat_w: float, t_s: float) -> float:
        """Temperature at time t after a step of heat_w applied at t=0 (initial T=Tamb)."""
        q = nonnegative("heat_w", heat_w, "W")
        t = nonnegative("t_s", t_s, "s")
        dt_ss = q * self.resistance_k_w
        return self.ambient_k + dt_ss * (1.0 - math.exp(-t / self.time_constant_s))

    def settled_fraction(self, t_s: float) -> float:
        return 1.0 - math.exp(-nonnegative("t_s", t_s, "s") / self.time_constant_s)


def counterflow_effectiveness(ntu: float, capacity_ratio: float) -> float:
    """eps-NTU for a counterflow heat exchanger. capacity_ratio = C_min/C_max in [0,1]."""
    from .validation import fraction, in_range

    n = nonnegative("ntu", ntu, "-")
    cr = fraction("capacity_ratio", capacity_ratio)
    if n == 0:
        return 0.0
    if abs(cr - 1.0) < 1e-12:
        return n / (1.0 + n)
    exp_term = math.exp(-n * (1.0 - cr))
    return in_range("effectiveness", (1.0 - exp_term) / (1.0 - cr * exp_term), 0.0, 1.0, "-")


def heat_exchanger_duty_w(
    effectiveness: float, c_min_w_k: float, t_hot_in_k: float, t_cold_in_k: float
) -> float:
    from .validation import fraction

    eps = fraction("effectiveness", effectiveness)
    cmin = positive("c_min_w_k", c_min_w_k, "W/K")
    if t_hot_in_k <= t_cold_in_k:
        raise ValueError("hot inlet must be hotter than cold inlet")
    return eps * cmin * (t_hot_in_k - t_cold_in_k)


def pump_parasitic_w(volume_flow_m3_s: float, pressure_drop_pa: float, pump_efficiency: float) -> float:
    from .validation import fraction

    q = positive("volume_flow_m3_s", volume_flow_m3_s, "m^3/s")
    dp = positive("pressure_drop_pa", pressure_drop_pa, "Pa")
    eta = fraction("pump_efficiency", pump_efficiency)
    if eta == 0:
        raise ValueError("pump_efficiency must be > 0")
    return q * dp / eta


def thermal_stress_screening_pa(
    elastic_modulus_pa: float, cte_per_k: float, delta_t_k: float, poisson_ratio: float
) -> float:
    """Fully constrained thermal stress, sigma = E*alpha*dT/(1-nu).

    Screening only: it ignores plasticity, creep, and real constraint compliance, so it
    must not be read as a fatigue or lifetime prediction.
    """
    from .validation import fraction

    e = positive("elastic_modulus_pa", elastic_modulus_pa, "Pa")
    alpha = positive("cte_per_k", cte_per_k, "1/K")
    nu = fraction("poisson_ratio", poisson_ratio)
    if nu >= 0.5:
        raise ValueError("poisson_ratio must be < 0.5 for an isotropic solid")
    return e * alpha * delta_t_k / (1.0 - nu)
