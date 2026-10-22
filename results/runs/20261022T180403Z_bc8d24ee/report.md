# Simulation report — 20261022T180403Z_bc8d24ee

- git commit: `uncommitted`
- config checksum: `bc8d24eebdf8ea8f…`
- runtime: 4.05 s
- mission: 1.0 kW base, 6.0 kW peak, 8.0 h

## Architecture results

| Key | Architecture | Delivered kWh | Efficiency | Mass kg | Capex USD | LCOE $/kWh | Targets met (of 5) |
|---|---|---:|---:|---:|---:|---:|---:|
| A1 | LiFePO4 battery only | 10.00 | 87.4% | 99.2 | 4,647 | 0.533 | 3 |
| A2 | LiFePO4 + supercapacitor pulse buffer | 10.00 | 87.4% | 107.5 | 5,407 | 0.579 | 2 |
| B1 | Diesel genset, no buffer (rated to peak) | 10.00 | 13.6% | 97.7 | 2,400 | 1.199 | 3 |
| B2 | Thermoelectric generator on a burner | 10.00 | 6.5% | 166.1 | 30,000 | 3.960 | 1 |
| B3 | TPV + high-temperature thermal store | 10.00 | 27.2% | 207.0 | 2,371 | 0.141 | 3 |
| B4 | PEM fuel cell, no buffer (rated to peak) | 10.00 | 50.0% | 82.5 | 21,900 | 1.665 | 2 |
| C1 | PEM fuel cell + small battery buffer | 10.00 | 49.8% | 39.1 | 6,080 | 0.796 | 2 |
| C2 | Diesel genset + small battery buffer | 10.00 | 27.9% | 27.7 | 1,150 | 0.592 | 4 |

## Targets

| Metric | Target |
|---|---:|
| Mass | ≤ 35.0 kg |
| Volume | ≤ 60.0 L |
| Capex | ≤ $5,000 |
| LCOE | ≤ $0.40/kWh |

All delivered-energy values are model outputs for the defined mission, not measured data.
Component parameters are parameterised estimates (see `provenance.csv`).

## Warnings

- Component parameters are estimates; no hardware was measured.
- Mass and cost are parametric estimates, not bills of materials.
- Diesel emissions and noise are not modeled.
