# Red-team review

**Scope:** attack the model, the mission, and the conclusions. Each item states
severity, evidence, response, and status. Written against the baseline run
`20261022T195415Z_920ce114` and the cycle-3 sensitivity report.

Severity: **H** could change the decision, **M** changes a number, **L** cosmetic.

---

## 1. The mission is invented

**H.** The 1 kW / 6 kW / 8 h / 35 kg mission was chosen by the project, not by a
customer. Every conclusion is conditional on it.

*Response:* locked in `docs/PROJECT_E_REQUIREMENTS.md` with change control. A
different mission requires a full rerun. At 60 kg, C2 (50.3 kg) would pass mass
and only LCOE would block it — the decision is sensitive to a target nobody has
validated.

*Status:* accepted, documented. Needs a real use case before any purchase.

---

## 2. Prices are E0 and they decide the winner

**H.** The Monte Carlo P10–P90 spread (e.g. C2 $0.590–$1.008/kWh) is wider than the
difference between candidates. "B3 is cheapest in 83% of draws" is a statement
about assumed ranges, not about the world.

*Response:* every price carries a range and evidence level; the report says the
MC is a bounded what-if, not a forecast. The cost model lists break-even
thresholds so a reader can judge plausibility.

*Status:* accepted. Supplier RFQs are the only fix.

---

## 3. Thermal store standby loss is omitted

**H.** B3 assumes 0.28 kWh/kg of heat is stored and all of it is available after
charging. An 8 h hold at 1500 °C with real insulation loses a significant
fraction. Ignoring it flatters B3's mass by roughly the loss fraction.

*Response:* not yet fixed. B3 is rejected on mass and volume regardless, so the
decision does not change — but the $0.301/kWh figure is optimistic.

*Status:* open, low priority while B3 is out of scope for portable use.

---

## 4. TPV heat is treated as a priced commodity

**H.** B3 assumes ≥1500 °C heat at $0.04/kWh with no co-location, delivery, or
storage hardware. That is not a portable source; it is a host facility.

*Response:* the architecture is labelled "stationary concept" in the comparison.
Its LCOE excludes the heat source.

*Status:* accepted, out of scope for the portable branch.

---

## 5. Radiator model is steady-state and optimistic

**H.** `h = 10 W/m²K` is an effective coefficient, not a measured fin performance.
Fan power is not subtracted. Transient warm-up and solar gain are absent. At
45 °C ambient with 45 °C battery coolant the model correctly refuses to run — but
a real unit would need active cooling, which adds mass and parasitic load.

*Response:* sensitivity runs h from 5–25 W/m²K and flags the 45 °C bound as
infeasible. The experiment plan includes a 40 °C soak.

*Status:* partially addressed; measurement required.

---

## 6. Diesel comparison is biased in diesel's favour

**M.** Fuel logistics, jerrycans, spill risk, emissions controls, noise
enclosure, and refuelling labour are excluded. Including them would raise C2/B1
LCOE and mass.

*Response:* stated explicitly in `economics/COST_MODEL.md`. The comparison is
therefore conservative **against** the non-diesel options.

*Status:* accepted; strengthens the conclusion that diesel is not a long-term answer.

---

## 7. Converter efficiency is not in the dispatch

**M.** The hybrid dispatch treats source power as delivered load; inverter and
converter losses (≈5%) are absent. This understates fuel by a few percent and
slightly understates heat rejection.

*Response:* fixed. Dispatch now carries the AC load as `load / 0.95` on the DC
bus, charges the loss to the energy account, and sizes the hybrid source from
average **DC** power. The cycle-3 audit then found C2 was still multiplying its
genset efficiency by the converter *and* letting dispatch divide by it again;
that double charge is removed, and the diesel part-load model is now shared with
B1. B1 is exempt because its alternator is inside the native genset efficiency.
Fuel and heat rise, as expected; the ranking does not change.

*Status:* closed. The effect is smaller than the price uncertainty.

---

## 8. Volume models are crude

**M.** B1 and B2 use ad hoc volume formulas (litres × 1.35, kW × 8/12). Radiator
and converter volume are excluded everywhere. A2's capacitor volume was missing
and has been added.

*Response:* volume is a secondary target; the mass failure is decisive for every
candidate. Volume should not be quoted as a design value.

*Status:* partially fixed. Needs a geometric build-up before any mechanical design.

---

## 9. Mass excludes multi-mission fuel, spares, and payload

