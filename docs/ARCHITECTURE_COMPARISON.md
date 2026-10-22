# Architecture comparison

**Baseline run:** `results/runs/20261022T195415Z_920ce114`
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
- packaging factor 1.25 on component **mass and volume**;
- radiator sized from coolant-side waste heat at 3 kg/m²;
- converter mass 1.5 kg/kW at peak throughput (11.25 kg at 6 kW);
- converter efficiency 95% at the AC boundary, charged to fuel/input energy;
- B1 is native AC (its alternator is inside `efficiency_lhv`), so it carries no
  separate converter;
- mass and volume include only the unit, not payload, spares, or multi-mission fuel.

Converter efficiency and volume packaging were both fixed in cycle 3. Before
that, C2 paid the converter twice while B1 paid it zero times, and hybrids
reported unpackaged volume. Both made the comparison look better than it is.

---

## 2. Sizing logic

**A1 battery.** End-of-life usable energy = 10/0.95/(1−0.20) = 13.16 kWh; capacity
over the 5–95% SOC window = 14.62 kWh. Cells = max(14.62/0.175, 6/0.95/0.30) =
83.6 kg. Add packaging, converter, radiator → 118.4 kg.

**A2.** A1 plus a capacitor bank sized for one pulse with 1.2 margin
(0.053 kWh DC), 6 Wh/kg and 5 Wh/L. It cannot reduce mission energy, so it is
strictly heavier and costlier.

**B1 diesel.** Genset rated to 6 kW, part-load efficiency derated to 13.6% at
the mission average. Fuel for one mission only.

**B2 TEG.** ZT = 1.0 at 230/50 °C gives 6.2% conversion after the output stage;
93.8% of fuel energy must be rejected, which drives a 38 m² radiator. Cost at
$5/W electric.

**B3 TPV.** 32% cell × 0.85 spectral quality × 0.95 converter = 25.8%
heat-to-electric. Store mass dominates: graphite at 0.28 kWh/kg plus 25% vessel
fraction. Requires ≥1500 °C external heat, priced at $0.04/kWh.

**B4 fuel cell.** Stack sized to 6.32 kW DC (6 kW AC), so it is oversized for
average load. Tank at 5 wt% H2 system fraction.

**C1/C2 hybrid.** Source sized at **1.1 × average mission DC power**; 0.3 kWh
buffer carries the pulses. This is the lightest point found in the sizing grid
(`reports/SIZING_STUDY.md`), and it is higher than 1.0× because a source rated at
exactly average load cannot replace the buffer's round-trip losses over repeated
missions. Dispatch is simulated at 1 s and verified at 2 s and 0.5 s.

---

## 3. Baseline results

| Key | Architecture | Source | Mass kg | Volume L | Capex USD | LCOE $/kWh | Efficiency | Radiator m² | Targets |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| A1 | LiFePO4 battery only | grid charge | 118.4 | 52.2 | 4,866 | 0.602 | 83.0% | 0.90 | 3/5 |
| A2 | LiFePO4 + supercapacitor | grid charge | 129.4 | 65.4 | 5,647 | 0.648 | 83.0% | 0.90 | 1/5 |
| B1 | Diesel genset, no buffer | diesel | 118.5 | 72.5 | 2,400 | 1.199 | 13.6% | 6.95 | 2/5 |
| B2 | TEG on a burner | combustion heat | 300.3 | 122.3 | 31,579 | 4.169 | 6.2% | 38.08 | 1/5 |
| B3 | TPV + thermal store | ≥1500 °C heat | 256.9 | 144.0 | 2,453 | 0.301 | 25.8% | 9.22 | 3/5 |
| B4 | PEM fuel cell, no buffer | compressed H2 | 102.9 | 64.7 | 23,053 | 1.753 | 47.5% | 1.73 | 1/5 |
| C1 | Fuel cell + battery | compressed H2 | 56.5 | 31.7 | 6,583 | 0.871 | 46.9% | 1.77 | 2/5 |
| C2 | Diesel + battery | diesel | 50.3 | 21.3 | 1,149 | 0.668 | 24.7% | 3.33 | 3/5 |

Efficiency is delivered AC energy ÷ source energy (fuel LHV, heat, or grid input),
including the 95% output stage.

