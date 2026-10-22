"""Input validation shared by all Project E models.

Every physical quantity carries a unit string. Invalid or nonsensical values raise
ValueError with the offending quantity named -- models must never silently accept
negative absolute temperatures or efficiencies above one.
"""

from __future__ import annotations

import math


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def positive(name: str, value: float, unit: str = "") -> float:
    require(isinstance(value, (int, float)) and not isinstance(value, bool),
            f"{name} must be a real number, got {value!r}")
    require(math.isfinite(value), f"{name} must be finite, got {value}")
    require(value > 0, f"{name} must be > 0 {unit}, got {value} {unit}")
    return float(value)


def nonnegative(name: str, value: float, unit: str = "") -> float:
    require(isinstance(value, (int, float)) and not isinstance(value, bool),
            f"{name} must be a real number, got {value!r}")
    require(math.isfinite(value), f"{name} must be finite, got {value}")
    require(value >= 0, f"{name} must be >= 0 {unit}, got {value} {unit}")
    return float(value)


def in_range(name: str, value: float, lo: float, hi: float, unit: str = "") -> float:
    require(isinstance(value, (int, float)) and not isinstance(value, bool),
            f"{name} must be a real number, got {value!r}")
    require(math.isfinite(value), f"{name} must be finite, got {value}")
    require(lo <= value <= hi,
            f"{name} must be in [{lo}, {hi}] {unit}, got {value} {unit}")
    return float(value)


def fraction(name: str, value: float) -> float:
    """Dimensionless efficiency/fraction in [0, 1]."""
    return in_range(name, value, 0.0, 1.0, "-")


def temperature_k(name: str, value: float) -> float:
    """Absolute temperature in kelvin. Guards against Celsius/kelvin confusion."""
    require(isinstance(value, (int, float)) and not isinstance(value, bool),
            f"{name} must be a real number, got {value!r}")
    require(math.isfinite(value), f"{name} must be finite, got {value}")
    require(value > 0, f"{name} must be > 0 K (absolute temperature, not Celsius), got {value}")
    require(value <= 5000, f"{name} = {value} K is outside this model's credible range (<5000 K)")
    return float(value)


def celsius_to_kelvin(celsius: float, name: str = "temperature") -> float:
    require(math.isfinite(celsius), f"{name} must be finite, got {celsius}")
    return temperature_k(name, celsius + 273.15)


def combine_relative(*relative_uncertainties: float) -> float:
    """Quadrature sum of independent relative standard uncertainties."""
    for u in relative_uncertainties:
        nonnegative("relative uncertainty", u, "-")
    return math.sqrt(sum(u * u for u in relative_uncertainties))


def propagate_ratio(num: float, num_rel: float, den: float, den_rel: float) -> tuple[float, float]:
    """Ratio y = num/den with independent relative uncertainties -> (y, relative u)."""
    positive("numerator", num)
    positive("denominator", den)
    return num / den, combine_relative(num_rel, den_rel)
