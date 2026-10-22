# Simulation report — 20261022T195415Z_920ce114

- git commit: `bbfe9d3a442e91a1f7b143ef060438631762eb07`
- config checksum: `920ce11410717293…`
- runtime: 6.91 s
- mission: 1.0 kW base, 6.0 kW peak, 8.0 h

## Architecture results

| Key | Architecture | Delivered kWh | Efficiency | Mass kg | Capex USD | LCOE $/kWh | Targets met (of 5) |
|---|---|---:|---:|---:|---:|---:|---:|
| A1 | LiFePO4 battery only | 10.00 | 83.0% | 118.4 | 4,866 | 0.602 | 3 |
| A2 | LiFePO4 + supercapacitor pulse buffer | 10.00 | 83.0% | 129.3 | 5,647 | 0.648 | 1 |
| B1 | Diesel genset, no buffer (rated to peak) | 10.00 | 13.6% | 118.5 | 2,400 | 1.199 | 2 |
| B2 | Thermoelectric generator on a burner | 10.00 | 6.2% | 300.3 | 31,579 | 4.169 | 1 |
| B3 | TPV + high-temperature thermal store | 10.00 | 25.8% | 256.9 | 2,453 | 0.301 | 3 |
| B4 | PEM fuel cell, no buffer (rated to peak) | 10.00 | 47.5% | 102.9 | 23,053 | 1.753 | 1 |
| C1 | PEM fuel cell + small battery buffer | 10.00 | 46.9% | 56.5 | 6,583 | 0.871 | 2 |
| C2 | Diesel genset + small battery buffer | 10.00 | 24.7% | 50.3 | 1,149 | 0.668 | 3 |

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
