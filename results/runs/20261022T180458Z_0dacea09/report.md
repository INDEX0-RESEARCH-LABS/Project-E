# Simulation report — 20261022T180458Z_0dacea09

- git commit: `uncommitted`
- config checksum: `0dacea09737b005a…`
- runtime: 4.01 s
- mission: 1.0 kW base, 6.0 kW peak, 8.0 h

## Architecture results

| Key | Architecture | Delivered kWh | Efficiency | Mass kg | Capex USD | LCOE $/kWh | Targets met (of 5) |
|---|---|---:|---:|---:|---:|---:|---:|
| A1 | LiFePO4 battery only | 10.00 | 87.4% | 101.9 | 4,647 | 0.583 | 3 |
| A2 | LiFePO4 + supercapacitor pulse buffer | 10.00 | 87.4% | 110.2 | 5,407 | 0.628 | 2 |
| B1 | Diesel genset, no buffer (rated to peak) | 10.00 | 13.6% | 118.5 | 2,400 | 1.199 | 3 |
| B2 | Thermoelectric generator on a burner | 10.00 | 6.5% | 274.2 | 30,000 | 3.960 | 1 |
| B3 | TPV + high-temperature thermal store | 10.00 | 27.2% | 232.8 | 2,371 | 0.288 | 3 |
| B4 | PEM fuel cell, no buffer (rated to peak) | 10.00 | 50.0% | 87.2 | 21,900 | 1.665 | 2 |
| C1 | PEM fuel cell + small battery buffer | 10.00 | 49.8% | 43.8 | 6,080 | 0.801 | 2 |
| C2 | Diesel genset + small battery buffer | 10.00 | 27.9% | 36.2 | 1,150 | 0.596 | 3 |

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
