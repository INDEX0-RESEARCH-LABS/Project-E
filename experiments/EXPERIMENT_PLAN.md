# Experiment plan — hybrid buffer bench test

**Branch:** portable hybrid (C2 diesel + battery; C1 fuel cell + battery uses the
same buffer)
**Purpose:** test the one claim the model cannot settle — that a small buffer,
charged by a source sized near average load, actually delivers 6 kW pulses for
8 h with the assumed efficiency and thermal behaviour.
**Status:** planned, not funded, not started.

---

## 1. What is being tested

| ID | Hypothesis | Falsified if |
|---|---|---|
| H1 | A 1.45 kW DC source (1.1× average) + 0.3 kWh LFP buffer serves the 8 h mission with unmet energy ≤ 0.1% | unmet > 1% of 10 kWh, or the run aborts |
| H2 | Measured source-to-load efficiency is within ±15% relative of the modelled 24.7% (C2) | measured efficiency < 70% of model |
| H3 | At 40 °C ambient, buffer and converter stay below datasheet limits with the modelled radiator | any limit exceeded, or thermal shutdown |
| H4 | The dispatch rule holds SOC within 5–95% across three repeats | SOC leaves the window |

H2 is a **model check**, not a performance record. This test cannot prove the
LCOE or the 10-year life.

---

## 2. Why this test and not another

- The mass, capex and LCOE conclusions are dominated by prices (E0), which a
  bench test cannot fix. A test of those would measure the wrong thing.
- The dispatch claim is E3 (model-only) and is the only system-level claim that a
  small, affordable rig can move to E4/E5.
- A failure here invalidates C2 and C1 together, which is decisive for the branch.
- A success does **not** make the concept competitive; it only removes a
  feasibility objection.

---

## 3. Apparatus

Two stages, so a control failure is not confused with a source failure.

| Item | Specification | Purpose | Cost estimate (E0) |
|---|---|---|---:|
| LFP pack | 48 V, 0.3 kWh usable, BMS with CAN | buffer under test | $300–600 |
| Bidirectional inverter/charger | 6 kW peak, 48 V, ≥94% | pulse delivery and recharge | $500–1,200 |
| DC source (stage 1) | 0–60 V, 0–2 kW, programmable | emulates the genset without fuel | $300–900 (or lab supply) |
| Diesel genset (stage 2) | 2 kW electric, inverter or synchronous | real source efficiency and fuel use | $500–1,000 |
| Programmable load | 6 kW, 0–60 V, or resistor bank + relays | mission profile | $400–1,500 |
| Power analyser / shunts | ±1% of reading, 10 Hz logging | energy and efficiency | $300–800 |
| Thermocouples | 6 × type K, ±0.5 K | pack, converter, coolant, ambient | $120–250 |
| DAQ / logger | ≥10 channels, CSV, 1 Hz | records every run | $200–600 |
| Fuel scale | 0–5 kg, ±1 g | fuel mass per run | $60–150 |
| CO monitor | portable, alarm | safety and emissions note | $120–250 |
| Enclosure / ducting | insulated box, fan, radiator | 40 °C ambient simulation | $150–400 |
| **Total** | | | **$3,000–7,750** |

Prices are single-unit retail estimates, not quotations. A university or
workshop with a programmable supply and load bank can cut this substantially.

Instrumentation uncertainty: power ±1%, temperature ±0.5 K, fuel mass ±1 g,
timing ±10 ms. These are stated because the pass/fail thresholds are wider than
the uncertainty; no result will be reported to more precision than this.

---

## 4. Procedure

### 4.1 Design, before any run

The unit of replication is **one complete 8 h mission**, not an individual
sample. Treating 10 Hz samples as replicates would fabricate precision.

| Element | Choice |
|---|---|
| Factors | source type: DC emulator vs diesel genset; ambient: 25 °C vs 40 °C |
| Cells | 2 × 2 = 4 conditions, 3 missions each = 12 missions |
| Control | DC emulator at 25 °C: tests dispatch without fuel or heat |
| Blocking | one block per chamber/day; all four conditions appear in each block where possible |
| Randomisation | run order pre-generated with seed `20261022`, recorded before the first run |
| Blinding | not possible; analysis uses raw logger files and a fixed script |
| MSA | calibrate power/current shunts and thermocouples before and after each block; repeat one reference mission at the start and end |
| Stopping | fixed 3 repeats per cell; no early stop on a favourable result; stop immediately on a safety limit or repeated fault |

