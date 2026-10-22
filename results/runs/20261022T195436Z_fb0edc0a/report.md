# Simulation report — 20261022T195436Z_fb0edc0a

- git commit: `bbfe9d3a442e91a1f7b143ef060438631762eb07`
- config checksum: `fb0edc0a1434059f…`
- runtime: 9.03 s
- mission: 1.0 kW base, 6.0 kW peak, 8.0 h

## Architecture results

| Key | Architecture | Delivered kWh | Efficiency | Mass kg | Capex USD | LCOE $/kWh | Targets met (of 5) |
|---|---|---:|---:|---:|---:|---:|---:|
| A1 | LiFePO4 battery only | 10.00 | 79.4% | 209.1 | 7,999 | 0.974 | 1 |
| A2 | LiFePO4 + supercapacitor pulse buffer | 10.00 | 79.4% | 221.4 | 8,780 | 1.032 | 1 |
| B1 | Diesel genset, no buffer (rated to peak) | 10.00 | 10.7% | 199.6 | 2,400 | 2.301 | 2 |
| B2 | Thermoelectric generator on a burner | 10.00 | 3.7% | 1202.2 | 75,789 | 11.659 | 1 |
| B3 | TPV + high-temperature thermal store | 10.00 | 16.2% | 731.8 | 3,524 | 0.510 | 2 |
| B4 | PEM fuel cell, no buffer (rated to peak) | 10.00 | 39.9% | 135.4 | 40,151 | 3.894 | 1 |
| C1 | PEM fuel cell + small battery buffer | 10.00 | 39.1% | 84.7 | 11,555 | 1.972 | 2 |
| C2 | Diesel genset + small battery buffer | 10.00 | 19.3% | 91.4 | 1,194 | 1.297 | 3 |

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
