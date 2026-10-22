# Simulation report — 20261022T180510Z_b69ccdcf

- git commit: `uncommitted`
- config checksum: `b69ccdcf570aa225…`
- runtime: 2.78 s
- mission: 1.0 kW base, 6.0 kW peak, 8.0 h

## Architecture results

| Key | Architecture | Delivered kWh | Efficiency | Mass kg | Capex USD | LCOE $/kWh | Targets met (of 5) |
|---|---|---:|---:|---:|---:|---:|---:|
| A1 | LiFePO4 battery only | 10.00 | 90.2% | 71.5 | 2,702 | 0.263 | 4 |
| A2 | LiFePO4 + supercapacitor pulse buffer | 10.00 | 90.2% | 79.9 | 3,462 | 0.296 | 4 |
| B1 | Diesel genset, no buffer (rated to peak) | 10.00 | 16.0% | 94.3 | 2,400 | 0.740 | 3 |
| B2 | Thermoelectric generator on a burner | 10.00 | 8.1% | 174.3 | 12,000 | 1.758 | 1 |
| B3 | TPV + high-temperature thermal store | 10.00 | 34.0% | 128.3 | 2,075 | 0.206 | 3 |
| B4 | PEM fuel cell, no buffer (rated to peak) | 10.00 | 58.0% | 75.1 | 11,214 | 0.633 | 2 |
| C1 | PEM fuel cell + small battery buffer | 10.00 | 58.1% | 34.7 | 3,324 | 0.326 | 5 |
| C2 | Diesel genset + small battery buffer | 10.00 | 33.1% | 26.6 | 1,090 | 0.364 | 5 |

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
