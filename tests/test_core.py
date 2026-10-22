"""Analytical and invariant tests for the core physics models.

Each test encodes a hand-calculable reference value or a physical invariant, so a
failure indicates a modeling error, not merely a changed number.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from project_e.models import conversion, energy, storage, thermal, validation


def test_carnot_reference_value():
    assert conversion.carnot_efficiency(800.0, 300.0) == pytest.approx(0.625)


def test_carnot_rejects_inverted_reservoirs():
    with pytest.raises(ValueError, match="hotter"):
        conversion.carnot_efficiency(300.0, 800.0)


def test_teg_efficiency_matches_hand_calculation():
    # Th=500, Tc=300, ZT=1: eta_C=0.4; (sqrt2-1)/(sqrt2+0.6)=0.2056453 -> 0.08225812
    eta = conversion.teg_efficiency(500.0, 300.0, 1.0)
    assert eta == pytest.approx(0.08225812, rel=1e-6)


def test_teg_zero_zt_has_zero_efficiency():
    assert conversion.teg_efficiency(600.0, 300.0, 0.0) == pytest.approx(0.0)


def test_teg_efficiency_below_carnot():
    eta = conversion.teg_efficiency(1000.0, 300.0, 3.0)
    assert 0 < eta < conversion.carnot_efficiency(1000.0, 300.0)


def test_tpv_efficiency_rejects_carnot_violation():
    with pytest.raises(ValueError, match="Carnot"):
        conversion.tpv_efficiency(800.0, 300.0, 0.7)


def test_pv_temperature_derating():
    eta = conversion.pv_efficiency(0.22, -0.0035, 65.0)
    assert eta == pytest.approx(0.22 * (1 - 0.0035 * 40), rel=1e-12)


def test_pv_rejects_positive_temperature_coefficient():
    with pytest.raises(ValueError, match="temperature coefficient"):
        conversion.pv_efficiency(0.22, 0.0035, 25.0)


def test_radiation_matches_stefan_boltzmann():
    p = thermal.radiation_net_w(1.0, 1.0, 600.0, 300.0)
    expected = 5.670374419e-8 * (600.0**4 - 300.0**4)
    assert p == pytest.approx(expected, rel=1e-12)
    assert p == pytest.approx(6889.5049, rel=1e-5)


def test_radiation_is_zero_at_thermal_equilibrium():
    assert thermal.radiation_net_w(0.9, 2.0, 350.0, 350.0) == pytest.approx(0.0, abs=1e-9)


def test_radiation_rejects_celsius_as_kelvin():
    with pytest.raises(ValueError, match="absolute temperature"):
        thermal.radiation_net_w(0.9, 1.0, 0.0, 300.0)


def test_required_radiator_area_inverts_radiation():
    area = thermal.radiation_required_area_m2(1000.0, 0.9, 700.0, 300.0)
    assert thermal.radiation_net_w(0.9, area, 700.0, 300.0) == pytest.approx(1000.0)


def test_conduction_slab():
    assert thermal.conduction_w(1.0, 1.0, 1.0, 1.0) == pytest.approx(1.0)


def test_lumped_steady_state_and_time_constant():
    node = thermal.LumpedThermal(heat_capacity_j_k=1000.0, resistance_k_w=1.0, ambient_k=300.0)
    assert node.time_constant_s == pytest.approx(1000.0)
    assert node.steady_state_delta_t(100.0) == pytest.approx(100.0)
    assert node.step_response_k(100.0, 1000.0) == pytest.approx(300.0 + 100.0 * (1 - math.exp(-1)))


def test_lumped_step_starts_at_ambient():
    node = thermal.LumpedThermal(500.0, 2.0, 290.0)
    assert node.step_response_k(50.0, 0.0) == pytest.approx(290.0)


def test_counterflow_effectiveness_limits():
    assert thermal.counterflow_effectiveness(2.0, 0.0) == pytest.approx(1 - math.exp(-2))
    assert thermal.counterflow_effectiveness(2.0, 1.0) == pytest.approx(2 / 3)
    assert thermal.counterflow_effectiveness(0.0, 0.5) == 0.0


def test_pump_parasitic_power():
    assert thermal.pump_parasitic_w(1e-3, 1e4, 0.5) == pytest.approx(20.0)


def test_integrate_power_one_kilowatt_hour():
    t = np.array([0.0, 3600.0])
    p = np.array([1000.0, 1000.0])
    assert energy.integrate_power(t, p) == pytest.approx(1.0)


def test_integrate_power_rejects_non_monotonic_time():
    with pytest.raises(ValueError, match="increase"):
        energy.integrate_power(np.array([0.0, 1.0, 0.5]), np.array([1.0, 1.0, 1.0]))


def test_energy_balance_closes_and_reports_efficiency():
    acc = energy.energy_balance(e_in_kwh=10.0, e_useful_kwh=8.0, e_aux_kwh=0.5,
                               e_stored_delta_kwh=1.0)
    assert acc.is_balanced
    assert acc.e_loss_kwh == pytest.approx(1.0)
    assert acc.efficiency == pytest.approx(0.8)


def test_energy_balance_detects_hidden_source():
    with pytest.raises(ValueError, match="hidden energy source"):
        energy.energy_balance(e_in_kwh=1.0, e_useful_kwh=2.0, e_aux_kwh=0.0,
                              e_stored_delta_kwh=0.0)


def test_energy_balance_detects_aux_exceeding_losses():
    with pytest.raises(ValueError, match="subset"):
        energy.EnergyAccount(e_in_kwh=10.0, e_useful_kwh=9.0, e_loss_kwh=1.0,
                             e_stored_delta_kwh=0.0, e_aux_kwh=2.0)


def test_energy_account_residual_exceeds_tolerance():
    acc = energy.EnergyAccount(1.0, 0.5, 0.4, 0.0, tolerance_kwh=1e-6)
    assert not acc.is_balanced
    with pytest.raises(ValueError, match="balance violated"):
        acc.check()


def test_battery_round_trip_matches_specification():
    pack = storage.BatteryPack(capacity_kwh=10.0, round_trip_efficiency=0.81,
                               soc_min=0.05, soc_max=0.95, p_charge_kw=10.0,
                               p_discharge_kw=10.0, soc=0.5)
    charged = pack.charge(4.0, hours=1.0)
    assert charged.energy_terminal_kwh == pytest.approx(4.0)
    assert pack.soc == pytest.approx(0.5 + 3.6 / 10.0)
    discharged = pack.discharge(3.24, hours=1.0)
    assert discharged.energy_terminal_kwh == pytest.approx(3.24)
    assert discharged.energy_terminal_kwh / charged.energy_terminal_kwh == pytest.approx(0.81)


def test_battery_respects_soc_and_power_limits():
    pack = storage.BatteryPack(capacity_kwh=1.0, round_trip_efficiency=0.9,
                               soc_min=0.1, soc_max=0.9, p_charge_kw=0.2,
                               p_discharge_kw=0.3, soc=0.5)
    r = pack.charge(5.0, hours=1.0)
    assert r.energy_terminal_kwh == pytest.approx(0.2)
    assert r.clipped_kwh == pytest.approx(4.8)
    assert pack.soc <= 0.9
    r2 = pack.discharge(5.0, hours=1.0)
    assert r2.energy_terminal_kwh == pytest.approx(0.3)
    assert pack.soc >= 0.1
    for _ in range(200):
        pack.charge(0.05, 1.0)
        pack.discharge(0.05, 1.0)
        assert pack.soc_min - 1e-12 <= pack.soc <= pack.soc_max + 1e-12


def test_battery_self_discharge_is_small_and_monotonic():
    pack = storage.BatteryPack(capacity_kwh=10.0, round_trip_efficiency=0.9, soc=0.8)
    before = pack.soc
    pack.rest_hours(24.0)
    assert 0.79 < pack.soc < before


def test_battery_degradation_reference_points():
    pack = storage.BatteryPack(capacity_kwh=10.0, round_trip_efficiency=0.9)
    assert pack.capacity_after_degradation(0, 0) == pytest.approx(1.0)
    assert pack.capacity_after_degradation(3000, 0) == pytest.approx(0.8)
    hotter = pack.capacity_after_degradation(3000, 0, mean_temp_c=45.0)
    assert hotter < 0.8


def test_supercapacitor_usable_energy_hand_calculation():
    cap = storage.Supercapacitor(capacitance_f=3000.0, v_max=48.0, v_min=24.0, esr_ohm=0.01)
    assert cap.usable_energy_kwh == pytest.approx(0.72)


def test_supercapacitor_efficiency_falls_with_power():
    cap = storage.Supercapacitor(3000.0, 48.0, 24.0, esr_ohm=0.01)
    assert cap.discharge_efficiency(1.0) > cap.discharge_efficiency(5.0)
    with pytest.raises(ValueError, match="short-circuit"):
        cap.discharge_efficiency(500.0)


def test_sensible_store_capacity_hand_calculation():
    store = conversion.SensibleHeatStore(100.0, 1000.0, 300.0, 1000.0, insulation_ua_w_k=5.0)
    assert store.capacity_kwh == pytest.approx(19.4444, rel=1e-4)
    assert store.standby_loss_kwh(300.0, 10.0) == pytest.approx(5.0 * 350.0 * 10 / 1000.0)


def test_fuel_consumption_diesel_reference():
    # 1 kW electrical at 30% LHV: 1/(0.3*9.94) = 0.335 L/h
    assert conversion.fuel_consumption(1.0, 0.30, conversion.LHV_DIESEL_KWH_PER_L) == pytest.approx(
        0.33535, rel=1e-4
    )


@pytest.mark.parametrize("bad", [-1.0, 0.0, float("nan"), float("inf")])
def test_temperature_validation_rejects_invalid(bad):
    with pytest.raises(ValueError):
        validation.temperature_k("T", bad)


def test_fraction_rejects_out_of_range():
    with pytest.raises(ValueError, match="efficiency"):
        validation.fraction("efficiency", 1.2)
    with pytest.raises(ValueError):
        validation.fraction("efficiency", -0.1)


def test_combine_relative_uncertainty_quadrature():
    assert validation.combine_relative(0.03, 0.04) == pytest.approx(0.05)
