# Architecture comparison

**Run:** `results/runs/20261022T181859Z_9c00c799` (baseline)
**Mission:** 1 kW continuous, 6 kW / 30 s pulses every 10 min, 8 h
**Targets:** 35 kg, 60 L, $5,000, $0.40/kWh, 10 years
**Requirements:** [`PROJECT_E_REQUIREMENTS.md`](PROJECT_E_REQUIREMENTS.md)

All numbers below are model outputs. No hardware was measured.

---

## 1. What is compared

Eight fixed candidates in three classes. Every candidate declares its source.

| Class | Definition | Candidates |
|---|---|---|
| A — storage | energy bought before the mission | A1 battery, A2 battery + supercapacitor |
| B — generation | named source converts fuel/heat continuously | B1 diesel, B2 TEG, B3 TPV + heat store, B4 fuel cell |
| C — hybrid | generator sized near average load, buffer carries peaks | C1 fuel cell + battery, C2 diesel + battery |

Common boundary applied to **all** candidates:

- same mission and ambient (25 °C reference);
- packaging factor 1.25 on component mass;
- radiator sized from coolant-side waste heat at 3 kg/m²;
- **converter mass** 1.5 kg/kW at peak throughput (11.25 kg at 6 kW);
- mass and volume include only the unit, not payload, spares, or multi-mission fuel.

The converter-mass term was added after the first comparison. Without it the
hybrids looked ~11 kg lighter and the optimistic scenario falsely passed. It is
now charged uniformly, including to the battery.

---

## 2. Sizing logic

**A1 battery.** End-of-life usable energy = 10/(1−0.20) = 12.5 kWh; capacity over
the 5–95% SOC window = 13.89 kWh. Cells = max(13.89/0.175, 6/0.30) = 79.4 kg.
Add packaging, converter, radiator → 113.2 kg.

**A2.** A1 plus a capacitor bank sized for one pulse with 1.2 margin
(0.06 kWh), 6 Wh/kg and 5 Wh/L. It cannot reduce mission energy, so it is
strictly heavier and costlier.

**B1 diesel.** Genset rated to 6 kW, part-load efficiency derated to ~13.6% at
the mission average. Fuel for one mission only.

**B2 TEG.** ZT = 1.0 at 230/50 °C gives ~6.5% conversion; 93.5% of fuel energy
must be rejected, which drives a 36 m² radiator. Cost at $5/W electric.

**B3 TPV.** 32% cell × 0.85 spectral quality = 27.2% heat-to-electric. Store mass
dominates: graphite at 0.28 kWh/kg plus 25% vessel fraction. Requires ≥1500 °C
external heat, priced at $0.04/kWh.

**B4 fuel cell.** Stack sized to 6 kW, so it is oversized for average load.
Tank at 5 wt% H2 system fraction.

**C1/C2 hybrid.** Source sized at 1.3 × average load; 0.5 kWh buffer carries the
6 kW pulses. Dispatch is simulated at 1 s and verified at 2 s and 0.5 s.

---

## 3. Baseline results

| Key | Architecture | Source | Mass kg | Volume L | Capex USD | LCOE $/kWh | Efficiency | Radiator m² | Targets |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| A1 | LiFePO4 battery only | grid charge | 113.2 | 49.6 | 4,647 | 0.583 | 87.4% | 0.90 | 3/5 |
| A2 | LiFePO4 + supercapacitor | grid charge | 121.5 | 59.6 | 5,407 | 0.628 | 87.4% | 0.90 | 2/5 |
| B1 | Diesel genset, no buffer | diesel | 129.8 | 58.0 | 2,400 | 1.199 | 13.6% | 6.95 | 3/5 |
| B2 | TEG on a burner | combustion heat | 285.5 | 92.9 | 30,000 | 3.960 | 6.5% | 36.05 | 1/5 |
| B3 | TPV + thermal store | ≥1500 °C heat | 244.1 | 136.8 | 2,371 | 0.288 | 27.2% | 8.60 | 3/5 |
| B4 | PEM fuel cell, no buffer | compressed H2 | 98.4 | 51.0 | 21,900 | 1.665 | 50.0% | 1.56 | 2/5 |
| C1 | Fuel cell + battery | compressed H2 | 55.0 | 24.2 | 6,080 | 0.801 | 49.8% | 1.58 | 2/5 |
| C2 | Diesel + battery | diesel | 47.5 | 15.3 | 1,150 | 0.596 | 27.9% | 2.83 | 3/5 |

Efficiency is delivered energy ÷ source energy (fuel LHV, heat, or grid input).

### Target compliance

