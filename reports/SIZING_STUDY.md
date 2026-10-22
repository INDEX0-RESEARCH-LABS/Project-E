# Sizing study — hybrid source and buffer

Grid: source sizing factor 0.9–1.5 × average load, buffer 0.3–1.0 kWh.
A point is feasible only if dispatch serves the whole mission (unmet ≤ 1e-6 kWh)
and the source can sustain the DC load plus the buffer's round-trip loss over
repeated missions. A source at exactly average load fails the second test.
C1 is the fuel-cell hybrid; C2 the diesel hybrid. All other parameters at baseline.

## C2

- feasible points: 30 / 42
- infeasible: 12 (source below sustainable load, unmet pulse, or rejected configuration; per-point reason in the CSV)
- lightest feasible: 50.3 kg at 1.1× source, 0.3 kWh buffer, $0.669/kWh, 3/5 targets
- cheapest feasible: $0.669/kWh at 1.1× source, 0.3 kWh buffer, 50.3 kg, 3/5 targets

### Pareto front (mass vs LCOE)

| Source × | Buffer kWh | Mass kg | LCOE $/kWh | Capex USD | Targets |
|---:|---:|---:|---:|---:|---:|
| 1.1 | 0.3 | 50.3 | 0.669 | 1,149 | 3/5 |

Best target score over the grid: **3/5** at 1.1× source and 0.3 kWh buffer.

Even the lightest feasible point is 15.3 kg above the mass target. Re-sizing the hybrid cannot close that gap.

## C1

- feasible points: 30 / 42
- infeasible: 12 (source below sustainable load, unmet pulse, or rejected configuration; per-point reason in the CSV)
- lightest feasible: 56.5 kg at 1.1× source, 0.3 kWh buffer, $0.871/kWh, 2/5 targets
- cheapest feasible: $0.804/kWh at 1.1× source, 1.0 kWh buffer, 61.5 kg, 2/5 targets

### Pareto front (mass vs LCOE)

| Source × | Buffer kWh | Mass kg | LCOE $/kWh | Capex USD | Targets |
|---:|---:|---:|---:|---:|---:|
| 1.1 | 0.3 | 56.5 | 0.871 | 6,583 | 2/5 |
| 1.1 | 1.0 | 61.5 | 0.804 | 6,793 | 2/5 |

Best target score over the grid: **2/5** at 1.1× source and 0.3 kWh buffer.

Even the lightest feasible point is 21.5 kg above the mass target. Re-sizing the hybrid cannot close that gap.

