# Simulation report — 20261022T195444Z_2d325f92

- git commit: `bbfe9d3a442e91a1f7b143ef060438631762eb07`
- config checksum: `2d325f92ab835d2c…`
- runtime: 7.9 s
- mission: 1.0 kW base, 6.0 kW peak, 8.0 h

## Architecture results

| Key | Architecture | Delivered kWh | Efficiency | Mass kg | Capex USD | LCOE $/kWh | Targets met (of 5) |
|---|---|---:|---:|---:|---:|---:|---:|
| A1 | LiFePO4 battery only | 10.00 | 85.7% | 85.6 | 2,819 | 0.272 | 4 |
| A2 | LiFePO4 + supercapacitor pulse buffer | 10.00 | 85.7% | 95.7 | 3,600 | 0.305 | 4 |
| B1 | Diesel genset, no buffer (rated to peak) | 10.00 | 16.0% | 94.3 | 2,400 | 0.740 | 2 |
| B2 | Thermoelectric generator on a burner | 10.00 | 7.7% | 193.9 | 12,632 | 1.850 | 1 |
| B3 | TPV + high-temperature thermal store | 10.00 | 32.3% | 145.6 | 2,142 | 0.215 | 3 |
| B4 | PEM fuel cell, no buffer (rated to peak) | 10.00 | 55.1% | 89.1 | 11,804 | 0.666 | 2 |
| C1 | PEM fuel cell + small battery buffer | 10.00 | 54.8% | 46.0 | 3,575 | 0.353 | 4 |
| C2 | Diesel genset + small battery buffer | 10.00 | 29.3% | 38.6 | 1,113 | 0.406 | 3 |

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
