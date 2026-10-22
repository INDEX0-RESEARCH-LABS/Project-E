# Project E — Status

**Cycle:** 2026-10-22 → 2026-10-23 (cycle 3, complete)
**Overall state:** comparison, sizing, requirement-feasibility, and an
independent model audit are complete; no hardware; no candidate meets all
targets.
**Plan:** [`docs/PLAN.md`](../docs/PLAN.md)
**Next actions:** [`reports/NEXT_ACTIONS.md`](NEXT_ACTIONS.md)

## Snapshot

| Item | State |
|---|---|
| Repository | `INDEX0-RESEARCH-LABS/Project-E`, branch `main` |
| Tests | 57 passing (`tests/test_core.py`, `tests/test_systems.py`) |
| Baseline run | `results/runs/20261022T195415Z_920ce114` |
| Conservative run | `results/runs/20261022T195436Z_fb0edc0a` |
| Optimistic run | `results/runs/20261022T195444Z_2d325f92` |
| Sensitivity | 2,000 draws, `reports/SENSITIVITY_ANALYSIS.md` |
| Sizing study | 84 grid points, `reports/SIZING_STUDY.md` |
| Mission scaling | `reports/MISSION_SCALING.md` |
| Literature | 12 DOI-verified records; abstracts only |
| Physical prototype | none; no measurement claimed |

## Baseline architecture scores

Mission: 1 kW continuous, 6 kW / 30 s pulses, 8 h. Targets: 35 kg, 60 L,
$5,000, $0.40/kWh.

| Key | Architecture | Mass kg | Volume L | Capex USD | LCOE $/kWh | Targets |
|---|---|---:|---:|---:|---:|---:|
| A1 | Battery only | 118.4 | 52.2 | 4,866 | 0.602 | 3/5 |
| A2 | Battery + supercap | 129.4 | 65.4 | 5,647 | 0.648 | 1/5 |
| B1 | Diesel, no buffer | 118.5 | 72.5 | 2,400 | 1.199 | 2/5 |
| B2 | TEG burner | 300.3 | 122.3 | 31,579 | 4.169 | 1/5 |
| B3 | TPV + thermal store | 256.9 | 144.0 | 2,453 | 0.301 | 3/5 |
| B4 | Fuel cell, no buffer | 102.9 | 64.7 | 23,053 | 1.753 | 1/5 |
| C1 | Fuel cell + battery | 56.5 | 31.7 | 6,583 | 0.871 | 2/5 |
| C2 | Diesel + battery | 50.3 | 21.3 | 1,149 | 0.668 | 3/5 |

## Scenario robustness

| Scenario | Best targets | Lightest | Cheapest per kWh |
|---|---:|---|---|
| Conservative | 3/5 (C2) | 84.7 kg (C1) | $0.510 (B3, 732 kg) |
| Baseline | 3/5 (A1, B3, C2) | 50.3 kg (C2) | $0.301 (B3, 257 kg) |
| Optimistic | 4/5 (A1, A2, C1) | 38.6 kg (C2) | $0.215 (B3, 146 kg) |

No candidate reaches 5/5 in any scenario.

## Monte Carlo (2,000 draws, cost drivers only)

| Key | P10 | P50 | P90 | P(cheapest) | P(≤$0.40) |
|---|---:|---:|---:|---:|---:|
| A1 | 0.472 | 0.688 | 1.080 | 12% | 3% |
| B3 | 0.236 | 0.468 | 0.714 | 83% | 38% |
| C2 | 0.590 | 0.801 | 1.008 | 5% | 0% |
| C1 | 0.764 | 1.165 | 1.798 | 0% | 0% |

The spread is wider than the difference between candidates. This is a bounded
what-if, not a forecast.

## Key thresholds

| To meet $0.40/kWh | Need | Assumed |
|---|---:|---:|
| A1 battery | ≤ $145.9/kWh | $300/kWh |
| C2 diesel | ≤ $0.732/L | $1.40/L |
| C1 fuel cell | unreachable (floor $0.492 with free H2) | $6/kg |
| A1 utilisation | ~520 missions/yr ($0.408 at 500) | 250/yr |
| A1 mass 35 kg | ~870 Wh/kg pack | 175 Wh/kg |

## The requirement set is the binding constraint

| Architecture | Mass at 0.5 h | Mass at 8 h | Binding term |
|---|---:|---:|---|
| A1 battery | 40.3 kg | 118.4 kg | 6 kW pulse pack + converter |
| C2 diesel hybrid | 44.8 kg | 50.3 kg | converter + genset + buffer + radiator |
| B1 genset | 111.3 kg | 118.5 kg | 6 kW genset |

A1 cannot reach 35 kg at **any** duration: 6 kW ÷ 300 W/kg = 21.1 kg of cells
before packaging, plus an 11.25 kg converter. C2's floor is 44.8 kg; even at a
2 kW peak it is 36.8 kg. Re-sizing the hybrid finds 50.3 kg at 1.1× source and
0.3 kWh buffer — still 15.3 kg over.

## Evidence level

- Model ranking: **E3** (internal consistency + analytic checks).
- Component parameters: **E0/E2** (estimates and datasheets, not measured).
- No **E4–E6** evidence exists.
- Full register: `validation/MODEL_VALIDATION_REGISTER.md`.
- Attacks and counters: `reports/RED_TEAM_REVIEW.md`.

## Decision

Retain the portable-hybrid branch as a **cost and integration** problem.
Do not buy hardware until:

1. a real use case fixes the duty cycle (G1), and
2. the peak/mass requirement is renegotiated or a modular pack is approved
   (G1b), and
3. quotations replace the E0 prices (G2), and
4. the bench test passes (`experiments/EXPERIMENT_PLAN.md`, G3).

## What changed in cycle 3

An independent audit found real defects. The ones that changed published
numbers were fixed and everything was rerun:

- C2 charged the converter twice; it now pays it once, in dispatch.
- B1 and C2 used different diesel part-load models; both now use the same curve,
  evaluated at their own load fraction. C2 efficiency fell from 28% to 24.7%.
- Battery capacity was sized on AC energy; it now includes the 95% output stage,
  +0.7 kWh and ~4 kg.
- Hybrid sizing now rejects a source rated at exactly average load, which cannot
  replace buffer losses over repeated missions. The baseline moved from 1.3×/0.5
  to the lightest sustainable point, 1.1×/0.3.
- Buffer replacement follows cycle throughput (≈3 cycles per mission), not one
  replacement per mission.
- TPV efficiency now passes a Carnot guard; config values are range-validated at
  the boundary; packaged volume is applied uniformly to every candidate, which
  drops B1 and B4 to 2/5 and 1/5.
- The sensitivity figure now plots signed deltas, not absolute values.
- Docs are stamped with the run they came from.
