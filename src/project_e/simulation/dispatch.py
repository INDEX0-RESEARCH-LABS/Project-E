"""Mission profiles and hybrid dispatch at the system boundary.

The dispatch simulation closes an energy balance every run. Any architecture that
cannot meet the load reports unmet energy rather than pretending the load was served.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..models.energy import EnergyAccount
from ..models.storage import BatteryPack
from ..models.validation import nonnegative, positive, require


@dataclass(frozen=True)
class Mission:
    """A repeating base load with rectangular power pulses."""

    duration_h: float
    base_load_kw: float
    peak_load_kw: float
    pulse_duration_s: float
    pulse_period_s: float

    def __post_init__(self) -> None:
        positive("duration_h", self.duration_h, "h")
        positive("base_load_kw", self.base_load_kw, "kW")
        positive("peak_load_kw", self.peak_load_kw, "kW")
        require(self.peak_load_kw >= self.base_load_kw, "peak load must be >= base load")
        positive("pulse_duration_s", self.pulse_duration_s, "s")
        positive("pulse_period_s", self.pulse_period_s, "s")
        require(self.pulse_duration_s <= self.pulse_period_s,
                "pulse duration cannot exceed its period")

    @property
    def pulse_extra_kw(self) -> float:
        return self.peak_load_kw - self.base_load_kw

    @property
    def pulse_energy_kwh(self) -> float:
        return self.pulse_extra_kw * self.pulse_duration_s / 3600.0

    @property
    def pulse_count(self) -> float:
        return self.duration_h * 3600.0 / self.pulse_period_s

    @property
    def energy_kwh(self) -> float:
        return self.base_load_kw * self.duration_h + self.pulse_energy_kwh * self.pulse_count

    def series(self, dt_s: float = 1.0):
        n = int(round(self.duration_h * 3600.0 / dt_s))
        t = np.arange(n + 1) * dt_s
        phase = np.mod(t, self.pulse_period_s)
        p = np.full_like(t, self.base_load_kw, dtype=float)
        p[phase < self.pulse_duration_s] = self.peak_load_kw
        # A pulse must not be truncated at the mission boundary; the series is closed at t=end.
        return t, p


@dataclass
class DispatchResult:
    delivered_kwh: float
    generated_kwh: float
    fuel_kwh: float
    unmet_kwh: float
    curtailed_kwh: float
    storage_loss_kwh: float
    soc_min: float
    soc_max: float
    account: EnergyAccount
    series: dict[str, np.ndarray] = field(default_factory=dict)

    @property
    def capacity_factor_ok(self) -> bool:
        return self.unmet_kwh <= 1e-9


def simulate_hybrid(
    mission: Mission,
    source_rated_kw: float,
    source_efficiency: float,
    battery: BatteryPack,
    dt_s: float = 1.0,
    soc_target: float = 0.60,
    control_time_constant_h: float = 0.5,
) -> DispatchResult:
    """Run a source + battery hybrid against the mission load.

    Controller: the source supplies the instantaneous load plus a proportional
    correction that drives SOC toward soc_target. The battery absorbs pulses.
    Source output is clipped to [0, rated]; unmet load is reported, never hidden.
    """
    positive("source_rated_kw", source_rated_kw, "kW")
    require(0 < source_efficiency <= 1, "source_efficiency must be in (0, 1]")
    require(0 < soc_target < 1, "soc_target must be in (0, 1)")
    positive("dt_s", dt_s, "s")

    t, load_series = mission.series(dt_s)
    load = load_series[:-1]  # one value per time step; last node closes the interval
    n = load.size
    p_source = np.zeros(n)
    p_batt = np.zeros(n)  # >0 discharge to load, <0 charge from source
    soc = np.zeros(n)
    unmet = np.zeros(n)
    curtailed = np.zeros(n)
    gen = 0.0
    stor_loss = 0.0
    deliv = 0.0

    gain_kw = battery.capacity_kwh / control_time_constant_h
    e_initial = battery.energy_available_kwh()
    for k in range(n):
        command = load[k] + gain_kw * (soc_target - battery.soc)
        p_src = float(np.clip(command, 0.0, source_rated_kw))
        p_source[k] = p_src
        net = p_src - load[k]  # >0 surplus, <0 deficit
        if net >= 0:
            r = battery.charge(net * dt_s / 3600.0, dt_s / 3600.0)
            stor_loss += r.loss_kwh
            curtailed[k] = r.clipped_kwh
            p_batt[k] = -r.energy_terminal_kwh * 3600.0 / dt_s
            served = load[k]
        else:
            r = battery.discharge(-net * dt_s / 3600.0, dt_s / 3600.0)
            stor_loss += r.loss_kwh
            p_batt[k] = r.energy_terminal_kwh * 3600.0 / dt_s
            served = min(load[k], p_src + p_batt[k])
            unmet[k] = max(load[k] - served, 0.0)
        deliv += served * dt_s / 3600.0
        gen += p_src * dt_s / 3600.0
        soc[k] = battery.soc

    fuel_in = gen / source_efficiency
    rejected_heat = fuel_in - gen
    e_stored_delta = battery.energy_available_kwh() - e_initial
    account = EnergyAccount(
        e_in_kwh=fuel_in,
        e_useful_kwh=deliv,
        e_loss_kwh=rejected_heat + stor_loss + float(np.sum(curtailed)),
        e_stored_delta_kwh=e_stored_delta,
        e_aux_kwh=0.0,
        tolerance_kwh=1e-6,
    )
    # Tolerance absorbs float accumulation across ~3e4 steps; closure is still asserted.
    account.check()

    return DispatchResult(
        delivered_kwh=deliv,
        generated_kwh=gen,
        fuel_kwh=fuel_in,
        unmet_kwh=float(np.sum(unmet) * dt_s / 3600.0),
        curtailed_kwh=float(np.sum(curtailed)),
        storage_loss_kwh=stor_loss,
        soc_min=float(soc.min()),
        soc_max=float(soc.max()),
        account=account,
        series={
            "t_s": t[:-1],
            "load_kw": load,
            "source_kw": p_source,
            "battery_kw": p_batt,
            "soc": soc,
            "unmet_kw": unmet,
        },
    )


def battery_only_energy(mission: Mission, battery_efficiency: float, charging_efficiency: float) -> float:
    """Grid/charging energy needed to deliver the mission from a battery alone."""
    require(0 < battery_efficiency <= 1, "battery_efficiency must be in (0, 1]")
    require(0 < charging_efficiency <= 1, "charging_efficiency must be in (0, 1]")
    return mission.energy_kwh / (battery_efficiency * charging_efficiency)
