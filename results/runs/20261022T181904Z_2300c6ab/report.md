# Simulation report — 20261022T181904Z_2300c6ab

- git commit: `e16192937bd1a0acc659954f7f749eb1387f9a0b`
- config checksum: `2300c6ab5d9b21d0…`
- runtime: 4.14 s
- mission: 1.0 kW base, 6.0 kW peak, 8.0 h

## Architecture results

| Key | Architecture | Delivered kWh | Efficiency | Mass kg | Capex USD | LCOE $/kWh | Targets met (of 5) |
|---|---|---:|---:|---:|---:|---:|---:|
| A1 | LiFePO4 battery only | 10.00 | 83.6% | 200.8 | 7,623 | 1.193 | 1 |
| A2 | LiFePO4 + supercapacitor pulse buffer | 10.00 | 83.6% | 209.1 | 8,383 | 1.250 | 1 |
| B1 | Diesel genset, no buffer (rated to peak) | 10.00 | 10.7% | 212.2 | 2,400 | 2.301 | 2 |
| B2 | Thermoelectric generator on a burner | 10.00 | 3.9% | 1140.8 | 72,000 | 11.075 | 1 |
| B3 | TPV + high-temperature thermal store | 10.00 | 17.0% | 694.2 | 3,388 | 0.488 | 2 |
| B4 | PEM fuel cell, no buffer (rated to peak) | 10.00 | 42.0% | 128.9 | 38,143 | 3.699 | 2 |
| C1 | PEM fuel cell + small battery buffer | 10.00 | 41.5% | 81.7 | 10,648 | 1.817 | 2 |
| C2 | Diesel genset + small battery buffer | 10.00 | 21.7% | 83.9 | 1,225 | 1.156 | 3 |

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
