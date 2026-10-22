# Project E — Plan and progress

**Last updated:** 2026-10-22
**Where the work lives:** `/home/darion-dev/project-e`

---

## 1. What Project E is actually testing

The fictional "Arc Reactor" is treated only as ambition. The real question this
project can answer with evidence is:

> **Can a compact, source-defined energy unit beat a battery pack or a diesel
> genset on mass, cost per delivered kWh, efficiency, or thermal feasibility —
> for a clearly specified mission?**

That is a falsifiable question. It is also the cheapest question to answer,
because it needs only reduced-order physics and real component data — no
prototype, no lab, no fuel.

**Reference mission (fixed for now):**
1 kW continuous, 6 kW pulses for 30 s every 10 min, 8 hour mission.
Targets: ≤ 35 kg, ≤ 60 L, ≤ $5,000 capex, ≤ $0.40/kWh delivered, 10-year life.

Every architecture is scored against the same mission and the same targets.
**No architecture is allowed an undefined energy source.**

---

## 2. The three architecture classes

| Class | Meaning | Examples evaluated |
|---|---|---|
| **A — Storage** | Charge first, discharge later | LiFePO4 pack; LiFePO4 + supercapacitor |
| **B — Generation** | A named source converts fuel/heat continuously | Diesel genset; TEG on a burner; TPV + thermal store; PEM fuel cell |
| **C — Hybrid** | Generator + small buffer for transients | PEM fuel cell + battery; diesel genset + battery |

---

## 3. Where we are right now

```
PHASE 0  Environment + repo setup ................ DONE
PHASE 1  Requirements ............................ NEXT (after sensitivity)
PHASE 2  Literature (12 verified sources) ........ DONE
PHASE 3  Physics models + validation ............. DONE (37 tests pass)
PHASE 4  Simulation pipeline + scenarios ......... DONE (baseline run exists)
PHASE 5  Sensitivity + Monte Carlo ............... IN PROGRESS  <-- you are here
PHASE 6  Cost model + incumbent comparison ....... PENDING
PHASE 7  Validation register (E0-E6) ............. PENDING
PHASE 8  Experiment design (smallest decisive) ... PENDING
PHASE 9  Red-team review ......................... PENDING
PHASE 10 Decision: continue / pivot / stop ....... PENDING
PHASE 11 Repo hygiene, CI, commit ................ PENDING
```

### What is real and working

- Git repo, isolated Python 3.12 venv, pinned dependencies.
- 37 physics tests pass, checking hand-calculated reference values (Carnot,
  Stefan-Boltzmann, TEG formula, battery round-trip, SOC limits, energy closure).
- A simulation runner that writes immutable run folders with config checksum,
  git commit, provenance CSV, raw numbers, plots and a report.
- Three scenarios (baseline, conservative, optimistic), each a full rerun.

### What is not real (and is not claimed)

- No physical hardware was measured. Everything is a model output.
- Component prices and masses are labelled estimates, not quotations.
- No FEA/CFD solver is installed; thermal work is reduced-order.
- Diesel emissions, noise, and indoor-safety disqualification are noted but not scored.

---

## 4. What the numbers say so far (baseline mission)

| Key | Architecture | Mass | Capex | LCOE | Targets met |
|---|---|---:|---:|---:|---:|
| A1 | LiFePO4 battery only | 102 kg | $4,647 | $0.58/kWh | 3 / 5 |
| A2 | LiFePO4 + supercapacitor | 110 kg | $5,407 | $0.63/kWh | 2 / 5 |
| B1 | Diesel genset, no buffer | 119 kg | $2,400 | $1.20/kWh | 3 / 5 |
| B2 | TEG on a burner | 274 kg | $30,000 | $3.96/kWh | 1 / 5 |
| B3 | TPV + thermal store | 233 kg | $2,371 | $0.29/kWh | 3 / 5 |
| B4 | PEM fuel cell, no buffer | 87 kg | $21,900 | $1.67/kWh | 2 / 5 |
| C1 | PEM fuel cell + battery | 44 kg | $6,080 | $0.80/kWh | 2 / 5 |
| C2 | Diesel genset + battery | 36 kg | $1,150 | $0.60/kWh | 3 / 5 |

**Plain-language reading:**

1. **Nothing meets all five targets at baseline.** That is the headline result,
   not a failure of the code.
2. **Battery is the efficiency/cost leader but is 3× too heavy** for this mission.
3. **Diesel hybrid is the mass and capex leader**, but fuel makes it ~$0.60/kWh
   and it is disqualifying indoors.
4. **TEG is not viable at kW scale** — 274 kg and $30k, because 93% of heat must
   be rejected through a large radiator.
5. **TPV becomes cheap per kWh only if the heat is cheap**, and it is still
   233 kg; it is a stationary concept, not a portable one.
6. **Supercapacitors cannot help this mission** — they add 8 kg because the
   battery is energy-limited, not power-limited.

**Optimistic scenario:** C1 and C2 both reach 5/5, so the winner depends on
future cost assumptions, not on novel physics.
**Conservative scenario:** nothing exceeds 3/5. The concept is fragile to
component reality.

---

## 5. The decision this project now faces

The physics does not leave room for a compact "reactor". What remains is a
genuine engineering trade-off, and Project E must pick one honest direction:

| Option | What it means | Evidence needed | Risk |
|---|---|---|---|
| **A. Portable hybrid power unit** | Diesel or H2 fuel cell + buffer, optimised integration | Supplier quotes, emissions/noise test | Not novel; crowded market |
| **B. Stationary heat-to-power** | TPV + cheap/free high-temperature heat, mass not binding | Real heat source, cell cost/area, duty cycle | Needs a host heat source; 233 kg |
| **C. Component play** | High-power buffer, thermal management, controls | One measurable component advantage | Smaller upside, faster to prove |
| **D. Stop generation branch** | Battery-only or buy incumbent | — | Honest, low cost |

The project should **not** continue all four. The sensitivity analysis in
progress determines which uncertain parameter most changes the ranking; that
parameter decides between A, B and C.

---

## 6. Remaining work, in order

| Step | Deliverable | Why it matters | Effort |
|---|---|---|---|
| 5 | `reports/SENSITIVITY_ANALYSIS.md` + tornado/MC figures | Finds which unknown to measure first; tests if the ranking is robust | ~15 min |
| 6 | Requirements + architecture comparison docs | Locks the mission and target rationale; stops goalpost-moving | ~15 min |
| 7 | Cost model + incumbent comparison | Shows whether Project E can beat a real product, not a strawman | ~20 min |
| 8 | Validation register (E0–E6) | States exactly what each claim rests on | ~15 min |
| 9 | Experiment plan | One cheap test that can falsify the preferred branch | ~15 min |
| 10 | Red-team review | Independent attack on assumptions, boundary, hidden inputs | ~15 min |
| 11 | Status, next actions, README, CI, commit | Makes the work reproducible and reviewable | ~10 min |

**Total remaining:** roughly 1.5–2 hours of compute/writing, no purchases, no
external commitments.

---

## 7. What "done" looks like for this cycle

- A reproducible baseline run anyone can regenerate with one command.
- A sensitivity ranking that names the single most important unknown.
- A cost comparison against the strongest incumbent under the same mission.
- An explicit evidence level for every important claim.
- A written decision: continue one branch, pivot, or stop — with reasons.

Not "a working reactor". A defensible answer about whether one can exist here,
and what to measure next.
