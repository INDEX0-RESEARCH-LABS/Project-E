# Cost model and incumbent comparison

**Model:** `src/project_e/economics.py` (`CostStreams`)
**Cost basis:** USD, 2026, no currency conversion, no inflation
**Mission:** 10 kWh delivered per mission, 250 missions/year (baseline)

All prices are assumptions. None is a quotation. The evidence level of each is
stated in `configs/baseline.yaml` and summarised in
`validation/MODEL_VALIDATION_REGISTER.md`.

---

## 1. Formulation

Levelized cost of delivered energy:

```
LCOE = Σ_t [ C_t / (1+r)^t ]  /  Σ_t [ E_t / (1+r)^t ]
```

with `t = 0 … N`, capex at t = 0, and

```
C_t = O&M_annual + fuel_annual + replacement_t
E_t = delivered_kWh_per_year
```

- `r` = real discount rate (baseline 8%).
- Replacements are placed in a specific year, not smeared.
- Battery replacement year comes from the same fade model used for sizing:
  `decay/yr = 0.20 × missions/yr ÷ cycle_life + 0.01`; replacement when
  cumulative fade reaches 20%.
- The fuel-cell hybrid includes a stack replacement at year 5 at 40% of stack
  capex.
- The denominator is delivered energy, so a unit that fails to serve load is not
  rewarded with a lower LCOE (unmet load is asserted to zero in sizing).

This is a **levelized cost**, not a price and not a profit model. It excludes
taxes, financing structure, warranty, logistics, and end-of-life.

---

## 2. Cost elements by architecture

| Element | A1/A2 battery | B1 diesel | B3 TPV | B4/C1 fuel cell | C2 diesel hybrid |
|---|---|---|---|---|---|
| capex | pack + converter | genset at 6 kW | cells + store + emitter | stack + tank | genset + buffer + converter |
| fuel | grid electricity | diesel | external heat | hydrogen | diesel |
| O&M | none modelled | $0.02/kWh | none | none | $0.02/kWh |
| replacement | pack at fade year | none | none | stack at year 5 (C1) | buffer at fade year |

A2 adds capacitor capex and converter cost. B2 adds TEG modules at $5/W electric.
Capacitor and TEG costs are the weakest numbers in the model (E0).

---

## 3. Inputs that dominate

| Input | Baseline | Range | Evidence | Effect on LCOE |
|---|---:|---|---|---|
| Missions per year | 250 | 100–350 | E0 | up to $2.68/kWh across all candidates |
| Diesel price | $1.40/L | 1.00–2.20 | E0 | up to $1.24/kWh (C2/B1) |
| Battery price | $300/kWh | 180–450 | E0 | up to $0.19/kWh (A1) |
| Hydrogen price | $6.00/kg | 3–12 | E0 | up to $0.36/kWh (C1) |
| Fuel-cell stack | $3,500/kW | 1,800–6,000 | E0 | up to $0.89/kWh (C1/B4) |
| Heat price | $0.04/kWh | 0–0.12 | E0 | up to $0.29/kWh (B3) |
| Discount rate | 8% | 4–12% | E0 | up to $0.34/kWh |
| Lifetime | 10 a | 5–15 a | E0 | up to $1.22/kWh |

The first row is not a component at all: **utilisation dominates**. A unit that
runs 100 missions/year costs roughly 1.5–2× more per kWh than one that runs 500.
That is a deployment question, and it cannot be answered by better hardware.

---

## 4. Incumbent comparison under the same mission

| Option | Mass kg | Capex USD | LCOE $/kWh | Meets mission? | Notes |
|---|---:|---:|---:|---|---|
| A1 battery only | 113.2 | 4,647 | 0.583 | energy yes, mass no | needs 825 Wh/kg for 35 kg |
| B1 diesel genset, 6 kW | 129.8 | 2,400 | 1.199 | energy yes, mass no | one mission of fuel; 13.6% avg efficiency |
| C2 diesel + battery | 47.5 | 1,150 | 0.596 | energy yes, mass 12.5 kg over | closest to mission |
| C1 fuel cell + battery | 55.0 | 6,080 | 0.801 | energy yes, mass 20 kg over | H2 supply dependency |
| Grid extension | not modelled | — | $0.15/kWh (assumed tariff) | site-dependent | not portable; excluded |

