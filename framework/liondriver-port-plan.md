# Porting LionDriver's modeling, diagram and simulation approach to Susanoo

**Status:** Plan, 2026-11. Step 1 in work. Source reviewed: [jherrodthomas/LionDriver](https://github.com/jherrodthomas/LionDriver) at `93bafc3` (`assurance/`, `.claude/skills/`, `.github/workflows/`).

LionDriver is an ISO 26262 / ISO 21448 assurance effort on an openpilot fork. Susanoo uses MIL-STD-882E (11 May 2012) on a piloted walker and a PX4 UAV. The standards and the physics differ. The **method** ports almost unchanged.

## 1. The rule LionDriver runs on

> The work-product records are the source of truth. Every model file, diagram, simulation result and page is generated from them by a script with `--check`, and CI fails when anything drifts.

The supporting conventions:
- **Tooling:** standard-library Python wherever possible, with byte-deterministic output. A digest of the records replaces timestamps.
- **Stale or unexpected inputs:** every generator has `--check` and a test, and raises an error on an unknown value instead of guessing.
- **Figures:** every label is read from a record, and hand-listed facts quote a phrase from their source, so rewording the source fails the build.
- **Simulation:** every result is labelled *synthetic, no evidence credit* until a fidelity case is approved for that scenario family.
- **Acceptance:** only a recorded human review accepts anything. CI passing, test results, the existence of a file or an AI review never do.
- **Decisions:** questions for the project lead live in a register, written so each one stands alone and asked in batches of about ten.

Susanoo already follows the first two conventions: `tools/pdac` validates the records and `report --check` keeps the generated pages current.

## 2. What LionDriver has, and what we take

| Area | LionDriver | Take for Susanoo | Replace |
|---|---|---|---|
| Boundary and context diagrams | Item definition kept as tables. `fig_c01_*.py` generators. The hand-drawn boundary SVGs are being retired in favour of SysML views | Boundary records plus generated context and boundary figures, with layout kept as data and checked against the record IDs | Automotive elements (CAN, panda, EPS) |
| Figure kit | `figkit.py` (palette, header, legend, table parsers, `FigureError`), `terms.py` definitions footer, templates with tests | `tools/figures/figkit.py` in the same style | Palette and brand |
| SysML v2 | 17 `.sysml` files, a stdlib reader (`sysml_lite.py`), `check_model.py` rule families M/N/B/H/R, 28 views from `layout.toml`, an offline explorer page, OMG pilot conformance validation | The same machinery. Library rewritten in 882E terms: risk level, SCC, SwCI, `@Source`, `@Hazard` | ISO 26262 vocabulary (ASIL, FFI, FTTI); AUTOSAR export |
| 2D scenes | `scenekit.py` and `.js`: one ego, dashed green for what should happen, solid red for what does, fault marker, 6 s loop | Two kits: a side-view walker and a top-down dock/UAV approach | Road geometry |
| Plant simulation | Bicycle model with the real safety C code in the loop, `faults.yaml` traced to FMEA, FMU packaging | Reduced-order walker (stance plus lumped hydraulics, pilot reaction), walker interlock logic in the loop, `faults.yaml` traced to HAZ IDs | Vehicle dynamics; panda code |
| Scenarios | OpenSCENARIO/OpenDRIVE, esmini replay | YAML terrain-and-mission scenarios: slope, step, soft ground, wind, dock approach, link loss | No legged-terrain standard exists |
| Failure search | `families.yaml`, Monte Carlo then cross-entropy search for worst cases. Each worst case is re-run without the fault and with each assumption changed, then mapped to HE/SH; unmatched cases become findings | Same method. Robustness measures: stability margin, residual pressure, tip angle, distance to people, UAV separation, geofence and battery margins | HARA mapping replaced by HAZ and RAC mapping |
| UAV simulation | (none) | PX4 SITL: the built-in SIH simulator headless in CI if practical; Gazebo on a self-hosted runner, gated as LionDriver gates MetaDrive | — |
| Higher-fidelity dynamics | Project Chrono (built from source, about 80 CPU-min) | MuJoCo (pip install, CPU) as the default, to be decided | Chrono |
| 3D | Blender `scenes.yaml`: 67 scenes, 125 with variants. Dashboards and gallery. A test proves that changing the look never changes the analysis. Single-file three.js `machine` kit | `scenes.yaml` per hazard, parametric walker model, `machine`-kit cutaway pages fed only from results JSON | Purchased car mesh. Susanoo is an original design, so we build the model from our own spec |
| Fault models | fmdtools sweeps cross-checked with fault trees; FRET formalisation of requirements | fmdtools for the walker and dock chains; FRET for PX4 failsafes and dock interlocks | — |
| Assurance backbone | Case records (claims, evidence, defeaters), review records, accept-only-by-review rule (V6), decision register and inbox, clause register, a known-findings list that may only shrink, `CLAUDE.md` and 11 skills | Review records plus the accept-only-by-review rule, decision register, `CLAUDE.md`. Later: a findings list that may only shrink, case records and GSN | ASIL/HARA rules, ASPICE map, document-control workflow |

**Do not copy the scale.** LionDriver's `assurance.yaml` is 992 lines with about 144 `--check` steps. Port the smallest slice of each piece, and add more only when there is content to check.

## 3. Steps

### Step 1: Foundation (in work)
1. **Figure kit** `tools/figures/figkit.py`, stdlib only, with tests.
2. **Item definition records** in `architecture/item-definition.yaml`: functions, elements inside the boundary, external elements, and interfaces. This merges the wiki IF-001..008 register and the PX4 IF-PX4-001..009 contract.
3. **Validator rules** to keep the records consistent:
   - IDs are unique, parents exist, and interface endpoints resolve.
   - Every hazard subsystem, event subsystem and requirement allocation names a real element.
   - Every element and every external element has an interface.
   - Every function is performed by some element.
4. **Generated figures:** a context figure and a boundary figure, from the record plus a layout file checked against its IDs, each with `--check` and a test. Retire the four `docs/diagrams/architecture/*.drawio` files.
5. **Review records** (`reviews/REV-YYYY-NNN.yaml`) and the rule that a risk acceptance, an approved task record, a baselined requirement or an approved tailoring needs an accepting review by a human in the right role. An AI review is independence level I0 and never accepts.
6. **Decision register** `decisions/register.yaml`: checker plus a generated inbox page.
7. **`CLAUDE.md`:** decision rules, and a table of what the AI may and may not do.

### Step 2: SysML core
Port `sysml_lite.py` and the library in 882E terms. Hand-write `Architecture.sysml`. Generate `Requirements.sysml` and `Satisfaction.sysml` from `requirements/` and `safety/hazards/`. Port model checks M1 (elements), M4 (interfaces), M7 (risk level on every element), M9 (functions), and R1–R3. Views: V-01 context, V-02 hierarchy, V-03 IBD, V-08 N2, then the CONOPS mode state machine (MOD-01..10) and the VCRM. Add a CI job that runs OMG pilot validation. The SysML context view then replaces the step 1 context figure.

### Step 3: 2D simulation
Build the walker plant, `faults.yaml` and `report --check` with synthetic-labelled results. Then one search family (pressure loss mid-stride on a slope), with edge cases mapped to hazards and unmatched cases turned into findings. Then 2D scenes for the Catastrophic and Critical hazards, and the evidence-gate section stating that there is no credit without an approved fidelity case.

### Step 4: UAV and fidelity
PX4 SITL failsafe checks (lost link, geofence, battery, dock approach, abort). MuJoCo legged dynamics as fidelity level 2, cross-checked against the plant.

### Step 5: 3D
`scenes.yaml` with one scene per hazard, plus the test that changing the look never changes the analysis. Blender stills and clips, or `machine`-kit pages, fed only from the results.

## 4. Findings so far
- **The power and actuation baseline is inconsistent.** `README.md` and the seeded hazards assume hydraulic actuation. The wiki architecture page assumes a series-hybrid engine-generator with batteries and electric or electrohydraulic joints. Trade study TS-001 covers actuation but not the power source. This is decision DQ-006.
- The four architecture draw.io files are not traced to any record, and none has an exported image. The Mermaid blocks on the wiki page are the only rendered versions.
- Two interface registers (IF-001..008 and IF-PX4-001..009) overlapped without cross-references.
