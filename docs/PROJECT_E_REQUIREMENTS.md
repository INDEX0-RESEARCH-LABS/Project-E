# Project E — Requirements

**Status:** locked for the current cycle
**Version:** 1.0 (2026-10-22)
**Supersedes:** none

This document fixes the mission and the acceptance criteria. Every architecture is
scored against this document and nothing else. Changing a number here invalidates
the comparison and requires a full rerun.

---

## 1. Purpose

Determine, with traceable evidence, whether a compact source-defined energy unit
can meet a defined portable off-grid mission better than a battery pack or a
diesel genset.

The unit must **not** claim net energy generation. Every joule delivered is
accounted to a declared source: stored charge, chemical fuel, or externally
supplied heat.

---

## 2. Mission profile

| Parameter | Value | Unit | Basis |
|---|---:|---|---|
| Mission duration | 8 | h | one working shift |
| Continuous load | 1.0 | kW | baseline equipment |
| Peak load | 6.0 | kW | motor/compressor start |
| Pulse duration | 30 | s | start transient |
| Pulse period | 600 | s | 10 min duty |
| Pulses per mission | 48 | — | 8 h / 10 min |
| Delivered energy | 10.0 | kWh | 8 × 1 kW; pulses draw from the same average |
| Operating ambient | 15–45 | °C | field range; 25 °C reference |

Derivation of delivered energy: base load contributes 1 kW × 8 h = 8.0 kWh.
Each pulse adds 5 kW for 30 s = 0.0417 kWh, and there are 48 pulses, adding
2.0 kWh. Total = 10.0 kWh. The dispatch model integrates the actual profile at
1 s and is verified at 2 s and 0.5 s. See `simulation/dispatch.py`.

---

## 3. Targets and rationale

| ID | Requirement | Target | Rationale | Verification |
|---|---|---:|---|---|
| PR-1 | System mass | ≤ 35 kg | two-person carry, ~17 kg each | model (mass build-up) |
| PR-2 | System volume | ≤ 60 L | vehicle footwell / two packs | model (volume build-up) |
| PR-3 | Capital cost | ≤ $5,000 | parity with genset + battery | model (capex build-up) |
| PR-4 | Levelized cost | ≤ $0.40/kWh | below remote diesel, above grid | model (discounted LCOE) |
| PR-5 | Service life | ≥ 10 a | amortisation horizon | model (replacement schedule) |
| PR-6 | Delivered energy | 10.0 kWh per mission | mission profile | model (dispatch) |
| PR-7 | Unmet energy | ≤ 0.001 kWh | no load shedding | model (dispatch assertion) |

These targets are **requirements, not demonstrated performance**. A target is
"met" only if the model value satisfies it; no target is claimed as measured.

---

## 4. Functional requirements

| ID | Requirement | Status in this cycle |
|---|---|---|
| FR-1 | Deliver 1 kW continuous for 8 h | modelled |
| FR-2 | Supply 6 kW for 30 s every 10 min | modelled |
| FR-3 | Declare one energy source per architecture | enforced by construction |
| FR-4 | Close the energy balance to ≤ 1e-9 relative | asserted in dispatch |
| FR-5 | Reject invalid inputs (negative, >100% efficiency, coolant ≤ ambient) | implemented and tested |
| FR-6 | Produce 230 V AC, 50 Hz output | **not modelled** |
| FR-7 | Start within 60 s of a cold request | **not modelled** |
| FR-8 | Report remaining energy and fault state | **not modelled** |
| FR-9 | Refuel or recharge within 10 min | **not modelled** |
| FR-10 | Operate at 15–45 °C ambient | partially modelled; 45 °C fails for LFP cooling |

Unmodelled functional requirements are listed here so they cannot be mistaken for
satisfied. They are candidates for the experiment plan, not for the model.

---

## 5. Constraints

| ID | Constraint | Consequence |
|---|---|---|
| C-1 | No architecture may have an undefined energy source | disqualification |
| C-2 | No net-energy or over-unity claim | disqualification |
| C-3 | Combustion units are disqualified indoors (CO, noise) | diesel branches are outdoor-only |
| C-4 | Hydrogen branch requires an external supply chain | availability dependency |
| C-5 | TPV branch requires ≥ 1500 °C external heat | co-location dependency |
| C-6 | All costs in USD, all energies in kWh, all masses in kg | unit consistency |
| C-7 | Raw data must remain separate from processed data | repository layout |
| C-8 | A model result is not a measurement | evidence labelling |

---

## 6. Assumptions that could invalidate the result

| ID | Assumption | Value | Evidence | If wrong |
|---|---|---:|---|---|
| A-1 | Missions per year | 250 | E0 | LCOE is highly sensitive; 500/yr is needed for battery parity |
| A-2 | Diesel delivered price | $1.40/L | E0 | Break-even for $0.40/kWh is $0.85/L |
| A-3 | Pack-level battery specific energy | 175 Wh/kg | E2 | ~870 Wh/kg would be needed for 35 kg; the 6 kW pulse also sets a ~40 kg floor |
| A-4 | Hydrogen delivered price | $6.00/kg | E0 | Free H2 still leaves the fuel-cell hybrid at $0.44/kWh |
| A-5 | Process heat price | $0.04/kWh | E0 | TPV stays under $0.40/kWh up to $0.070/kWh |
| A-6 | Discount rate | 8% real | E0 | ±4 points moves LCOE by ~$0.34/kWh |
| A-7 | Packaging factor | 1.25 | E1 | ±0.15 moves mass by several kg |
| A-8 | Converter mass | 1.5 kg/kW | E1 | this alone is ~11 kg at 6 kW |

Full ranges and sources: `configs/baseline.yaml`. Sensitivity:
`reports/SENSITIVITY_ANALYSIS.md`.

---

## 7. Acceptance criteria

A candidate passes the cycle only if **all** of the following hold:

1. PR-1 through PR-7 are satisfied at baseline, and
2. it remains within PR-1 through PR-4 under the conservative scenario, and
3. its energy source is declared and its energy balance closes, and
4. it does not violate constraints C-1 to C-5.

Current result: **no candidate passes.** The best baseline score is 3/5 targets
(A1, B1, B3, C2); the best conservative score is 3/5 (C2); the best optimistic
score is 4/5 (A1, A2, C1, C2). Details: `docs/ARCHITECTURE_COMPARISON.md`.

---

## 8. Out of scope

- Grid-tied operation, export, or revenue.
- Manufacturing design, certification, or regulatory approval.
- Indoor combustion operation.
- Hydrogen production or compression plant.
- Any claim of a physical prototype.
- Optimisation beyond the eight fixed candidates.

---

## 9. Change control

Any change to Sections 2, 3, or 5 requires:

1. a new version of this document,
2. a full rerun of `simulate` for baseline and both scenarios,
3. a regenerated sensitivity report,
4. an entry in `reports/NEXT_ACTIONS.md` explaining why the target moved.

Moving a target after seeing a result is goalpost-moving and must be recorded as
such, not silently applied.