**M.** B1/C2 carry one mission of fuel. A real deployment needs reserve, tools,
cables, and user payload. The 35 kg target may exclude all of those, which makes
it stricter than it looks.

*Response:* stated in the comparison. The experiment plan weighs the dry unit
separately from fuel.

*Status:* accepted. Define whether 35 kg is dry or wet before the next cycle.

---

## 10. "No architecture meets all targets" is model-specific

**M.** It holds for this mission, these eight candidates, and these inputs. It is
not a theorem. Sizing was fixed, not optimised: C2's 1.3 kW source and 0.5 kWh
buffer were chosen by rule, not by search.

*Response:* cycle 3 ran the search: 42 points per hybrid over source factor
0.9–1.5 and buffer 0.3–1.0 kWh, with a sustainability test that rejects a source
rated at exactly average load. The lightest feasible C2 is 50.3 kg at 1.1× and
0.3 kWh, $0.669/kWh — 15.3 kg above target and still 3/5. The gap is the
converter and pulse-rated pack, so optimisation saved 7.3 kg against the old
1.3×/0.5 rule but does not rescue the requirement.

*Status:* closed for this requirement set. The result is a stronger negative
finding, not a rescue.

---

## 11. Fuel-cell replacement is arbitrary

**M.** C1 replaces the stack at year 5 at 40% of capex, with no source. This is a
guess that happens to be conservative.

*Response:* listed as E0. Sensitivity on stack cost covers part of the effect.

*Status:* open; needs stack life data.

---

## 12. Sensitivity is one-at-a-time plus independent sampling

**M.** OAT ignores interactions (ambient × convection coefficient, diesel price ×
part-load efficiency). The MC samples independently and uniformly; real prices
correlate and are not uniform.

*Response:* stated in the report. OAT is for influence ranking, not probability.

*Status:* accepted. A correlated or scenario-based sampling would be better.

---

## 13. Tests verify code, not physics

**M.** 57 tests check formulas and invariants against hand calculations. A bug
that is consistently wrong in both code and test would pass.

*Response:* the validation register keeps the ceiling at E3 and lists what is
unmeasured. Independent re-derivation of the TEG and TPV formulas was done by
hand; battery and thermal models were not independently implemented.

*Status:* accepted. Only measurement raises the level.

---

## 14. Safety and emissions are out of the model

**H for deployment, not for the comparison.** CO, noise, fuel handling, LFP
thermal runaway, hydrogen embrittlement/leak, and high-temperature surfaces are
not modelled. The diesel branch is disqualified indoors by constraint, not by
calculation.

*Response:* constraint C-3, experiment safety plan, CO monitor.

*Status:* open. Any field use needs a proper safety case.

---

## 15. The strongest counter-argument

**The project may be answering a question nobody is asking.** A battery pack and
a small genset already exist, are cheaper than any custom unit, and the model
shows no path to beating both on all axes. The value of Project E so far is a
negative result: at 1 kW scale, there is no compact source that beats the
incumbents on mass, cost, and efficiency simultaneously.

*Response:* that is the finding, and it is worth recording. Continuing is only
justified if a real use case values one axis (mass, silence, no fuel logistics)
enough to pay for the others.

*Status:* accepted. The next cycle should not start with hardware until a use
case and a single dominant axis are chosen.

---

## 16. Published numbers drifted from the code

**H.** The cycle-3 audit found documents quoting a prior run (A1 87.4% vs 83.0%;
C2 47.5 kg / $0.596 vs the then-current 55.1 / $0.633) and a validation-register
note that still said converter efficiency was excluded. Numbers no current code
path reproduces are the most dangerous artefact in the repository.

*Response:* every report now stamps the run it came from; the comparison, cost
model, status and plan were regenerated from run `20261022T195415Z_920ce114`;
register item 18 and the environment-audit evidence ceiling were corrected.

*Status:* closed for this cycle. The rule is regenerate from a pinned run, not
hand-edit a table.

---

## Summary

| Severity | Count | Decision-changing? |
|---|---:|---|
| H | 7 | Only #1 and #15; the rest are scope boundaries or trust defects now closed |
| M | 8 | No — they move numbers, not the ranking |
| L | 0 | — |

The ranking (battery efficiency, diesel mass/capex, TPV $/kWh, fuel cell last on
cost) survives every attack listed. The **absolute** numbers do not deserve
confidence better than ±30%, and no number is a measurement.
