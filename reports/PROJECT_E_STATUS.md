# Project E — Status

**Cycle:** 2026-10-22 → 2026-10-23 (cycle 1, complete)
**Overall state:** comparison and decision complete; no hardware; no candidate
meets all targets.
**Plan:** [`docs/PLAN.md`](../docs/PLAN.md)
**Next actions:** [`reports/NEXT_ACTIONS.md`](NEXT_ACTIONS.md)

## Snapshot

| Item | State |
|---|---|
| Repository | `INDEX0-RESEARCH-LABS/Project-E`, branch `main` |
| Tests | 51 passing (`tests/test_core.py`, `tests/test_systems.py`) |
| Baseline run | `results/runs/20261022T181859Z_9c00c799` |
| Conservative run | `results/runs/20261022T181904Z_2300c6ab` |
| Optimistic run | `results/runs/20261022T181913Z_df1cb11b` |
| Sensitivity | 2,000 draws, `reports/SENSITIVITY_ANALYSIS.md` |
| Literature | 12 DOI-verified records; abstracts only |
| Physical prototype | none; no measurement claimed |

## Baseline architecture scores

Mission: 1 kW continuous, 6 kW / 30 s pulses, 8 h. Targets: 35 kg, 60 L,
$5,000, $0.40/kWh.

| Key | Architecture | Mass kg | Volume L | Capex USD | LCOE $/kWh | Targets |
|---|---|---:|---:|---:|---:|---:|
| A1 | Battery only | 113.2 | 49.6 | 4,647 | 0.583 | 3/5 |
| A2 | Battery + supercap | 121.5 | 59.6 | 5,407 | 0.628 | 2/5 |
| B1 | Diesel, no buffer | 129.8 | 58.0 | 2,400 | 1.199 | 3/5 |
| B2 | TEG burner | 285.5 | 92.9 | 30,000 | 3.960 | 1/5 |
| B3 | TPV + thermal store | 244.1 | 136.8 | 2,371 | 0.288 | 3/5 |
| B4 | Fuel cell, no buffer | 98.4 | 51.0 | 21,900 | 1.665 | 2/5 |
| C1 | Fuel cell + battery | 55.0 | 24.2 | 6,080 | 0.801 | 2/5 |
| C2 | Diesel + battery | 47.5 | 15.3 | 1,150 | 0.596 | 3/5 |

## Scenario robustness

| Scenario | Best targets | Lightest | Cheapest per kWh |
|---|---:|---|---|
| Conservative | 3/5 (C2) | 81.7 kg (C1) | $0.488 (B3, 694 kg) |
| Baseline | 3/5 (A1, B1, B3, C2) | 47.5 kg (C2) | $0.288 (B3, 244 kg) |
| Optimistic | 4/5 (A1, A2, C1, C2) | 36.9 kg (C2) | $0.206 (B3, 139 kg) |

No candidate reaches 5/5 in any scenario.

## Monte Carlo (2,000 draws, cost drivers only)

| Key | P10 | P50 | P90 | P(cheapest) | P(≤$0.40) |
|---|---:|---:|---:|---:|---:|
| A1 | 0.467 | 0.677 | 1.079 | 9% | 3% |
| B3 | 0.227 | 0.447 | 0.682 | 82% | 41% |
| C2 | 0.527 | 0.714 | 0.897 | 9% | 0% |
| C1 | 0.703 | 1.072 | 1.643 | 0% | 0% |

The spread is wider than the difference between candidates. This is a bounded
what-if, not a forecast.

## Key thresholds

| To meet $0.40/kWh | Need | Assumed |
|---|---:|---:|
| A1 battery | ≤ $157/kWh | $300/kWh |
| C2 diesel | ≤ $0.85/L | $1.40/L |
| C1 fuel cell | unreachable (floor $0.441 with free H2) | $6/kg |
| A1 utilisation | ≥ 500 missions/yr | 250/yr |
| A1 mass 35 kg | ~825 Wh/kg pack | 175 Wh/kg |

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
2. quotations replace the E0 prices (G2), and
3. the bench test passes (`experiments/EXPERIMENT_PLAN.md`, G3).

## What changed in this cycle

- Added converter mass (1.5 kg/kW) uniformly — this removed the false optimistic
  pass and raised every mass by ~9–11 kg.
- Added supercapacitor volume, which made A2's volume 59.6 L (still just inside
  the limit) instead of 49.6 L.
- Regenerated all runs, sensitivity, and figures on the corrected model.
- Added 14 system regression tests.