The honest incumbent for a portable 1 kW / 6 kW mission is **C2 or B1**, not a
laboratory fuel cell. Project E does not beat them today.

Note what the comparison does **not** include: diesel storage and transport,
refuelling labour, emissions controls, noise enclosures, or the cost of carrying
spare fuel for more than one mission. Those would make diesel look worse; they
are omitted, which biases the comparison **in diesel's favour**.

---

## 5. Break-even thresholds

Solved by bisection on the full model, all else at baseline:

| Question | Threshold | Baseline | Interpretation |
|---|---:|---:|---|
| Battery price for A1 ≤ $0.40/kWh | $157/kWh | $300/kWh | pack must be 48% cheaper |
| Diesel price for C2 ≤ $0.40/kWh | $0.85/L | $1.40/L | fuel must be 39% cheaper |
| Hydrogen price for C1 ≤ $0.40/kWh | not reachable | $6.00/kg | floor is $0.441/kWh even at $0/kg |
| Heat price for B3 ≤ $0.40/kWh | $0.070/kWh | $0.04/kWh | already met |
| Missions/year for A1 ≤ $0.40/kWh | 500/yr | 250/yr | doubles utilisation |
| Missions/year for B3 ≤ $0.40/kWh | 150/yr | 250/yr | TPV is already below target per kWh |
| Battery specific energy for 35 kg | ~825 Wh/kg | 175 Wh/kg | 4.7× beyond current Li-ion packs |

### Utilisation sensitivity

| Missions/year | A1 | B3 | C2 | C1 |
|---:|---:|---:|---:|---:|
| 100 | 0.864 | 0.500 | 0.694 | 1.451 |
| 250 | 0.583 | 0.288 | 0.596 | 0.801 |
| 500 | 0.395 | 0.218 | 0.560 | 0.544 |

C2 improves only slowly with utilisation because fuel, not capex, dominates.
A1 crosses the target only at ~500 missions/year. That is 10 missions/week for
10 years — a utilisation assumption that must be justified by a real duty cycle,
not assumed.

---

## 6. What is missing from the cost model

1. **No logistics.** Fuel transport to a remote site, jerrycans, and storage are
   excluded. For diesel this is material and would raise C2/B1 LCOE.
2. **No emissions or noise cost.** Indoor disqualification is treated as a
   constraint, not priced.
3. **No hydrogen supply chain.** Production, compression, and boil-off are
   outside the boundary.
4. **No volume or mass penalty in cost.** A 244 kg TPV unit can still show a low
   $/kWh; the mass target is applied separately.
5. **No learning curve or volume pricing.** All prices are single-unit estimates.
6. **No financing, tax, warranty, or end-of-life.**
7. **Uniform independent distributions** in the Monte Carlo; real prices
   correlate and are not uniform.

These omissions are stated so that no reader treats the LCOE column as a
purchasable price.

---

## 7. Conclusion

- The battery is the cheapest per kWh only if utilisation is high and the mass
  target is abandoned.
- The diesel hybrid is the cheapest to buy and the lightest, but its fuel sets a
  hard floor near $0.50/kWh — above the $0.40 target at any plausible diesel
  price in this range.
- The fuel-cell hybrid cannot reach the target even with free hydrogen, because
  stack capex and replacement dominate.
- TPV is the only candidate that meets the LCOE target at baseline, and it does
  so by ignoring the mass and heat-supply constraints that define the mission.

**No cost assumption within the declared ranges makes a portable candidate meet
all targets.** The blocking constraints are mass (battery), fuel price (diesel),
and capex (hydrogen). Those are the three things a next-cycle experiment or
supplier enquiry should attack — in that order.
