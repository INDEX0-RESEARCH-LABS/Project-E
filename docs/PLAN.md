# Project E — Plan and progress

**Last updated:** 2026-10-23
**Where the work lives:** `/home/darion-dev/project-e`
**Remote:** https://github.com/INDEX0-RESEARCH-LABS/Project-E

---

## 1. What Project E is testing

The "Arc Reactor" is treated only as ambition. The real question:

> **Can a compact, source-defined energy unit beat a battery pack or a diesel
> genset on mass, cost per delivered kWh, efficiency, or thermal feasibility —
> for a fixed mission?**

**Reference mission:** 1 kW continuous, 6 kW for 30 s every 10 min, 8 h.
Targets: ≤ 35 kg, ≤ 60 L, ≤ $5,000 capex, ≤ $0.40/kWh, 10-year life.

Every architecture is scored on the same mission, and none may have an undefined
energy source. Full requirements: `docs/PROJECT_E_REQUIREMENTS.md`.

---

## 2. The three architecture classes

| Class | Meaning | Candidates |
|---|---|---|
| **A — Storage** | charge first, discharge later | A1 battery; A2 battery + supercapacitor |
| **B — Generation** | named source converts fuel/heat continuously | B1 diesel; B2 TEG; B3 TPV + heat store; B4 fuel cell |
| **C — Hybrid** | generator near average load + buffer for peaks | C1 fuel cell + battery; C2 diesel + battery |

---

## 3. Where we are

```
PHASE 0  Environment + repo ..................... DONE
PHASE 1  Requirements ........................... DONE
PHASE 2  Literature (12 verified DOIs) .......... DONE
PHASE 3  Physics models + analytic tests ........ DONE
PHASE 4  Simulation + 3 scenarios ............... DONE
PHASE 5  Sensitivity + Monte Carlo .............. DONE
PHASE 6  Cost model + incumbent comparison ...... DONE
PHASE 7  Validation register (E0-E6) ............ DONE
PHASE 8  Experiment plan ........................ DONE (not funded)
PHASE 9  Red-team review ........................ DONE
PHASE 10 Decision: branch selected ............... DONE (portable hybrid)
PHASE 11 CI, tests, commit ...................... DONE
PHASE 12 Sizing optimisation .................... DONE
PHASE 13 Requirement feasibility study .......... DONE
PHASE 14 Experimental design revision ........... DONE
PHASE 15 Independent model audit + fixes ........ DONE
```

**Cycle 3 complete.** The next cycle still needs a real use case, quotations,
and funding for the bench test. See `reports/NEXT_ACTIONS.md`.

### What is real

- 57 passing tests: analytic reference values, dispatch convergence, converter
  loss accounting, config rejection, Carnot guard, economics, Pareto logic,
  architecture invariants.
- Immutable run artifacts with config checksum, git commit, provenance, plots.
- 12 DOI-verified sources; full texts not accessed, so no unverified numbers are
  quoted.
- Sensitivity over 2,000 Monte Carlo draws and every declared parameter range.
- Deterministic sizing grid (84 points) and mission/peak scaling studies, with
  infeasible points reported rather than dropped.

### What is not real

- No hardware was measured. Component prices are estimates (E0/E1).
- No FEA/CFD; thermal work is steady-state and reduced-order.
- Emissions, noise, 230 V output, start time, and controls are not modelled.

---

## 4. Baseline result (all eight candidates)

| Key | Architecture | Mass kg | Volume L | Capex USD | LCOE $/kWh | Targets |
|---|---|---:|---:|---:|---:|---:|
| A1 | LiFePO4 battery only | 118.4 | 52.2 | 4,866 | 0.602 | 3/5 |
| A2 | Battery + supercapacitor | 129.3 | 65.4 | 5,647 | 0.648 | 1/5 |
| B1 | Diesel genset, no buffer | 118.5 | 72.5 | 2,400 | 1.199 | 2/5 |
| B2 | TEG on a burner | 300.3 | 122.3 | 31,579 | 4.169 | 1/5 |
| B3 | TPV + thermal store | 256.9 | 144.0 | 2,453 | 0.301 | 3/5 |
| B4 | PEM fuel cell, no buffer | 102.9 | 64.7 | 23,053 | 1.753 | 1/5 |
| C1 | Fuel cell + battery | 56.5 | 31.7 | 6,583 | 0.871 | 2/5 |
| C2 | Diesel + battery | 50.3 | 21.3 | 1,149 | 0.668 | 3/5 |

**Plain reading:**

1. **Nothing meets all five targets** at baseline, conservative, or optimistic
   (best: 3/5 baseline, 3/5 conservative, 4/5 optimistic).
2. Battery is efficient and simple but 3.4× too heavy; 35 kg would need ~870 Wh/kg
   pack-level versus 175 assumed. It is also **power-limited**: even a 0.5 h
   mission is 40.3 kg because of the 6 kW pulse.
3. Diesel hybrid is lightest, smallest and cheapest to buy, but fuel alone contributes
   ~$0.56/kWh; even free capital cannot reach $0.40.
4. TEG is not viable at kW scale: 6.2% conversion, 38 m² radiator, 300 kg.
5. TPV is cheapest per kWh only by ignoring mass, volume, and the ≥1500 °C heat
   supply. It is stationary, not portable.
6. Supercapacitors add 8.8 kg and no energy.
7. Fuel cell cannot reach the target even with free hydrogen ($0.492/kWh floor).
8. Re-sizing the hybrid finds 50.3 kg (C2) at 1.1× source and 0.3 kWh buffer —
   still 15.3 kg over target. The gap is the converter plus pulse-rated pack,
   not the buffer.

---

## 5. The decision

The portable-hybrid direction is retained, but the finding is that it is a
**cost and integration problem, not a new-physics problem**:

| Candidate | Strength | Blocking gap |
|---|---|---|
| A1 battery | efficiency, simplicity, no fuel | mass (118.4 kg vs 35) |
| C2 diesel hybrid | mass, volume, capex | LCOE ($0.668 vs $0.40) and indoor emissions |
| C1 fuel-cell hybrid | volume, no local emissions | capex/LCOE ($0.871), H2 supply |

The single most influential unknown is **missions per year** (up to $2.824/kWh),
which is a use-case question. The second is diesel price ($1.306/kWh range).
Hardware cannot answer either.

The requirement set itself is now a finding: 35 kg, 6 kW and 8 h are jointly
infeasible for A1 and C2 with the assumed pulse-power components. The next cycle
must either renegotiate the peak/mass requirement, adopt a modular pack, or
measure a genuinely higher pulse-power density before more architecture work.

---

## 6. Next cycle (not started)

| Step | Deliverable | Gate |
|---|---|---|
| 1 | Real use case + duty cycle | G1: dominant axis exists |
| 2 | Renegotiate peak/mass, or approve modular pack | G1b: a feasible requirement set |
| 3 | Three supplier quotations | G2: real prices within 20% of model |
| 4 | Bench test of pulse power and hybrid buffer (`experiments/EXPERIMENT_PLAN.md`) | G3: H1/H3 pass |
| 5 | Re-rank with measured/real inputs | G4: 4/5 targets |
| 6 | Only then consider a prototype | — |

Estimated bench cost: **$3,000–7,750**, ~3 weeks. No purchase is authorised.

---

## 7. What "done" means for this cycle

- A reproducible baseline anyone can regenerate.
- A sensitivity ranking that names the most important unknown.
- A cost comparison against the strongest incumbent.
- An explicit evidence level for every claim.
- A written decision on the branch.

Delivered. What is **not** delivered — and not claimed — is a working compact
reactor, a prototype, or a path to all five targets.
