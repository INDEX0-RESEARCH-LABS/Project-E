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
```

**Cycle complete.** The next cycle is not authorised yet: it needs a real use
case, quotations, and funding for the bench test. See
`reports/NEXT_ACTIONS.md`.

### What is real

- 51 passing tests: analytic reference values, dispatch convergence, economics,
  architecture invariants.
- Immutable run artifacts with config checksum, git commit, provenance, plots.
- 12 DOI-verified sources; full texts not accessed, so no unverified numbers are
  quoted.
- Sensitivity over 2,000 Monte Carlo draws and every declared parameter range.

### What is not real

- No hardware was measured. Component prices are estimates (E0/E1).
- No FEA/CFD; thermal work is steady-state and reduced-order.
- Emissions, noise, 230 V output, start time, and controls are not modelled.

---

## 4. Baseline result (all eight candidates)

| Key | Architecture | Mass kg | Volume L | Capex USD | LCOE $/kWh | Targets |
|---|---|---:|---:|---:|---:|---:|
| A1 | LiFePO4 battery only | 113.2 | 49.6 | 4,647 | 0.583 | 3/5 |
| A2 | Battery + supercapacitor | 121.5 | 59.6 | 5,407 | 0.628 | 2/5 |
| B1 | Diesel genset, no buffer | 129.8 | 58.0 | 2,400 | 1.199 | 3/5 |
| B2 | TEG on a burner | 285.5 | 92.9 | 30,000 | 3.960 | 1/5 |
| B3 | TPV + thermal store | 244.1 | 136.8 | 2,371 | 0.288 | 3/5 |
| B4 | PEM fuel cell, no buffer | 98.4 | 51.0 | 21,900 | 1.665 | 2/5 |
| C1 | Fuel cell + battery | 55.0 | 24.2 | 6,080 | 0.801 | 2/5 |
| C2 | Diesel + battery | 47.5 | 15.3 | 1,150 | 0.596 | 3/5 |

**Plain reading:**

1. **Nothing meets all five targets** at baseline, conservative, or optimistic
   (best: 3/5 baseline, 3/5 conservative, 4/5 optimistic).
2. Battery is efficient and simple but 3× too heavy; 35 kg would need ~825 Wh/kg
   pack-level versus 175 assumed.
3. Diesel hybrid is lightest, smallest and cheapest to buy, but fuel sets a
   ~$0.50/kWh floor; even free capital cannot reach $0.40.
4. TEG is not viable at kW scale: 6.5% conversion, 36 m² radiator, 285 kg.
5. TPV is cheapest per kWh only by ignoring mass, volume, and the ≥1500 °C heat
   supply. It is stationary, not portable.
6. Supercapacitors add 8 kg and no energy; the mission is energy-limited.
7. Fuel cell cannot reach the target even with free hydrogen ($0.44/kWh floor).

---

## 5. The decision

The portable-hybrid direction is retained, but the finding is that it is a
**cost and integration problem, not a new-physics problem**:

| Candidate | Strength | Blocking gap |
|---|---|---|
| A1 battery | efficiency, simplicity, no fuel | mass (113 kg vs 35) |
| C2 diesel hybrid | mass, volume, capex | LCOE ($0.596 vs $0.40) and indoor emissions |
| C1 fuel-cell hybrid | volume, no local emissions | capex/LCOE ($0.80), H2 supply |

The single most influential unknown is **missions per year** (up to $2.68/kWh),
which is a use-case question. The second is diesel price ($1.24/kWh range).
Hardware cannot answer either.

---

## 6. Next cycle (not started)

| Step | Deliverable | Gate |
|---|---|---|
| 1 | Real use case + duty cycle | G1: dominant axis exists |
| 2 | Three supplier quotations | G2: real prices within 20% of model |
| 3 | Bench test of hybrid buffer (`experiments/EXPERIMENT_PLAN.md`) | G3: H1/H3 pass |
| 4 | Re-rank with measured/real inputs | G4: 4/5 targets |
| 5 | Only then consider a prototype | — |

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
