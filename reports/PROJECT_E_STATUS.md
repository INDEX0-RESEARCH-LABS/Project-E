# Project E — Status

**Cycle:** 2026-10-22 (first execution cycle)
**Overall state:** models running, baseline + 2 scenarios complete, sensitivity in progress
**Full plan:** [`docs/PLAN.md`](../docs/PLAN.md)

## Snapshot

| Item | State |
|---|---|
| Repository | Created, git-initialized, no prior Project E work existed |
| Environment | Python 3.12 venv, numpy/scipy/pandas/matplotlib/pytest, 4 CPU, no GPU |
| Tests | 37 passing (analytical reference values + invariants) |
| Baseline run | `results/runs/20261022T180707Z_0dacea09` |
| Conservative run | `results/runs/20261022T180527Z_33ebb8da` |
| Optimistic run | `results/runs/20261022T180510Z_b69ccdcf` |
| Literature | 12 records verified by DOI; 5 abstracts retrieved; full texts not accessed |
| Physical prototype | None. No measurement is claimed. |

## Baseline architecture scores

Mission: 1 kW continuous, 6 kW / 30 s pulses, 8 h. Targets: 35 kg, 60 L,
$5,000, $0.40/kWh.

| Key | Architecture | Mass kg | Capex USD | LCOE $/kWh | Targets |
|---|---|---:|---:|---:|---:|
| A1 | Battery only | 101.9 | 4,647 | 0.583 | 3/5 |
| A2 | Battery + supercap | 110.2 | 5,407 | 0.628 | 2/5 |
| B1 | Diesel, no buffer | 118.5 | 2,400 | 1.199 | 3/5 |
| B2 | TEG burner | 274.2 | 30,000 | 3.960 | 1/5 |
| B3 | TPV + thermal store | 232.8 | 2,371 | 0.288 | 3/5 |
| B4 | Fuel cell, no buffer | 87.2 | 21,900 | 1.665 | 2/5 |
| C1 | Fuel cell + battery | 43.8 | 6,080 | 0.801 | 2/5 |
| C2 | Diesel + battery | 36.2 | 1,150 | 0.596 | 3/5 |

Scenario robustness:

| Scenario | Best targets met | Best mass | Best LCOE |
|---|---|---|---|
| Conservative | 3/5 (C2) | 71.3 kg (C1) | $0.49/kWh (B3, mass 682 kg) |
| Baseline | 3/5 (A1, B1, B3, C2) | 36.2 kg (C2) | $0.29/kWh (B3, mass 233 kg) |
| Optimistic | 5/5 (C1, C2) | 26.6 kg (C2) | $0.21/kWh (B3, mass 128 kg) |

## Evidence level of current claims

- Architecture ranking: **E3** (numerically verified model, analytic checks) —
  not experimentally validated.
- Component parameters: mixture of **E0/E2** estimates; see `provenance.csv` in
  each run folder.
- "No architecture meets all targets at baseline": **E2/E3** for this model and
  mission definition only.

## Next action

Run sensitivity analysis (one-at-a-time + cost Monte Carlo), then write the
requirements and architecture-comparison documents that lock the mission.
