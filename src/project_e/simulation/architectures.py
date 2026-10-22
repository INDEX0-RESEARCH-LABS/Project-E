"""Architecture candidates: sizing, mass, cost, and thermal-rejection screening.

Three classes are kept separate:
  A  storage        -- energy supplied during charging, recovered on demand
  B  generation     -- a named source continuously converts fuel/heat to electricity
  C  hybrid         -- generation plus a buffer that carries transients

Every result states its energy source. Nothing here generates energy without one.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np

from ..models import conversion, thermal
from ..models.storage import BatteryPack
from ..models.validation import positive, require
from .dispatch import Mission, simulate_hybrid


@dataclass(frozen=True)
class ArchResult:
    key: str
    name: str
    architecture_class: str
    energy_source: str
    delivered_kwh: float
    input_kwh: float
    efficiency: float
    mass_kg: float
    volume_l: float
    capex_usd: float
    waste_heat_kw: float
    radiator_area_m2: float
    unmet_kwh: float
    fuel_units: float
    fuel_unit: str
    fuel_cost_usd: float
    annual_om_usd: float
    coolant_fraction: float = 1.0
    coolant_c: float = 65.0
    capex_items: dict[str, float] = field(default_factory=dict)
    fuel_driver: str = ""
    replacements_usd: dict[int, float] = field(default_factory=dict)
    notes: tuple[str, ...] = ()
    evidence: str = "E1/E3"


def _radiator_area(waste_heat_kw: float, coolant_c: float, ambient_c: float, h: float) -> float:
    if waste_heat_kw <= 0:
        return 0.0
    dt = coolant_c - ambient_c
    if dt <= 0:
        raise ValueError("coolant must be hotter than ambient to reject heat")
    return waste_heat_kw * 1000.0 / (h * dt)


def _m(component_kg: float, packaging: float) -> float:
    return component_kg * packaging


def _replacement_schedule(cycles_per_year: float, p: dict, cost_usd: float) -> dict[int, float]:
    """Replace a pack each time cumulative throughput reaches its cycle life.

    The fade model is 20% loss at cycle_life plus 1%/a calendar fade, taken to the
    80% end-of-life threshold. Repeat the interval for the whole project life: one
    replacement is not enough for a heavily cycled buffer.
    """
    b = p["battery"]
    decay_per_year = 0.20 * cycles_per_year / b["cycle_life"] + 0.01
    interval = max(1, int(0.20 / decay_per_year + 0.9999))
    out: dict[int, float] = {}
    year = interval
    while year <= p["assumptions"]["lifetime_years"]:
        out[year] = cost_usd
        year += interval
    return out


def battery_only(mission: Mission, p: dict) -> ArchResult:
    b = p["battery"]
    packaging = p["assumptions"]["packaging_factor"]
    conv = p["assumptions"]["converter_efficiency"]
    eol = p["assumptions"]["degradation_margin"]
    soc_window = b["soc_max"] - b["soc_min"]
    # The pack sits behind the output converter: it must supply E/conv, not E.
    usable_eol = mission.energy_kwh / conv / (1.0 - eol)
    capacity = usable_eol / soc_window
    mass_cells = max(
        capacity * 1000.0 / b["specific_energy_wh_kg"],
        mission.peak_load_kw / p["assumptions"]["converter_efficiency"] * 1000.0
        / b["specific_power_w_kg"],
    )
    volume = capacity * 1000.0 / b["energy_density_wh_l"]
    capex = capacity * b["cost_usd_per_kwh"] + mission.peak_load_kw * b["power_electronics_usd_per_kw"]
    charge_eff = (
        b["round_trip_efficiency"]
        * p["assumptions"]["charger_efficiency"]
        * p["assumptions"]["converter_efficiency"]
    )
    # Cycles per year from actual throughput, not one mission = one cycle.
    cycles_per_year = (
        p["assumptions"]["missions_per_year"] * (mission.energy_kwh / conv) / (capacity * soc_window)
    )
    replacements = _replacement_schedule(cycles_per_year, p, capacity * b["cost_usd_per_kwh"])
    input_kwh = mission.energy_kwh / charge_eff
    # Only discharge-side losses are rejected onboard; charger loss is off-board.
    dc_discharge = mission.energy_kwh / conv
    waste = dc_discharge * (1.0 / b["round_trip_efficiency"] - 1.0) + mission.energy_kwh * (1.0 / conv - 1.0)
    return ArchResult(
        key="A1",
        name="LiFePO4 battery only",
        architecture_class="A storage",
        energy_source="grid/electric charging before mission",
        delivered_kwh=mission.energy_kwh,
        input_kwh=input_kwh,
        efficiency=charge_eff,
        mass_kg=_m(mass_cells, packaging),
        volume_l=volume,
        capex_usd=capex,
        capex_items={
            "battery": capacity * b["cost_usd_per_kwh"],
            "power_electronics": mission.peak_load_kw * b["power_electronics_usd_per_kw"],
        },
        fuel_driver="electricity",
        waste_heat_kw=waste / mission.duration_h,
        radiator_area_m2=_radiator_area(
            waste / mission.duration_h,
            p["assumptions"]["battery_coolant_c"],
            p["assumptions"]["ambient_c"],
            p["assumptions"]["h_convection_w_m2k"],
        ),
        unmet_kwh=0.0,
        fuel_units=0.0,
        fuel_unit="",
        fuel_cost_usd=input_kwh * p["assumptions"]["electricity_usd_per_kwh"],
        annual_om_usd=0.0,
        replacements_usd=replacements,
        coolant_fraction=1.0,
        coolant_c=p["assumptions"]["battery_coolant_c"],
        notes=(
            f"sized for end-of-life capacity with {eol:.0%} degradation margin",
            "battery supplies both energy and 6 kW pulses",
        ),
        evidence="E2/E3 (sizing model); component parameters are ESTIMATES",
    )


def battery_supercap(mission: Mission, p: dict) -> ArchResult:
    """Same energy, plus a capacitor bank: demonstrates that capacitors do not add energy."""
    base = battery_only(mission, p)
    sc = p["supercap"]
    cap_kwh = (
        mission.pulse_energy_kwh
        * p["assumptions"]["pulse_cap_margin"]
        / p["assumptions"]["converter_efficiency"]
    )
    cap_mass = cap_kwh * 1000.0 / sc["specific_energy_wh_kg"]
    converter_kw = mission.peak_load_kw
    extra_capex = cap_kwh * sc["cost_usd_per_kwh"] + converter_kw * sc["converter_usd_per_kw"]
    return replace(
        base,
        key="A2",
        name="LiFePO4 + supercapacitor pulse buffer",
        mass_kg=base.mass_kg + _m(cap_mass, p["assumptions"]["packaging_factor"]),
        volume_l=base.volume_l + cap_kwh * 1000.0 / sc["energy_density_wh_l"],
        capex_usd=base.capex_usd + extra_capex,
        capex_items={
            **base.capex_items,
            "supercap": cap_kwh * sc["cost_usd_per_kwh"],
            "power_electronics": base.capex_items.get("power_electronics", 0.0)
            + converter_kw * sc["converter_usd_per_kw"],
        },
        notes=base.notes
        + (
            "capacitor covers one 30 s pulse on top of a 6 kW-rated pack",
            "heavier and costlier than A1 for this mission; a power-optimised pack "
            "would be a different architecture, not this control",
        ),
    )


def diesel_direct(mission: Mission, p: dict) -> ArchResult:
    d = p["diesel"]
    eta_avg = d["efficiency_lhv"] * (
        d["part_load_floor"] + (1.0 - d["part_load_floor"]) * mission.energy_kwh / mission.duration_h / mission.peak_load_kw
    )
    fuel_kwh = mission.energy_kwh / eta_avg
    litres = fuel_kwh / conversion.LHV_DIESEL_KWH_PER_L
    mass = mission.peak_load_kw * d["mass_kg_per_kw"] + litres * d["fuel_density_kg_per_l"]
    waste = fuel_kwh - mission.energy_kwh
    return ArchResult(
        key="B1",
        name="Diesel genset, no buffer (rated to peak)",
        architecture_class="B generation",
        energy_source="diesel fuel",
        delivered_kwh=mission.energy_kwh,
        input_kwh=fuel_kwh,
        efficiency=mission.energy_kwh / fuel_kwh,
        mass_kg=_m(mass, p["assumptions"]["packaging_factor"]),
        volume_l=litres * 1.35 + mission.peak_load_kw * 8.0,
        capex_usd=mission.peak_load_kw * d["cost_usd_per_kw"],
        capex_items={"generator": mission.peak_load_kw * d["cost_usd_per_kw"]},
        fuel_driver="diesel",
        waste_heat_kw=waste / mission.duration_h,
        radiator_area_m2=_radiator_area(
            waste / mission.duration_h, p["assumptions"]["coolant_c"],
            p["assumptions"]["ambient_c"], p["assumptions"]["h_convection_w_m2k"]),
        unmet_kwh=0.0,
        fuel_units=litres,
        fuel_unit="L",
        fuel_cost_usd=litres * d["fuel_usd_per_l"],
        annual_om_usd=d["maintenance_usd_per_kwh"] * mission.energy_kwh * p["assumptions"]["missions_per_year"],
        coolant_fraction=0.35,
        notes=("genset sized to peak load, so most operating time is at low part load",
               "part-load efficiency model is an ESTIMATE"),
    )


def teg_generator(mission: Mission, p: dict) -> ArchResult:
    t = p["teg"]
    eta = conversion.teg_efficiency(
        t["hot_c"] + 273.15, t["cold_c"] + 273.15, t["zt"]) * p["assumptions"]["converter_efficiency"]
    fuel_kwh = mission.energy_kwh / (eta * t["burner_efficiency"])
    if t["fuel"] != "diesel":
        raise ValueError(f"B2: unsupported fuel {t['fuel']!r}; only diesel has a cost path")
    litres = fuel_kwh / conversion.LHV_DIESEL_KWH_PER_L
    peak_dc_kw = mission.peak_load_kw / p["assumptions"]["converter_efficiency"]
    mass = peak_dc_kw * t["mass_kg_per_kw"] + litres * p["diesel"]["fuel_density_kg_per_l"]
    waste = fuel_kwh - mission.energy_kwh
    return ArchResult(
        key="B2",
        name="Thermoelectric generator on a burner",
        architecture_class="B generation",
        energy_source="combustion heat -> TEG",
        delivered_kwh=mission.energy_kwh,
        input_kwh=fuel_kwh,
        efficiency=mission.energy_kwh / fuel_kwh,
        mass_kg=_m(mass, p["assumptions"]["packaging_factor"]),
        volume_l=peak_dc_kw * 12.0 + litres * 1.35,
        capex_usd=peak_dc_kw * 1000.0 * t["cost_usd_per_w"],
        capex_items={"teg": peak_dc_kw * 1000.0 * t["cost_usd_per_w"]},
        fuel_driver="diesel",
        waste_heat_kw=waste / mission.duration_h,
        radiator_area_m2=_radiator_area(
            waste / mission.duration_h, t["cold_c"],
            p["assumptions"]["ambient_c"], p["assumptions"]["h_convection_w_m2k"]),
        unmet_kwh=0.0,
        fuel_units=litres,
        fuel_unit="L",
        fuel_cost_usd=litres * p["diesel"]["fuel_usd_per_l"],
        annual_om_usd=0.0,
        coolant_fraction=0.5,
        coolant_c=t["cold_c"],
        notes=(f"TEG efficiency {eta:.1%} from ZT={t['zt']} at {t['hot_c']}/{t['cold_c']} C",
               "heat rejection dominates the design at kW scale"),
    )


def tpv_storage(mission: Mission, p: dict) -> ArchResult:
    v = p["tpv"]
    packaging = p["assumptions"]["packaging_factor"]
    # Carnot guard: reject a cell efficiency that is not physically possible at
    # the declared emitter/cell temperatures before it inflates B3.
    cell_eta = conversion.tpv_efficiency(
        v["emitter_c"] + 273.15, v["cold_c"] + 273.15, v["efficiency"]
    )
    eta = cell_eta * v["spectral_quality"] * p["assumptions"]["converter_efficiency"]
    thermal_kwh = mission.energy_kwh / eta
    store_mass = thermal_kwh / v["storage_specific_kwh_per_kg"] * (1.0 + v["vessel_mass_fraction"])
    area_m2 = mission.peak_load_kw / p["assumptions"]["converter_efficiency"] * 1000.0 / v["power_density_w_cm2"] / 10000.0
    cell_mass = area_m2 * v["cell_mass_kg_per_m2"]
    waste = thermal_kwh - mission.energy_kwh
    capex = (
        area_m2 * v["cell_cost_usd_per_m2"]
        + store_mass * v["storage_cost_usd_per_kg"]
        + v["emitter_cost_usd"]
    )
    return ArchResult(
        key="B3",
        name="TPV + high-temperature thermal store",
        architecture_class="B generation (stored heat)",
        energy_source="external heat >=1500 C charging the thermal store",
        delivered_kwh=mission.energy_kwh,
        input_kwh=thermal_kwh,
        efficiency=eta,
        mass_kg=_m(store_mass + cell_mass, packaging),
        volume_l=store_mass / v["storage_density_kg_per_l"],
        capex_usd=capex,
        capex_items={
            "tpv_cells": area_m2 * v["cell_cost_usd_per_m2"],
            "thermal_storage": store_mass * v["storage_cost_usd_per_kg"],
            "emitter": v["emitter_cost_usd"],
        },
        fuel_driver="heat",
        waste_heat_kw=waste / mission.duration_h,
        radiator_area_m2=_radiator_area(
            waste / mission.duration_h, v["cold_c"],
            p["assumptions"]["ambient_c"], p["assumptions"]["h_convection_w_m2k"]),
        unmet_kwh=0.0,
        fuel_units=0.0,
        fuel_unit="",
        fuel_cost_usd=thermal_kwh * p["assumptions"]["heat_usd_per_kwh"],
        annual_om_usd=0.0,
        coolant_fraction=0.9,
        coolant_c=v["cold_c"],
        notes=("energy source must supply >1500 C heat; heat is priced as an input",
               "storage mass is the binding constraint, not cell efficiency"),
    )


def fuel_cell_direct(mission: Mission, p: dict) -> ArchResult:
    f = p["fuel_cell"]
    eta = f["efficiency_lhv"] * p["assumptions"]["converter_efficiency"]
    h2_kg = mission.energy_kwh / (eta * conversion.LHV_H2_KWH_PER_KG)
    tank_mass = h2_kg / f["tank_gravimetric_fraction"]
    peak_dc_kw = mission.peak_load_kw / p["assumptions"]["converter_efficiency"]
    mass = peak_dc_kw * f["mass_kg_per_kw"] + tank_mass + f["balance_of_plant_kg"]
    fuel_kwh = mission.energy_kwh / eta
    waste = fuel_kwh - mission.energy_kwh
    return ArchResult(
        key="B4",
        name="PEM fuel cell, no buffer (rated to peak)",
        architecture_class="B generation",
        energy_source="compressed hydrogen",
        delivered_kwh=mission.energy_kwh,
        input_kwh=fuel_kwh,
        efficiency=eta,
        mass_kg=_m(mass, p["assumptions"]["packaging_factor"]),
        volume_l=mission.peak_load_kw * 6.0 + h2_kg * f["tank_l_per_kg_h2"],
        capex_usd=peak_dc_kw * f["cost_usd_per_kw"] + h2_kg * f["tank_cost_usd_per_kg_h2"],
        capex_items={
            "fuel_cell": peak_dc_kw * f["cost_usd_per_kw"],
            "h2_tank": h2_kg * f["tank_cost_usd_per_kg_h2"],
        },
        fuel_driver="h2",
        waste_heat_kw=waste / mission.duration_h,
        radiator_area_m2=_radiator_area(
            waste / mission.duration_h, p["assumptions"]["coolant_c"],
            p["assumptions"]["ambient_c"], p["assumptions"]["h_convection_w_m2k"]),
        unmet_kwh=0.0,
        fuel_units=h2_kg,
        fuel_unit="kg H2",
        fuel_cost_usd=h2_kg * f["h2_usd_per_kg"],
        annual_om_usd=0.0,
        coolant_fraction=0.5,
        notes=("sized to peak power, so the stack is oversized for average load",
               "tank mass assumes 5 wt% system gravimetric fraction"),
    )


def _hybrid(
    mission: Mission,
    p: dict,
    key: str,
    name: str,
    source_kw: float,
    source_eta: float,
    buffer_kwh: float,
    mass_kg: float,
    volume_l: float,
    capex_usd: float,
    fuel_units_per_mission: float,
    fuel_unit: str,
    fuel_cost_usd: float,
    annual_om_usd: float,
    notes: tuple[str, ...],
    replacements: dict[int, float] | None = None,
    source: str = "",
    coolant_c: float | None = None,
    coolant_fraction: float = 1.0,
    capex_items: dict[str, float] | None = None,
    fuel_driver: str = "",
) -> ArchResult:
    battery = BatteryPack(
        capacity_kwh=buffer_kwh,
        round_trip_efficiency=p["battery"]["round_trip_efficiency"],
        soc_min=p["battery"]["soc_min"],
        soc_max=p["battery"]["soc_max"],
        p_charge_kw=max(source_kw * 1.5, 1.0),
        p_discharge_kw=mission.peak_load_kw / p["assumptions"]["converter_efficiency"],
        soc=0.6,
    )
    sim = simulate_hybrid(
        mission,
        source_kw,
        source_eta,
        battery,
        dt_s=p["assumptions"]["dt_s"],
        converter_efficiency=p["assumptions"]["converter_efficiency"],
    )
    require(sim.unmet_kwh <= 1e-6,
            f"{key}: unmet {sim.unmet_kwh:.4f} kWh — source rating, buffer size or "
            "controller lag; inspect the dispatch series")
    # Cyclic sustainability: the source must be able to cover the DC load *and*
    # replace the buffer's round-trip losses. A source rated at exactly average
    # load serves one mission by draining the buffer, then fails on the next.
    # Use the authoritative average, not the curtailed energy a particular
    # controller happened to use.
    avg_dc_kw = mission.energy_kwh / mission.duration_h / p["assumptions"]["converter_efficiency"]
    loss_kw = sim.storage_loss_kwh / mission.duration_h
    require(source_kw >= avg_dc_kw + loss_kw - 1e-6,
            f"{key}: source {source_kw:.3f} kW cannot sustain DC load {avg_dc_kw:.3f} kW "
            f"plus buffer loss {loss_kw:.3f} kW; this point relies on stored energy")
    waste = sim.fuel_kwh - sim.delivered_kwh
    dt_h = p["assumptions"]["dt_s"] / 3600.0
    throughput = float(np.sum(np.maximum(sim.series["battery_dc_kw"], 0.0))) * dt_h
    usable = buffer_kwh * (p["battery"]["soc_max"] - p["battery"]["soc_min"])
    cycles_per_year = p["assumptions"]["missions_per_year"] * throughput / usable
    pack_replacements = _replacement_schedule(
        cycles_per_year, p, buffer_kwh * p["battery"]["cost_usd_per_kwh"]
    )
    return ArchResult(
        key=key,
        name=name,
        architecture_class="C hybrid",
        energy_source=source,
        delivered_kwh=sim.delivered_kwh,
        input_kwh=sim.fuel_kwh,
        efficiency=sim.delivered_kwh / sim.fuel_kwh,
        mass_kg=_m(mass_kg, p["assumptions"]["packaging_factor"]),
        volume_l=volume_l,
        capex_usd=capex_usd,
        capex_items=capex_items or {},
        fuel_driver=fuel_driver,
        waste_heat_kw=waste / mission.duration_h,
        radiator_area_m2=_radiator_area(
            waste / mission.duration_h,
            coolant_c if coolant_c is not None else p["assumptions"]["coolant_c"],
            p["assumptions"]["ambient_c"],
            p["assumptions"]["h_convection_w_m2k"]),
        unmet_kwh=sim.unmet_kwh,
        fuel_units=fuel_units_per_mission,
        fuel_unit=fuel_unit,
        fuel_cost_usd=fuel_cost_usd,
        annual_om_usd=annual_om_usd,
        replacements_usd={**(replacements or {}), **pack_replacements},
        coolant_fraction=coolant_fraction,
        notes=notes + (f"dispatch: SOC {sim.soc_min:.2f}-{sim.soc_max:.2f}, unmet {sim.unmet_kwh:.2e} kWh",),
    )


def fuel_cell_hybrid(mission: Mission, p: dict) -> ArchResult:
    f = p["fuel_cell"]
    conv = p["assumptions"]["converter_efficiency"]
    avg_dc_kw = mission.energy_kwh / mission.duration_h / conv
    source_kw = avg_dc_kw * f["source_sizing_factor"]
    buffer_kwh = max(
        f["buffer_kwh"],
        mission.pulse_energy_kwh / conv / (p["battery"]["soc_max"] - p["battery"]["soc_min"]) * 1.2,
    )
    h2_kg = mission.energy_kwh / (
        f["efficiency_lhv"] * p["assumptions"]["converter_efficiency"] * conversion.LHV_H2_KWH_PER_KG
    )
    tank_mass = h2_kg / f["tank_gravimetric_fraction"]
    mass = (
        source_kw * f["mass_kg_per_kw"]
        + f["balance_of_plant_kg"]
        + tank_mass
        + buffer_kwh * 1000.0 / p["battery"]["specific_energy_wh_kg"]
    )
    capex = (
        source_kw * f["cost_usd_per_kw"]
        + buffer_kwh * p["battery"]["cost_usd_per_kwh"]
        + h2_kg * f["tank_cost_usd_per_kg_h2"]
        + mission.peak_load_kw * p["battery"]["power_electronics_usd_per_kw"]
    )
    return _hybrid(
        mission, p, "C1", "PEM fuel cell + small battery buffer",
        source_kw, f["efficiency_lhv"], buffer_kwh,
        mass_kg=mass,
        volume_l=source_kw * 6.0 + h2_kg * f["tank_l_per_kg_h2"] + buffer_kwh * 1000.0 / p["battery"]["energy_density_wh_l"],
        capex_usd=capex,
        fuel_units_per_mission=h2_kg,
        fuel_unit="kg H2",
        fuel_cost_usd=h2_kg * f["h2_usd_per_kg"],
        annual_om_usd=0.0,
        capex_items={
            "fuel_cell": source_kw * f["cost_usd_per_kw"],
            "battery": buffer_kwh * p["battery"]["cost_usd_per_kwh"],
            "h2_tank": h2_kg * f["tank_cost_usd_per_kg_h2"],
            "power_electronics": mission.peak_load_kw * p["battery"]["power_electronics_usd_per_kw"],
        },
        fuel_driver="h2",
        replacements={5: source_kw * f["cost_usd_per_kw"] * 0.4},
        coolant_fraction=0.5,
        notes=("stack sized for average load; battery carries 6 kW pulses",
               "hydrogen supply chain is an external dependency"),
        source="compressed hydrogen",
    )


def diesel_hybrid(mission: Mission, p: dict) -> ArchResult:
    d = p["diesel"]
    conv = p["assumptions"]["converter_efficiency"]
    avg_dc_kw = mission.energy_kwh / mission.duration_h / conv
    source_kw = avg_dc_kw * d["source_sizing_factor"]
    # Physical floor only: enough buffer to cover one pulse across the SOC window.
    buffer_kwh = max(
        d["buffer_kwh"],
        mission.pulse_energy_kwh / conv / (p["battery"]["soc_max"] - p["battery"]["soc_min"]) * 1.2,
    )
    # One diesel model: part-load efficiency at the source's actual average
    # fraction, same curve as B1. Converter loss is charged once, in dispatch.
    load_fraction = avg_dc_kw / source_kw
    eta = d["efficiency_lhv"] * (
        d["part_load_floor"] + (1.0 - d["part_load_floor"]) * load_fraction
    )
    fuel_kwh = mission.energy_kwh / (eta * conv)
    litres = fuel_kwh / conversion.LHV_DIESEL_KWH_PER_L
    mass = (
        source_kw * d["mass_kg_per_kw"]
        + buffer_kwh * 1000.0 / p["battery"]["specific_energy_wh_kg"]
        + litres * d["fuel_density_kg_per_l"] * 1.25
    )
    capex = (
        source_kw * d["cost_usd_per_kw"]
        + buffer_kwh * p["battery"]["cost_usd_per_kwh"]
        + mission.peak_load_kw * p["battery"]["power_electronics_usd_per_kw"]
    )
    return _hybrid(
        mission, p, "C2", "Diesel genset + small battery buffer",
        source_kw, eta, buffer_kwh,
        mass_kg=mass,
        volume_l=source_kw * 8.0 + litres * 1.35,
        capex_usd=capex,
        fuel_units_per_mission=litres,
        fuel_unit="L",
        fuel_cost_usd=litres * d["fuel_usd_per_l"],
        annual_om_usd=d["maintenance_usd_per_kwh"] * mission.energy_kwh * p["assumptions"]["missions_per_year"],
        capex_items={
            "generator": source_kw * d["cost_usd_per_kw"],
            "battery": buffer_kwh * p["battery"]["cost_usd_per_kwh"],
            "power_electronics": mission.peak_load_kw * p["battery"]["power_electronics_usd_per_kw"],
        },
        fuel_driver="diesel",
        notes=("small genset runs near its efficient point; battery carries pulses",
               "combustion emissions and noise are not modeled but are disqualifying indoors"),
        source="diesel fuel",
        coolant_c=p["assumptions"]["coolant_c"],
        coolant_fraction=0.35,
    )


def screen_architecture(r: ArchResult, mission: Mission, p: dict) -> ArchResult:
    """Apply the common thermal, converter-mass, and validity screening.

    Every candidate goes through this, so no architecture can hide its radiator
    or its power electronics.
    """
    a = p["assumptions"]
    positive("delivered_kwh", r.delivered_kwh, "kWh")
    require(r.efficiency <= 1.0 + 1e-9, f"{r.key}: efficiency above 1 without a heat pump")
    require(0 <= r.coolant_fraction <= 1, f"{r.key}: coolant_fraction outside [0,1]")
    # The coolant-side fraction of waste heat needs a real surface area.
    dt = r.coolant_c - a["ambient_c"]
    if r.waste_heat_kw > 0 and dt <= 0:
        raise ValueError(
            f"{r.key}: coolant ({r.coolant_c} C) must exceed ambient ({a['ambient_c']} C)"
        )
    area = 0.0 if dt <= 0 else r.waste_heat_kw * 1000.0 * r.coolant_fraction / (a["h_convection_w_m2k"] * dt)
    radiator_mass = area * a["radiator_kg_per_m2"]
    # Every candidate needs power conversion; its mass is easy to forget and material
    # at a 35 kg target, so it is charged to all architectures at peak throughput.
    # B1 is a native-AC genset: its alternator is inside efficiency_lhv, so it does
    # not carry a separate inverter.
    converter_mass = 0.0 if r.key == "B1" else _m(
        mission.peak_load_kw * a["power_electronics_kg_per_kw"], a["packaging_factor"]
    )
    # Apply the packaging factor to volume here, once, for every candidate. Some
    # architectures used to pre-multiply it and others did not, which made the
    # 60 L comparison apples-to-oranges.
    return replace(
        r,
        radiator_area_m2=area,
        mass_kg=r.mass_kg + radiator_mass + converter_mass,
        volume_l=r.volume_l * a["packaging_factor"],
    )


def all_architectures(mission: Mission, p: dict) -> list[ArchResult]:
    results = [
        battery_only(mission, p),
        battery_supercap(mission, p),
        diesel_direct(mission, p),
        teg_generator(mission, p),
        tpv_storage(mission, p),
        fuel_cell_direct(mission, p),
        fuel_cell_hybrid(mission, p),
        diesel_hybrid(mission, p),
    ]
    return [screen_architecture(r, mission, p) for r in results]
