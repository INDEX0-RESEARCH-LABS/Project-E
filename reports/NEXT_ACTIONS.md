# Next actions

**Cycle:** 2026-10-22
**State:** comparison complete; portable hybrid branch selected; no candidate
meets all targets; no hardware exists.

Ordered by decision value per unit of effort. Nothing here is funded.

---

## A. This week — close the evidence gaps that can change the decision

| ID | Action | Why | Effort | Gate |
|---|---|---|---|---|
| A1 | Define the real use case and duty cycle (missions/year, indoor/outdoor, payload) | Utilisation is the single most influential parameter ($2.68/kWh); the mission was invented | 1 h with the user | no purchase until answered |
| A2 | Decide whether the 35 kg target is dry or wet (fuel, cables, spares) | C2 is 47.5 kg dry; the answer changes whether it is 12 kg or 20 kg over | 30 min | requirements v1.1 |
| A3 | Get three real quotations: 0.5 kWh LFP + 6 kW converter, 2 kW genset, 48 V BMS | All capex is E0; quotations replace the weakest inputs | 1 week lead time, no cost | update configs, rerun |
| A4 | Fix converter efficiency in dispatch (±5%) | Known model gap; affects efficiency and heat rejection | 1 h code + rerun | tests pass |
| A5 | Commit and push the current cycle | Reproducibility | 15 min | CI green |

## B. Next — one decisive bench test

| ID | Action | Why | Cost | Gate |
|---|---|---|---|---|
| B1 | Run the hybrid buffer bench test (`experiments/EXPERIMENT_PLAN.md`) | Only system claim a small rig can move from E3 to E4/E5 | $3,000–7,750 | H1/H3 pass |
| B2 | Measure genset efficiency vs load at 25/50/75/100% | The 28% assumption and part-load floor drive B1/C2 | included in B1 | replace E1/E2 with E4 |
| B3 | Measure pack round-trip at pulse C-rate and 40 °C | Drives both efficiency and thermal feasibility | included in B1 | replace E2 with E4 |

## C. Only if B1 passes — commercial questions

| ID | Action | Why |
|---|---|---|
| C1 | Build a costed BOM from quotations for C2 and A1 | Replace every E0 price |
| C2 | Test a second mission (e.g. 4 h, 2 kW) to see if the ranking holds | The current result is one mission |
| C3 | Optimise C2 sizing (source 1.0–2.0 kW, buffer 0.3–1.0 kWh) | Fixed sizing may be 10–20% off |
| C4 | Decide on emissions/noise enclosure cost | Currently excluded and biased toward diesel |

## D. Do not do

- Do not buy TEG or TPV hardware. Both fail on physics or mass at this scale.
- Do not add supercapacitors. They add 8 kg and no energy.
- Do not claim a prototype, a working reactor, or net generation.
- Do not chase the $0.40/kWh target with diesel; the fuel floor is ~$0.50/kWh.
- Do not relax the mass target without recording it as a requirement change.

---

## Decision gates

| Gate | Question | If no |
|---|---|---|
| G1 | Is there a real use case with a dominant axis? | Stop at the comparison; publish the negative result |
| G2 | Do quotations keep C2 or A1 within 20% of the model? | Re-rank with real prices |
| G3 | Does the bench test pass H1 and H3? | Drop C2/C1; fall back to A1 with a relaxed mass target |
| G4 | Can the unit meet 4 of 5 targets with measured inputs? | Do not build a prototype |

## Current status against gates

- G1: **unanswered** — no external use case yet.
- G2: **not started** — no quotations.
- G3: **not started** — no hardware.
- G4: **no** — best is 3/5 baseline, 4/5 optimistic (mass still fails).
