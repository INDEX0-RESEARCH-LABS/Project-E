# Mission scaling — what the 35 kg target actually allows

All points use the baseline parameters; only duration or peak load changes.
Missions per year is held at 250, so a shorter mission delivers less annual
energy and its LCOE rises. That is deliberate: it compares cost per delivered
kWh at fixed utilisation, not at fixed operating hours.

## Mass and cost versus duration (1 kW base, 6 kW peak)

| Duration h | Energy kWh | A1 mass kg | A1 $/kWh | C2 mass kg | C2 $/kWh | B1 mass kg | B1 $/kWh |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 2.5 | 40.3 | 0.687 | 46.3 | 0.881 | 112.8 | 1.629 |
| 4 | 5.0 | 66.2 | 0.630 | 47.7 | 0.740 | 114.7 | 1.342 |
| 6 | 7.5 | 92.3 | 0.611 | 49.0 | 0.697 | 116.6 | 1.247 |
| 8 | 10.0 | 118.4 | 0.602 | 50.3 | 0.669 | 118.5 | 1.199 |
| 10 | 12.5 | 144.5 | 0.596 | 51.6 | 0.651 | 120.5 | 1.171 |
| 12 | 15.0 | 170.6 | 0.592 | 52.9 | 0.640 | 122.4 | 1.152 |

## Maximum mission length at the mass target (35 kg)

- **A1**: 40.3 kg at 0.5 h — 5.3 kg above target before useful mission energy is added. The floor is set by the 6 kW pulse (power-rated cells plus converter), not the 8 h duration.
- **B1**: 111.3 kg at 0.5 h — 76.3 kg above target before useful mission energy is added. The floor is set by the 6 kW genset, not the 8 h duration.
- **C2**: 44.8 kg at 0.5 h — 9.8 kg above target before useful mission energy is added. The floor is set by the 6 kW converter plus the minimum genset, buffer and radiator, not the 8 h duration.

For A1 the battery at 0.5 h is power-limited, not energy-limited: 6 kW ÷ 300 W/kg = 21.1 kg of cells before packaging, plus 11.2 kg of converter. That is the floor the requirement set has to live with.

## Peak load sweep (8 h, 1 kW base)

| Peak kW | Energy kWh | A1 mass kg | A1 $/kWh | C2 mass kg | C2 $/kWh |
|---:|---:|---:|---:|---:|---:|
| 2 | 8.4 | 93.7 | 0.584 | 36.8 | 0.639 |
| 3 | 8.8 | 99.9 | 0.589 | 40.2 | 0.647 |
| 4 | 9.2 | 106.1 | 0.594 | 43.6 | 0.655 |
| 6 | 10.0 | 118.4 | 0.602 | 50.3 | 0.669 |
| 8 | 10.8 | 130.7 | 0.608 | 57.1 | 0.674 |

## Interpretation

- The 35 kg, 6 kW, 8 h mission is not a design point any candidate reaches;
  it is a requirement set that is internally inconsistent for a battery and
  for a hydrocarbon hybrid.
- The peak-load sweep isolates the cost of the 6 kW pulse: converter and
  radiator scale with peak, while energy scales with duration.
- Reducing peak (staggered motor starts) or splitting the pack into modules
  are requirement-level changes, not hardware improvements.

These are model results. They do not replace the bench test.
