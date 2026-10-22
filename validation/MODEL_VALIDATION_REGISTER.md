# Model validation register

**Purpose:** state, for every claim the project makes, what it rests on and what
would be needed to raise it. A passing software test is not physical validation.

---

## 1. Evidence ladder

| Level | Meaning | Acceptable use |
|---|---|---|
| **E0** | Assumption or unsourced estimate | sensitivity input only; never a result |
| **E1** | Engineering estimate with a stated basis | preliminary design; must be measured before commitment |
| **E2** | Published/datasheet value, not independently reproduced | parameter input with citation |
| **E3** | Model reproduced with analytic or independent numerical check | comparative conclusions within the model |
| **E4** | Component measured on a bench by this project | component claims |
| **E5** | Integrated system measured in a relevant environment | system performance claims |
| **E6** | Independently replicated or field-validated | external claims |

Current project ceiling: **E3 for models, E2 for a few parameters, E0 for most
prices.** No E4–E6 exists.

---

## 2. Claim register

| # | Claim | Level | Verification performed | What is missing | Action to raise |
|---|---|---|---|---|---|
| 1 | Energy balance closes for every architecture | E3 | `EnergyAccount` closure asserted; dispatch asserts unmet ≤ 1e-6 kWh | none within model | — |
| 2 | Battery sizing at 20% degradation margin | E3 | hand-checked capacity 13.89 kWh; SOC window 5–95% | real pack at temperature | bench test |
| 3 | LiFePO4 pack specific energy 175 Wh/kg | E2 | range 140–200 in sensitivity | supplier datasheet, measured pack | request quotes |
| 4 | Battery round-trip 92% | E2 | range 88–95% | measured at pulse C-rate | bench test |
| 5 | Battery cycle life 3,000 to 80% | E2 | replacement year computed from fade | cycle test at mission depth | supplier data |
| 6 | Supercapacitor 6 Wh/kg, 5 Wh/L | E2 | range tested | measured module | not decisive; branch rejected |
| 7 | Thermal radiation/convection formulas | E3 | Stefan–Boltzmann and ε-NTU hand checks | real fin geometry, fan power | wind-tunnel or CFD |
| 8 | Radiator 3 kg/m², h = 10 W/m²K | E1 | sensitivity 2–5 kg/m², 5–25 W/m²K | measured heat exchanger | bench test |
| 9 | Steady-state thermal only | E1 | not modelled | transient warm-up, hot-day soak | experiment |
| 10 | Carnot limit enforcement | E3 | test rejects efficiency above Carnot | — | — |
| 11 | TEG efficiency from ZT | E3 | formula checked against hand calculation at ZT=1 | module ZT at temperature | datasheet/bench |
| 12 | TEG 6.5% at 230/50 °C | E2/E3 | computed from ZT and temperatures | contact resistance, leg geometry | bench test |
| 13 | TPV 32% cell × 0.85 spectral | E2 | range 20–40% tested | system-level measured efficiency | literature/bench |
| 14 | Thermal store 0.28 kWh/kg, no standby loss | E1/E2 | mass computed; **losses not modelled** | insulation loss over 8 h | experiment or detailed model |
| 15 | PEM fuel cell 50% LHV | E2 | range 42–58% | part-load curve, degradation | datasheet/bench |
| 16 | H2 tank 5 wt%, 25 L/kg | E2 | range tested | certified system data | supplier |
| 17 | Diesel 28% at rated load, part-load floor 0.35 | E1/E2 | B1 derates to 13.6%; C2 runs near rated | measured part-load curve | bench test |
| 18 | Hybrid dispatch meets pulses with 0.5 kWh buffer | E3 | 1 s simulation; converged at 2 s and 0.5 s; unmet 0 | converter efficiency excluded | experiment |
| 19 | Converter mass 1.5 kg/kW | E1 | applied uniformly to all candidates | weighed inverter | bench |
| 20 | Packaging factor 1.25 | E1 | sensitivity 1.15–1.40 | built enclosure | prototype |
| 21 | Capex estimates | E0 | ranges in sensitivity | quotations | supplier RFQ |
| 22 | LCOE formulation | E3 | hand-checked zero-discount case; replacement-year test | financing/tax | — |
| 23 | Architecture ranking | E3 | full model, three scenarios, 2,000-draw MC | measured inputs | E4/E5 |
| 24 | "No candidate meets all targets" | E2/E3 | baseline + scenarios + MC | only for this mission and model | rerun for other missions |
| 25 | Sensitivity ranking | E2 | OAT over declared ranges + MC | ranges are assumptions | measure top parameters |
| 26 | Emissions, noise, CO | **not modelled** | none | entire domain | experiment + regulations |
| 27 | 230 V AC output, start time, BMS/faults | **not modelled** | none | entire domain | design + test |

---

## 3. Test coverage map

`tests/test_core.py` (37 tests) covers:

- unit validation and rejection of invalid inputs;
- energy balance and efficiency bounds;
- battery SOC limits, round trip, power limits, fade;
- thermal conduction, convection, radiation, ε-NTU, pump parasitic;
- Carnot, TEG, heat engine, TPV, PV derating, fuel flow;
- dispatch energy closure and timestep convergence;
- economics levelized cost and replacement timing;
- architecture ordering invariants.

Not covered by tests:

- model-versus-measurement agreement (none exists);
- thermal transients;
- converter efficiency;
- emissions/noise;
- volume build-up for B1/B2 (ad hoc formulas).

---

## 4. Rules

1. A number without a unit and a source is not admissible.
2. An E0 parameter may move a conclusion; therefore any conclusion that depends
   on one must be reported as conditional.
3. Tests verify code behaviour, not physics. E3 means "internally consistent with
   analytic checks", not "true".
4. No claim may be upgraded without a new artifact (datasheet, measurement, or
   independent replication) recorded in the repository.
5. If a model input is revised, the affected runs must be regenerated and the old
   run kept, not overwritten.
