"""Energy accounting for a defined control volume and time interval.

    E_in = E_useful + E_loss + dE_stored

All quantities are kWh in this module. Auxiliary consumption is tracked separately
but is a *subset* of E_loss -- adding it twice would break the balance.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .validation import fraction, nonnegative, positive, require


def integrate_power(t_s: np.ndarray, p_w: np.ndarray) -> float:
    """Integrate a power time series (W) over time (s) -> energy in kWh."""
    t = np.asarray(t_s, dtype=float)
    p = np.asarray(p_w, dtype=float)
    require(t.ndim == 1 and p.ndim == 1, "t_s and p_w must be 1-D")
    require(t.size == p.size and t.size >= 2, "t_s and p_w must be equal length >= 2")
    require(np.all(np.isfinite(t)) and np.all(np.isfinite(p)), "non-finite value in series")
    dt = np.diff(t)
    require(np.all(dt > 0), "time must increase strictly")
    if np.any(p < 0):
        raise ValueError("integrate_power expects non-negative power; split import/export first")
    return float(np.trapezoid(p, t) / 3.6e6)


@dataclass(frozen=True)
class EnergyAccount:
    """Closed energy balance for one interval.

    Attributes
    ----------
    e_in_kwh : energy entering the control volume.
    e_useful_kwh : energy delivered to the load.
    e_loss_kwh : all dissipation, including auxiliary consumption.
    e_stored_delta_kwh : stored energy at end minus start (may be negative).
    e_aux_kwh : auxiliary/parasitic consumption, a subset of e_loss_kwh.
    tolerance_kwh : permitted closure residual (numerical + measurement).
    """

    e_in_kwh: float
    e_useful_kwh: float
    e_loss_kwh: float
    e_stored_delta_kwh: float
    e_aux_kwh: float = 0.0
    tolerance_kwh: float = 1e-9
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        positive("e_in_kwh", self.e_in_kwh)
        nonnegative("e_useful_kwh", self.e_useful_kwh)
        nonnegative("e_loss_kwh", self.e_loss_kwh)
        nonnegative("e_aux_kwh", self.e_aux_kwh)
        nonnegative("tolerance_kwh", self.tolerance_kwh)
        require(self.e_aux_kwh <= self.e_loss_kwh + self.tolerance_kwh,
                "auxiliary energy must be a subset of total losses")
        require(self.e_useful_kwh <= self.e_in_kwh + self.tolerance_kwh,
                "useful output cannot exceed input for a passive control volume")

    @property
    def residual_kwh(self) -> float:
        return self.e_in_kwh - (self.e_useful_kwh + self.e_loss_kwh + self.e_stored_delta_kwh)

    @property
    def is_balanced(self) -> bool:
        return abs(self.residual_kwh) <= self.tolerance_kwh

    @property
    def efficiency(self) -> float:
        """Delivered useful energy per unit input energy."""
        return fraction("efficiency", self.e_useful_kwh / self.e_in_kwh)

    def check(self) -> "EnergyAccount":
        if not self.is_balanced:
            raise ValueError(
                f"energy balance violated: residual {self.residual_kwh:.6g} kWh "
                f"exceeds tolerance {self.tolerance_kwh:.6g} kWh"
            )
        return self


def energy_balance(
    e_in_kwh: float,
    e_useful_kwh: float,
    e_aux_kwh: float,
    e_stored_delta_kwh: float,
    tolerance_kwh: float = 1e-9,
) -> EnergyAccount:
    """Close the balance by treating everything unaccounted for as loss."""
    nonnegative("e_in_kwh", e_in_kwh)
    loss = e_in_kwh - e_useful_kwh - e_stored_delta_kwh
    if loss < -tolerance_kwh:
        raise ValueError(
            "useful + stored change exceeds input; a hidden energy source or sign error "
            f"is present (loss would be {loss:.6g} kWh)"
        )
    return EnergyAccount(
        e_in_kwh=e_in_kwh,
        e_useful_kwh=e_useful_kwh,
        e_loss_kwh=max(loss, 0.0),
        e_stored_delta_kwh=e_stored_delta_kwh,
        e_aux_kwh=e_aux_kwh,
        tolerance_kwh=tolerance_kwh,
    ).check()