| Key | ≤35 kg | ≤60 L | ≤$5,000 | ≤$0.40/kWh | No unmet load | Score |
|---|:--:|:--:|:--:|:--:|:--:|:--:|
| A1 | ✗ 113.2 | ✓ 49.6 | ✓ 4,647 | ✗ 0.583 | ✓ | 3/5 |
| A2 | ✗ 121.5 | ✓ 59.6 | ✗ 5,407 | ✗ 0.628 | ✓ | 2/5 |
| B1 | ✗ 129.8 | ✓ 58.0 | ✓ 2,400 | ✗ 1.199 | ✓ | 3/5 |
| B2 | ✗ 285.5 | ✗ 92.9 | ✗ 30,000 | ✗ 3.960 | ✓ | 1/5 |
| B3 | ✗ 244.1 | ✗ 136.8 | ✓ 2,371 | ✓ 0.288 | ✓ | 3/5 |
| B4 | ✗ 98.4 | ✓ 51.0 | ✗ 21,900 | ✗ 1.665 | ✓ | 2/5 |
| C1 | ✗ 55.0 | ✓ 24.2 | ✗ 6,080 | ✗ 0.801 | ✓ | 2/5 |
| C2 | ✗ 47.5 | ✓ 15.3 | ✓ 1,150 | ✗ 0.596 | ✓ | 3/5 |

No candidate meets all five.

---

## 4. Why each fails

- **A1** is the efficiency and simplicity leader but needs 113 kg. Reaching 35 kg
  at this capacity would need ~825 Wh/kg pack-level, versus 175 assumed.
- **A2** adds 0.06 kWh of capacitors (8.3 kg with packaging) and cannot reduce
  the battery. It scores worse than A1; the mission is energy-limited, not
  power-limited.
- **B1** is cheap to buy and light enough only because it carries one mission of
  fuel; at 13.6% average efficiency the fuel cost sets a $1.20/kWh floor.
- **B2** loses on physics: 6.5% conversion at kW scale means a 36 m² radiator and
  $30k of modules. Not viable for portable use at any plausible price.
- **B3** is the cheapest per kWh but is 244 kg and 137 L, needs ≥1500 °C heat,
  and its model ignores standby loss from the thermal store. It is a stationary
  concept.
- **B4** is lighter than A1 but the 6 kW stack and 700 bar tank cost $21.9k; the
  stack is oversized relative to average load.
- **C1** has the best volume (24 L) and good efficiency, but capex and hydrogen
  price put it at $0.80/kWh. Even free H2 leaves it at $0.44/kWh.
- **C2** is the mass, volume and capex leader (47.5 kg, 15 L, $1,150) and misses
  the mass target by 12.5 kg. Its LCOE floor is fuel: $0.50/kWh before any capex.

---

## 5. Scenario robustness

| Scenario | Best score | Lightest | Cheapest per kWh |
|---|---:|---|---|
| Conservative | 3/5 (C2) | 81.7 kg (C1) | $0.488 (B3, 694 kg) |
| Baseline | 3/5 (A1, B1, B3, C2) | 47.5 kg (C2) | $0.288 (B3, 244 kg) |
| Optimistic | 4/5 (A1, A2, C1, C2) | 36.9 kg (C2) | $0.206 (B3, 139 kg) |

The ranking is stable: battery wins efficiency, diesel hybrid wins mass/capex,
TPV wins LCOE only when mass and heat supply are free. What changes is whether
any candidate gets close to the targets — and even optimistically, none does.

---

## 6. What would change the answer

Quantified thresholds from the model (see `economics/COST_MODEL.md`):

| To make… | …meet $0.40/kWh, need | Assumed | Gap |
|---|---|---:|---:|
| A1 battery | battery ≤ $157/kWh | $300/kWh | −48% |
| C2 diesel hybrid | diesel ≤ $0.85/L | $1.40/L | −39% |
| C1 fuel cell hybrid | not achievable; floor $0.441/kWh with free H2 | $6/kg | — |
| B3 TPV | heat ≤ $0.070/kWh | $0.04/kWh | already met |

| To make… | …meet 35 kg, need | Assumed | Gap |
|---|---|---:|---:|
| A1 battery | ~825 Wh/kg pack | 175 Wh/kg | 4.7× |
| C2 diesel hybrid | remove 12.5 kg | 47.5 kg | −26% |

No combination of plausible component improvements closes the battery mass gap.
The diesel mass gap is closable only by shrinking the genset/converter or
accepting a smaller buffer, which the dispatch model currently rejects.

---

## 7. Decision supported by this comparison

1. **Battery-only** is the correct choice if the mission can be recharged and the
   35 kg target is relaxed to ~115 kg.
2. **Diesel hybrid** is the correct choice if outdoor operation is acceptable,
   mass matters, and the LCOE target is relaxed to ~$0.60/kWh.
3. **Fuel-cell hybrid** is not competitive at current H2 and stack prices.
4. **TEG and TPV** are not portable candidates. TPV is only interesting as a
   stationary heat-to-power unit with cheap heat and no mass limit.
5. Supercapacitors add no value to this mission.

The portable-hybrid branch therefore reduces to a **cost and integration problem
between A1, C2 and C1** — not a search for new physics. The experiment plan tests
the one thing the model cannot settle: whether the hybrid buffer actually
delivers the pulses with the assumed efficiency and thermal behaviour.
