"""Storage models: Li-ion pack, supercapacitor, thermal store wrapper.

State of charge is always kept inside [soc_min, soc_max]; power and energy limits are
enforced by clipping and reported, never silently ignored.
"""

from __future__ import annotations

from dataclasses import dataclass

from .validation import fraction, nonnegative, positive, require

# One-way efficiency is sqrt(round-trip): charge and discharge losses are split equally.
# This is a modeling choice, stated here rather than buried in a literal.


@dataclass(frozen=True)
class FlowResult:
    """Result of one charge/discharge step, all energy in kWh at the terminals."""

    energy_terminal_kwh: float
    energy_internal_kwh: float
    loss_kwh: float
    clipped_kwh: float
    soc_after: float

    def __post_init__(self) -> None:
        nonnegative("energy_terminal_kwh", self.energy_terminal_kwh)
        nonnegative("energy_internal_kwh", self.energy_internal_kwh)
        nonnegative("loss_kwh", self.loss_kwh)
        nonnegative("clipped_kwh", self.clipped_kwh)
        fraction("soc_after", self.soc_after)


@dataclass
class BatteryPack:
    capacity_kwh: float
    round_trip_efficiency: float
    soc_min: float = 0.05
    soc_max: float = 0.95
    p_charge_kw: float = 3.0
    p_discharge_kw: float = 5.0
    self_discharge_per_day: float = 0.0005
    soc: float = 0.5

    def __post_init__(self) -> None:
        positive("capacity_kwh", self.capacity_kwh, "kWh")
        fraction("round_trip_efficiency", self.round_trip_efficiency)
        require(self.round_trip_efficiency > 0, "round_trip_efficiency must be > 0")
        fraction("soc_min", self.soc_min)
        fraction("soc_max", self.soc_max)
        require(self.soc_max > self.soc_min, "soc_max must exceed soc_min")
        positive("p_charge_kw", self.p_charge_kw, "kW")
        positive("p_discharge_kw", self.p_discharge_kw, "kW")
        fraction("self_discharge_per_day", self.self_discharge_per_day)
        fraction("soc", self.soc)
        self.soc = min(max(self.soc, self.soc_min), self.soc_max)

    @property
    def usable_kwh(self) -> float:
        return self.capacity_kwh * (self.soc_max - self.soc_min)

    @property
    def one_way_efficiency(self) -> float:
        return self.round_trip_efficiency**0.5

    def energy_available_kwh(self) -> float:
        return (self.soc - self.soc_min) * self.capacity_kwh

    def headroom_kwh(self) -> float:
        return (self.soc_max - self.soc) * self.capacity_kwh

    def rest_hours(self, hours: float) -> None:
        """Apply self-discharge over a rest interval."""
        h = nonnegative("hours", hours, "h")
        self.soc -= self.soc * self.self_discharge_per_day * h / 24.0
        self.soc = max(self.soc, self.soc_min)

    def charge(self, energy_kwh: float, hours: float) -> FlowResult:
        """Draw energy_kwh at the terminals; store what fits."""
        requested = nonnegative("energy_kwh", energy_kwh, "kWh")
        h = positive("hours", hours, "h")
        clip = 0.0
        limited = min(requested, self.p_charge_kw * h)
        clip += requested - limited
        eta = self.one_way_efficiency
        storable = limited * eta
        headroom = self.headroom_kwh()
        stored = min(storable, headroom)
        if stored < storable:
            clip += (storable - stored) / eta
        self.soc += stored / self.capacity_kwh
        self.soc = min(self.soc, self.soc_max)
        return FlowResult(
            energy_terminal_kwh=stored / eta,
            energy_internal_kwh=stored,
            loss_kwh=stored / eta - stored,
            clipped_kwh=max(clip, 0.0),
            soc_after=self.soc,
        )

    def discharge(self, energy_kwh: float, hours: float) -> FlowResult:
        """Deliver energy_kwh at the terminals; draw more than that from the cells."""
        requested = nonnegative("energy_kwh", energy_kwh, "kWh")
        h = positive("hours", hours, "h")
        limit_by_power = self.p_discharge_kw * h
        available = self.energy_available_kwh() * self.one_way_efficiency
        deliverable = min(requested, limit_by_power, available)
        clip = requested - deliverable
        eta = self.one_way_efficiency
        internal = deliverable / eta
        self.soc -= internal / self.capacity_kwh
        self.soc = max(self.soc, self.soc_min)
        return FlowResult(
            energy_terminal_kwh=deliverable,
            energy_internal_kwh=internal,
            loss_kwh=internal - deliverable,
            clipped_kwh=max(clip, 0.0),
            soc_after=self.soc,
        )

    def capacity_after_degradation(
        self, cycles: float, years: float, mean_temp_c: float = 25.0, cycle_life: float = 3000.0
    ) -> float:
        """Remaining capacity fraction, linear fade to 80% at cycle_life.

        Assumed model with explicit parameters; not a validated lifetime prediction.
        Temperature acceleration doubles fade per 10 K above 25 C, capped at 4x.
        """
        nonnegative("cycles", cycles, "-")
        nonnegative("years", years, "a")
        positive("cycle_life", cycle_life, "cycles")
        require(-20 <= mean_temp_c <= 80, "mean_temp_c outside credible operating range")
        temp_factor = min(2.0 ** (max(mean_temp_c - 25.0, 0.0) / 10.0), 4.0)
        cycle_fade = 0.20 * cycles / cycle_life * temp_factor
        calendar_fade = 0.01 * years * temp_factor  # 1%/a at 25 C, assumed
        return max(1.0 - cycle_fade - calendar_fade, 0.0)


@dataclass(frozen=True)
class Supercapacitor:
    """Symmetric supercapacitor bank. Usable energy above the minimum voltage."""

    capacitance_f: float
    v_max: float
    v_min: float
    esr_ohm: float
    self_discharge_per_day: float = 0.05

    def __post_init__(self) -> None:
        positive("capacitance_f", self.capacitance_f, "F")
        positive("v_max", self.v_max, "V")
        positive("v_min", self.v_min, "V")
        require(self.v_max > self.v_min, "v_max must exceed v_min")
        nonnegative("esr_ohm", self.esr_ohm, "ohm")
        fraction("self_discharge_per_day", self.self_discharge_per_day)

    @property
    def usable_energy_kwh(self) -> float:
        return 0.5 * self.capacitance_f * (self.v_max**2 - self.v_min**2) / 3.6e6

    def discharge_efficiency(self, power_kw: float) -> float:
        """Efficiency at constant power, small-loss approximation I = P/V_mean.

        Approximate (ignores the voltage swing during discharge); adequate for
        screening, not for converter design.
        """
        p = positive("power_kw", power_kw, "kW")
        if self.esr_ohm == 0:
            return 1.0
        v_mean = 0.5 * (self.v_max + self.v_min)
        loss_kw = (p * 1000.0 / v_mean) ** 2 * self.esr_ohm / 1000.0
        eta = 1.0 - loss_kw / p
        require(eta > 0, f"requested power exceeds short-circuit capability (eta={eta:.3f})")
        return fraction("supercapacitor efficiency", eta)