### Target compliance

| Key | ≤35 kg | ≤60 L | ≤$5,000 | ≤$0.40/kWh | No unmet load | Score |
|---|:--:|:--:|:--:|:--:|:--:|:--:|
| A1 | ✗ 118.4 | ✓ 52.2 | ✓ 4,866 | ✗ 0.602 | ✓ | 3/5 |
| A2 | ✗ 129.4 | ✗ 65.4 | ✗ 5,647 | ✗ 0.648 | ✓ | 1/5 |
| B1 | ✗ 118.5 | ✗ 72.5 | ✓ 2,400 | ✗ 1.199 | ✓ | 2/5 |
| B2 | ✗ 300.3 | ✗ 122.3 | ✗ 31,579 | ✗ 4.169 | ✓ | 1/5 |
| B3 | ✗ 256.9 | ✗ 144.0 | ✓ 2,453 | ✓ 0.301 | ✓ | 3/5 |
| B4 | ✗ 102.9 | ✗ 64.7 | ✗ 23,053 | ✗ 1.753 | ✓ | 1/5 |
| C1 | ✗ 56.5 | ✓ 31.7 | ✗ 6,583 | ✗ 0.871 | ✓ | 2/5 |
| C2 | ✗ 50.3 | ✓ 21.3 | ✓ 1,149 | ✗ 0.668 | ✓ | 3/5 |

No candidate meets all five.

---

## 4. Why each fails

- **A1** is the efficiency and simplicity leader but needs 118 kg. Reaching 35 kg
  at this capacity would need ~870 Wh/kg pack-level, versus 175 assumed (5.0×).
- **A2** adds a capacitor bank and cannot reduce the battery. It now also fails
  volume once packaging is counted uniformly.
- **B1** is cheap to buy and needs no converter, but at 13.6% average efficiency
  fuel dominates its $1.20/kWh, and its packaged volume is 72.5 L.
- **B2** loses on physics: 6.2% conversion at kW scale means a 38 m² radiator and
  $31.6k of modules. Not viable for portable use at any plausible price.
- **B3** is the cheapest per kWh but is 257 kg and 144 L, needs ≥1500 °C heat,
  and its model ignores standby loss from the thermal store. Stationary concept.
- **B4** is lighter than A1 but the 6.3 kW stack and 700 bar tank cost $23.1k; the
  stack is oversized relative to average load, and packaged volume is 64.7 L.
- **C1** has a good volume (31.7 L) and efficiency, but capex and hydrogen price
  put it at $0.87/kWh. Even free H2 leaves it at $0.49/kWh.
- **C2** is the mass, volume and capex leader (50.3 kg, 21.3 L, $1,149) and misses
  the mass target by 15.3 kg. Fuel alone contributes ≈$0.56/kWh of its $0.668; free fuel would still leave $0.11/kWh of capital and O&M.

---

## 5. Sizing study — the 1.1× / 0.3 kWh point

Grid over source factor 0.9–1.5 × average DC load and buffer 0.3–1.0 kWh,
42 points per hybrid. A point is feasible only if dispatch serves the mission
(`unmet ≤ 1e-6 kWh`) **and** the source can cover the DC load plus buffer loss
over repeated missions. Full data: `reports/SIZING_STUDY.md`.

| Hybrid | Feasible | Lightest point | LCOE there | Targets | Gap to 35 kg |
|---|---:|---|---:|---:|---:|
| C2 diesel | 30/42 | 50.3 kg at 1.1×, 0.3 kWh | $0.669 | 3/5 | +15.3 kg |
| C1 fuel cell | 30/42 | 56.5 kg at 1.1×, 0.3 kWh | $0.871 | 2/5 | +21.5 kg |

Twelve points per hybrid are rejected: the 0.9× column is below load, and every
1.0× point fails the sustainability test (source = average, no margin for buffer
losses). The baseline now uses the lightest feasible point, not a fixed 1.3× rule.
Re-sizing finds 7.3 kg for C2 but cannot close the mass gap.

---

## 6. Requirement feasibility — the 35 kg target is power-limited

`reports/MISSION_SCALING.md` varies duration and peak with everything else fixed.

