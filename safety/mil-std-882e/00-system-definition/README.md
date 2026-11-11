# 00 · System Definition and Analysis Baseline

> **Status:** Scaffold v0.1 — structure, diagrams and model views only
>
> Planning artifact. No completed hazard analysis, verified mitigation, risk acceptance, certification or MIL-STD-882E compliance is claimed. Category names follow MIL-STD-882E; confirm definitions against the controlled standard and the approved SSPP before formal use.

| Field | Value |
|---|---|
| Lifecycle gate | G0 (refreshed at every gate) |
| Accountable role | Systems lead with safety lead |
| Parent folder | [MIL-STD-882E System Safety Work Products](../README.md) |

## Purpose

Defines the system of interest, its decomposition, interfaces and external context that every
hazard analysis uses as its baseline. Holds the canonical SysML v2 models: `SusanooSystem`
(structure, ports, dock interface) and `SusanooSafety` (severity, probability, risk, SwCI,
mitigation precedence, hazard record). Per-folder SysML views import these packages.

## Position in the MIL-STD-882E flow

![Figure 1 · Position in the MIL-STD-882E flow](figures/fig-1-position-in-the-mil-std-882e-flow.svg)

## Block diagram

![Figure 2 · Block diagram](figures/fig-2-block-diagram.svg)

Source of truth: [`SusanooSystem.sysml`](sysml/SusanooSystem.sysml).

## Boundary diagram

![Figure 3 · Boundary diagram](figures/fig-3-boundary-diagram.svg)

| # | From | To | Crossing / interaction |
|---|---|---|---|
| 1 | EXT-PILOT: Pilot / operator | SUS-M1: Piloted walker | intent / alerts |
| 2 | EXT-CREW: Ground crew & maintainers | SUS-GSE: Ground support equipment | servicing / lockout |
| 3 | SUS-GSE: Ground support equipment | SUS-M1: Piloted walker | support / charging |
| 4 | SUS-M1: Piloted walker | SUS-A1: Observation UAV | dock power, data, retention |
| 5 | SUS-M1: Piloted walker | EXT-TERRAIN: Terrain & obstacles | foot contact loads |
| 6 | SUS-M1: Piloted walker | EXT-BYST: Bystanders & nearby workers | motion envelope |
| 7 | EXT-AIR: Airspace, GNSS & RF environment | SUS-A1: Observation UAV | GNSS / RF link |
| 8 | EXT-SITE: Site infrastructure & logistics | SUS-GSE: Ground support equipment | fuel, power, transport |
| 9 | SUS-M1: Piloted walker | EXT-ENV: Natural environment & receptors | exhaust, noise, fluids |

**Explicitly excluded:** weapons or armament of any kind; public-road operation; autonomous walker operation without a pilot

## SysML model

Canonical SysML v2 textual models (model of record for every folder in this tree): [`SusanooSystem.sysml`](sysml/SusanooSystem.sysml), [`SusanooSafety.sysml`](sysml/SusanooSafety.sysml).

![Figure 4 · SysML block definition — SUS-I1 system breakdown](figures/fig-4-sysml-block-definition.svg)

## Inputs and outputs

![Figure 5 · Inputs and outputs](figures/fig-5-inputs-and-outputs.svg)

| Input | Source |
|---|---|
| Missions, phases, users | [`concept/CONOPS.md`](../../../concept/CONOPS.md) |
| Decomposition and interfaces | [`concept/architecture.md`](../../../concept/architecture.md) |
| Power, control and dock diagrams | [`docs/wiki/SUS-M1-Architecture-and-Boundaries.md`](../../../docs/wiki/SUS-M1-Architecture-and-Boundaries.md) |
| Configuration ID SUS-I1-C001 | [`pdac/product.yaml`](../../../pdac/product.yaml) |

| Output | Destination |
|---|---|
| Analysis baseline | [02 · Identify and Document Hazards](../02-hazard-identification/README.md) |
| Software-controlled functions | [Software Contribution to System Risk (Section 4.4)](../software-safety/README.md) |
| Subsystem IDs for hazard records | [Task 106 · Hazard Tracking System (Hazard Log)](../hazard-tracking-system/README.md) |

## Folder contents

| Item | Description | State |
|---|---|---|
| [`sysml/SusanooSystem.sysml`](sysml/SusanooSystem.sysml) | Canonical structure model (parts | present |
| [`sysml/SusanooSafety.sysml`](sysml/SusanooSafety.sysml) | Canonical safety vocabulary (enums | present |
| `interface-register.csv` | Controlled interface list with hazard links | planned |
| [`figures/`](figures/) | Generated SVG figures (do not edit) | generated |

<!-- END GENERATED: content below this line is human-authored and preserved -->

## Working content

_No analysis content yet. Add authored material below this heading._