A failed mission is a data point and is reported. Repeats are used for a range
and a visual consistency check, not a significance test: n = 3 cannot support
one.

### Stage 0 — characterisation (1 day)

1. Measure buffer round-trip efficiency at 0.5 C charge / 2 C pulse discharge.
2. Measure converter efficiency at 1, 3, and 6 kW.
3. Measure source efficiency at 25%, 50%, 75%, 100% of rated load (stage 2 only).
4. Record all values with instrumentation uncertainty.

### Stage 1 — control and buffer with a DC source (3 days)

1. Program the exact mission profile: 1 kW base, 6 kW for 30 s every 600 s, 8 h.
2. Set the DC source to 1.45 kW (1.1× average DC load), not 1.3 kW.
3. Run three complete missions. Between runs, recharge the buffer as the design
   intends and record recharge energy and time.
4. Log at 10 Hz: load, source current, buffer current, SOC, temperatures.
5. Compute unmet energy, delivered energy, round-trip efficiency, SOC range.

### Stage 2 — diesel source (2 days, outdoors)

1. Repeat three 8 h missions at 25 °C with the genset as the source, then three
   at 40 °C.
2. Measure fuel mass before and after; compute fuel energy from LHV (9.94 kWh/L,
   0.83 kg/L) and system efficiency.
3. Record CO at 1 m from the exhaust; confirm outdoor-only operation.

### Stage 3 — thermal (2 days)

1. Place the buffer and converter in the insulated enclosure; hold 40 ± 2 °C.
2. Repeat three missions at that ambient with the modelled radiator area
   (3.33 m²) and airflow.
3. Record peak cell, converter, and coolant temperatures.

### Repeats

Three repeats per condition. Report mean and full range. With n = 3, no
statistical significance is claimed; the test is a feasibility screen.

---

## 5. Pass / fail

| Metric | Pass | Marginal | Fail |
|---|---|---|---|
| Unmet energy | ≤ 10 Wh (0.1%) | 10–100 Wh | > 100 Wh |
| SOC range | 0.05–0.95 | 0.03–0.97 | outside |
| Buffer round-trip | ≥ 0.88 | 0.82–0.88 | < 0.82 |
| System efficiency vs model | within ±15% rel. | ±15–30% | > 30% low |
| Peak temperature | ≥ 10 K margin to limit | 0–10 K | at/over limit |
| Aborts / faults | none | one recoverable | repeated |

Any "fail" on H1 or H3 stops the C2/C1 branch until the model is revised.

---

## 6. Decision rules

| Outcome | Decision |
|---|---|
| All pass | Dispatch claim moves to E4/E5. Next cycle: supplier RFQs for cost, not more bench work. |
| H1/H3 pass, H2 fails | Keep the architecture, replace the efficiency parameter with the measured value, rerun LCOE. |
| H1 fails | Buffer or control is undersized. Re-size from measured data once; if still failing, drop C2/C1. |
| H3 fails | Portable hybrid is thermally infeasible at 40 °C with passive rejection; require active cooling, re-cost, or drop. |
| Any safety issue | Stop. Do not continue the diesel branch indoors under any result. |

---

## 7. Safety and ethics

- Diesel runs outdoors only, downwind, with a CO alarm and a fire extinguisher.
- Fuel stored in a approved container, away from the load bank.
- 6 kW resistive load is a burn and fire hazard; guard and interlock.
- LFP pack: fuse at the pack, pre-charge the inverter, do not exceed datasheet
  charge/discharge limits, monitor cell temperature.
- No unattended 8 h runs.
- Results are published with the failed runs included.

---

## 8. What this experiment cannot show

- That the unit meets the $0.40/kWh or $5,000 targets. Those are price questions.
- That the pack lasts 10 years. That needs a cycle-life test of months.
- That the design is manufacturable, certifiable, or safe in all environments.
- That the mission itself is the right one.

Budget: **$3,000–7,750** (E0 estimates), **~3 weeks** including procurement.
