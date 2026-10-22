"""System-level regression tests: dispatch, economics, and architecture invariants.

These complement test_core.py. They check that the composed system keeps the
properties the model claims, not just the individual formulas.
"""

from __future__ import annotations

import pytest

from project_e.config import load_config
from project_e.economics import CostStreams
from project_e.models.storage import BatteryPack
from project_e.simulation.dispatch import Mission, simulate_hybrid
from project_e.simulation.runner import evaluate


def _mission() -> Mission:
    return Mission(
        duration_h=8.0,
        base_load_kw=1.0,
        peak_load_kw=6.0,
        pulse_duration_s=30.0,
        pulse_period_s=600.0,
    )


def _pack(capacity_kwh: float = 0.5) -> BatteryPack:
    return BatteryPack(
        capacity_kwh=capacity_kwh,
        round_trip_efficiency=0.92,
        soc_min=0.05,
        soc_max=0.95,
        p_charge_kw=2.0,
        p_discharge_kw=6.0,
        soc=0.6,
    )


# --- economics ---------------------------------------------------------------


def test_lcoe_without_discount_is_total_cost_over_total_energy():
    s = CostStreams(capex_usd=1000.0, annual_energy_kwh=100.0, lifetime_years=2, discount_rate=0.0)
    assert s.lcoe_usd_per_kwh == pytest.approx(5.0)


def test_replacement_is_charged_in_its_year():
    s = CostStreams(
        capex_usd=1000.0,
        annual_energy_kwh=100.0,
        replacements_usd={2: 500.0},
        lifetime_years=2,
        discount_rate=0.0,
    )
    assert s.lcoe_usd_per_kwh == pytest.approx(7.5)


def test_discounting_applies_to_both_cost_and_energy():
    # r = 100%: year-1 cost 100/2 = 50, year-1 energy 100/2 = 50.
    s = CostStreams(
        capex_usd=100.0,
        annual_energy_kwh=100.0,
        annual_om_usd=100.0,
        lifetime_years=1,
        discount_rate=1.0,
    )
    assert s.discounted() == pytest.approx((150.0, 50.0))
    assert s.lcoe_usd_per_kwh == pytest.approx(3.0)


def test_negative_capex_is_rejected():
    with pytest.raises(ValueError):
        CostStreams(capex_usd=-1.0, annual_energy_kwh=100.0)


# --- dispatch ----------------------------------------------------------------


def test_dispatch_is_timestep_convergent():
    coarse = simulate_hybrid(_mission(), 1.3, 0.28, _pack(), dt_s=2.0)
    fine = simulate_hybrid(_mission(), 1.3, 0.28, _pack(), dt_s=0.5)
    assert coarse.delivered_kwh == pytest.approx(fine.delivered_kwh, rel=1e-6)
    assert coarse.unmet_kwh <= 1e-6
    assert fine.unmet_kwh <= 1e-6
    assert fine.soc_min >= 0.05 - 1e-9
    assert fine.soc_max <= 0.95 + 1e-9


def test_undersized_buffer_reports_unmet_instead_of_hiding_it():
    sim = simulate_hybrid(_mission(), 1.3, 0.28, _pack(capacity_kwh=0.01), dt_s=2.0)
    assert sim.unmet_kwh > 0.0


@pytest.mark.parametrize("efficiency", [0.0, 1.2, -0.1])
def test_dispatch_rejects_invalid_source_efficiency(efficiency: float):
    with pytest.raises(ValueError):
        simulate_hybrid(_mission(), 1.3, efficiency, _pack())


# --- architecture invariants -------------------------------------------------


@pytest.fixture(scope="module")
def baseline():
    _, _, results, lcoe = evaluate(load_config("configs/baseline.yaml"))
    return {r.key: r for r in results}, lcoe


def test_supercapacitor_adds_mass_and_no_energy(baseline):
    results, _ = baseline
    assert results["A2"].mass_kg > results["A1"].mass_kg
    assert results["A2"].volume_l > results["A1"].volume_l
    assert results["A2"].delivered_kwh == pytest.approx(results["A1"].delivered_kwh)


def test_hybrid_is_lighter_than_generator_sized_to_peak(baseline):
    results, _ = baseline
    assert results["C2"].mass_kg < results["B1"].mass_kg
    assert results["C1"].mass_kg < results["B4"].mass_kg


def test_teg_is_worse_than_diesel_per_kwh(baseline):
    results, lcoe = baseline
    assert lcoe["B2"] > lcoe["B1"]
    assert results["B2"].mass_kg > results["B1"].mass_kg


def test_no_candidate_claims_over_unity_or_unmet_load(baseline):
    results, _ = baseline
    for r in results.values():
        assert 0.0 < r.efficiency <= 1.0, r.key
        assert abs(r.unmet_kwh) <= 1e-6, r.key
        assert r.energy_source, f"{r.key} has no declared source"


def test_no_candidate_meets_the_mass_target(baseline):
    results, _ = baseline
    assert all(r.mass_kg > 35.0 for r in results.values())
