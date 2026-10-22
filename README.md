# Project E

Reduced-order energy-system research: does a compact, source-defined power unit
beat a battery pack or a diesel genset on mass, cost per delivered kWh,
efficiency, or thermal feasibility — for a fixed mission?

The fictional "Arc Reactor" is treated as ambition, not as a design. No energy is
generated without a named source, and no physical test is claimed.

## Reference mission

1 kW continuous, 6 kW pulses for 30 s every 10 min, 8 hour mission.
Targets: ≤ 35 kg, ≤ 60 L, ≤ $5,000 capex, ≤ $0.40/kWh delivered, 10-year life.

## Setup

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest -q
```

## Run

```bash
# architecture comparison for the baseline mission
.venv/bin/python -m project_e simulate --config configs/baseline.yaml

# scenario overrides
.venv/bin/python -m project_e simulate --config configs/baseline.yaml \
    --scenario configs/scenarios/conservative.yaml

# sensitivity: one-at-a-time sweeps + cost Monte Carlo
.venv/bin/python -m project_e sensitivity --config configs/baseline.yaml

# deterministic design studies: hybrid sizing grid + mission/peak scaling
.venv/bin/python -m project_e study --kind all
```

Each run creates `results/runs/<UTC timestamp>_<config hash>/` containing the
resolved config, config checksum, git commit, provenance CSV, raw architecture
table, summary JSON, plots and a Markdown report. Runs are never overwritten.

## What is modelled

| Module | Contents |
|---|---|
| `models/energy.py` | Closed energy balance, power integration, efficiency |
| `models/storage.py` | Li-ion pack (SOC, power limits, round trip, fade), supercapacitor |
| `models/thermal.py` | Conduction, convection, radiation, lumped mass, ε-NTU, pump parasitic |
| `models/conversion.py` | Carnot, TEG (ZT), heat engine, TPV parameterisation, PV derating, fuel flow |
| `simulation/dispatch.py` | Mission profile and hybrid source+buffer dispatch with closure check |
| `simulation/architectures.py` | Eight candidates in classes A (storage), B (generation), C (hybrid) |
| `economics.py` | Discounted levelized cost of delivered energy |
| `simulation/runner.py` | Reproducible pipeline and artifacts |
| `simulation/sensitivity.py` | OAT sweeps and cost Monte Carlo |

## Evidence status

- Physics tests check hand-calculated reference values and invariants (E3).
- Component parameters are labelled estimates (E0/E2), not quotations or measurements.
- No experimental validation exists. This repository does not contain a prototype.

## Repository layout

```
configs/       baseline and scenario configurations with provenance
src/project_e/ models and simulation code
tests/         analytical and numerical verification
research/      verified source registry and literature review
reports/       environment audit, status, sensitivity, red-team review
docs/          requirements, architecture comparison, plan
validation/    model validation register
experiments/   smallest decisive experiment plan
economics/     cost model and incumbent comparison
results/runs/  immutable run artifacts
```

## Ground rules

- Every physical quantity carries a unit; invalid inputs are rejected.
- Energy balances are asserted, not assumed.
- A passing software test is not physical validation.
- Estimates are labelled; no fabricated citations, quotes, or measurements.