| Architecture | Mass at 0.5 h | Mass at 8 h | Cause of the floor |
|---|---:|---:|---|
| A1 battery | 40.3 kg | 118.4 kg | 6 kW pulse: 21.1 kg of cells + 11.2 kg converter |
| C2 diesel hybrid | 44.8 kg | 50.3 kg | converter + minimum genset, buffer, radiator |
| B1 diesel genset | 111.3 kg | 118.5 kg | 6 kW genset |

The important result: **A1 cannot reach 35 kg at any duration.** The 6 kW pulse
forces 6 kW ÷ 300 W/kg = 21.1 kg of cells (26.3 kg packaged) plus an 11.25 kg
converter before any energy is stored. C2's floor is 44.8 kg at 0.5 h, driven by
the converter and minimum generator set, not by the 8 h duration.

Peak-load sweep at 8 h:

| Peak kW | A1 kg | C2 kg |
|---:|---:|---:|
| 2 | 93.7 | 36.8 |
| 3 | 99.9 | 40.2 |
| 4 | 106.1 | 43.6 |
| 6 | 118.4 | 50.3 |
| 8 | 130.7 | 57.1 |

Two independent failures: the peak sets a ~40 kg floor for A1 and a ~37 kg floor
for C2 at 2 kW; the 8 h energy sets a ~118 kg floor for a battery. Neither can be
fixed by re-sizing the same components.

---

## 7. Scenario robustness

| Scenario | Best score | Lightest | Cheapest per kWh |
|---|---:|---|---|
| Conservative | 3/5 (C2) | 84.7 kg (C1) | $0.510 (B3, 732 kg) |
| Baseline | 3/5 (A1, B3, C2) | 50.3 kg (C2) | $0.301 (B3, 257 kg) |
| Optimistic | 4/5 (A1, A2, C1) | 38.6 kg (C2) | $0.215 (B3, 146 kg) |

The ranking is stable: battery wins efficiency, diesel hybrid wins
mass/volume/capex, TPV wins LCOE only when mass and heat supply are free. What
changes is how close a candidate gets — and even optimistically, none reaches
35 kg or 5/5.

---

## 8. What would change the answer

Quantified thresholds from the model (see `economics/COST_MODEL.md`):

| To make… | …meet $0.40/kWh, need | Assumed | Gap |
|---|---|---:|---:|
| A1 battery | battery ≤ $145.9/kWh | $300/kWh | −51% |
| C2 diesel hybrid | diesel ≤ $0.732/L | $1.40/L | −48% |
| C1 fuel cell hybrid | not achievable; floor $0.492/kWh with free H2 | $6/kg | — |
| B3 TPV | heat ≤ $0.0656/kWh | $0.04/kWh | already met |

| To make… | …meet 35 kg, need | Assumed | Gap |
|---|---|---:|---:|
| A1 battery | ~870 Wh/kg pack | 175 Wh/kg | 5.0× |
| C2 diesel hybrid | remove 15.3 kg at the optimum | 50.3 kg | −30% |

No plausible component improvement closes the battery mass gap. The diesel gap
is closable only with a higher-power-density converter/pack, a smaller source,
or a relaxed peak requirement — the study says the converter and pulse-rated
pack, not the buffer, are the binding terms.

---

## 9. Decision supported by this comparison

1. **Battery-only** is the correct choice if the mission can be recharged and the
   35 kg target is relaxed to ~118 kg (or ~40 kg with a 2 kW peak).
2. **Diesel hybrid** is the correct choice if outdoor operation is acceptable,
   mass matters, and the LCOE target is relaxed to ~$0.67/kWh.
3. **Fuel-cell hybrid** is not competitive at current H2 and stack prices.
4. **TEG and TPV** are not portable candidates. TPV is only interesting as a
   stationary heat-to-power unit with cheap heat and no mass limit.
5. Supercapacitors add no value to this mission.

The portable-hybrid branch reduces to a **cost and integration problem between
A1, C2 and C1** — not a search for new physics. The requirement set, not the
component list, is the first thing to renegotiate: 35 kg and 6 kW are jointly
infeasible with the assumed pulse-power components.

The experiment plan tests the one thing the model cannot settle: whether the
hybrid buffer actually delivers the pulses with the assumed efficiency and
thermal behaviour, and what the pack/converter pulse-power density really is.
