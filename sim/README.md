# Simulation track

Simulation for SUS-I1, following LionDriver's architecture (`assurance/sim`). Each piece of code sits next to the results it writes, and every output is checked in CI with `--check`: the committed file must equal a fresh run. Everything here uses only the Python standard library plus PyYAML. It is deterministic and seeded, and the whole track runs in a few seconds.

## Evidence gate

**Simulation results here carry no evidence credit.** Every result is labelled `data_kind: synthetic` and *no evidence credit*. A result can count toward verification only after two things happen:
1. a fidelity case is approved for its scenario family, by a review record under rule R13;
2. the safety lead takes it into the owning analysis.

Until then, results rank risks, find edge cases and guide tests. They never close a hazard, verify a mitigation or support a risk acceptance. The AI may not mark simulation results as verification evidence (`CLAUDE.md`).

## Layers

| Layer | Where | Status | What it does |
|---|---|---|---|
| Spec | `spec/walker.yaml` | built | Plant parameters. Each one has a unit, an allowed range, a status (assumed, derived or published) and a source. `plant/spec.py` refuses a value that is unsourced or out of range. |
| Faults | `faults.yaml` | built | FLT-01 hydraulic supply loss, FLT-02 frozen posture feedback, FLT-03 protective stop with zero torque, FLT-04 electric undervoltage. Each traces to hazard causal factors (`HAZ-x:CFn`), checked to exist. |
| 1 · Plant | `plant/walker.py` | built | Reduced-order sagittal walker with stated assumptions A1–A7: a linear inverted pendulum, a force-controlled leg, an actuator capacity fraction, load holding, a protective stop and a pilot reaction model. The hydraulic and electric variants stay open until decision DQ-006. |
| 1 · Report | `plant/report.py` | built | Runs every fault on 0° and 8° slopes, with and without its mitigations, plus the no-fault capability by slope. Writes `results/plant-results.md` and `.json`. |
| 4 · Search | `search/families.yaml`, `search/search.py` | built (1 family) | Seeded Monte Carlo, then cross-entropy falsification. Each worst case is re-run three ways: with rounded parameters, with no fault, and under assumption probes. It is then mapped to a hazard, or raised as a finding. Writes `results/search-SF-01.*` and `results/edge-cases.md`. |
| Scenes | `figures/scenes.py` | built | Animated 2D side views from plant runs: intended run as dashed green, performed run as solid red. The static pose is the end state. Writes `docs/wiki/images/sim-sc-*.svg` and the wiki page `docs/wiki/Simulation.md`. |
| 2 · Scenarios | — | planned | Terrain and mission scenarios as data (slope, step, soft ground, wind, dock approach, link loss). |
| UAV | — | planned (step 4) | PX4 SITL failsafes: lost link, geofence, battery, dock approach and abort. |
| Fidelity | — | planned (step 4) | Multibody legged dynamics (MuJoCo proposed, decision DQ-007), cross-checked against the plant. |
| 3D | — | planned (step 5) | `scenes.yaml` per hazard, with a test that changing the look never changes the analysis. |

## Commands

```bash
python -m sim.plant.report          # fault catalogue runs
python -m sim.search.search         # failure search (SF-01)
python -m sim.figures.scenes        # 2D scenes and docs/wiki/Simulation.md
python -m unittest discover -s sim/tests -t .
```

Each command accepts `--check`, which fails if its committed outputs are stale. Run them in the order above, because the scenes read the search results.

## Honesty rules for scenes and results

- Contact, rotation after tipping and terrain compliance are not modelled. A run stops at the first mishap, and its scene freezes there.
- Every scene is drawn from plant runs. Nothing is hand-animated. Each scene names its hazard or finding, its case, and the synthetic label.
- A finding is a draft for the safety lead. A new hazard or causal factor enters `safety/hazards/` only through review.
- Parameter values are concept assumptions, not design values. Changing one changes the results, and the `--check` steps make that visible in review.
