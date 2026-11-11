# Concept — SUS-I1 Operations, Architecture and Trade Studies

> **Status:** Unapproved concept (CONOPS rev 0.3-draft, architecture v0.2). Diagrams show proposed
> structure and behaviour only. No component, safe state, threshold or trade-study outcome has been
> selected or verified.

| Field | Value |
|---|---|
| Lifecycle gate | G0 (Concept) feeding G1–G2 |
| Accountable role | Systems lead |
| Documentation standard | [`framework/documentation-standard.md`](../framework/documentation-standard.md) |
| Analysis baseline | [`safety/mil-std-882e/00-system-definition`](../safety/mil-std-882e/00-system-definition/README.md) |

## Purpose

Defines what Susanoo is for and how it is meant to be used, before design commitments are made:
missions, operating modes and scenarios ([CONOPS](CONOPS.md)), the preliminary decomposition and
controlled interfaces ([architecture](architecture.md)), and the open actuation, pilot, locomotion
and docking alternatives ([trade studies](trade-studies.md)). These documents are the primary inputs
to the PHL, PHA and FHA in the MIL-STD-882E tree.

## Block diagram

Preliminary decomposition from [`architecture.md`](architecture.md). Dashed outline = subject of an open
trade study (TS-xxx).

![Figure 1 · Block diagram](figures/fig-1-block-diagram.svg)

## Boundary diagram

System boundary per CONOPS section 2. Numbered crossings match the table.

![Figure 2 · Boundary diagram](figures/fig-2-boundary-diagram.svg)

| # | From | To | Crossing |
|---|---|---|---|
| 1 | Pilot | SUS-M1 | Commands, emergency intervention |
| 2 | SUS-M1 | Pilot | Status, alarms, UAV video |
| 3 | Safety observer | SUS-I1 | Exclusion zone, intervention |
| 4 | Mission supervisor | SUS-I1 | Operational limits |
| 5 | Maintainer | SUS-GSE | Isolation and service |
| 6 | Terrain, weather | SUS-M1 | Ground loads, weather |
| 7 | Airspace, GNSS, RF | SUS-A1 | Navigation, link |
| 8 | SUS-M1 | Personnel and bystanders | Motion envelope, crush zones |
| 9 | SUS-A1 | Personnel and bystanders | Rotor and impact hazards |

**Explicitly excluded:** weapons or armament, amphibious mobility, authorized human-occupied operation
(requires separate review and test authorization).

## SysML model

SysML v2 textual model: [`ConceptOperations.sysml`](ConceptOperations.sysml) — the CONOPS operating
modes as a state machine and the nominal scenarios as use cases. It imports
[`SusanooSystem`](../safety/mil-std-882e/00-system-definition/sysml/SusanooSystem.sysml). The `.sysml`
file is the model of record; Figure 3 is drawn directly from it, so the figure cannot drift from the model.
[Task 206 (O&SHA)](../safety/mil-std-882e/02-hazard-identification/task-206-operating-and-support-hazard-analysis/README.md)
analyses the same state machine.

![Figure 3 · SysML state machine — operating modes](figures/fig-3-sysml-state-machine.svg)

![Figure 4 · SysML use cases — nominal scenarios](figures/fig-4-sysml-use-cases.svg)

## Inputs and outputs

![Figure 5 · Inputs and outputs](figures/fig-5-inputs-and-outputs.svg)

| Input | Source |
|---|---|
| Missions, users, constraints | Stakeholder needs (not yet formally captured) |
| Assurance approach | [`framework/standards-applicability.md`](../framework/standards-applicability.md) |

| Output | Destination |
|---|---|
| Modes and scenarios | [Task 201 PHL](../safety/mil-std-882e/02-hazard-identification/task-201-preliminary-hazard-list/README.md), [Task 206 O&SHA](../safety/mil-std-882e/02-hazard-identification/task-206-operating-and-support-hazard-analysis/README.md) |
| Decomposition and interfaces | [00 System definition](../safety/mil-std-882e/00-system-definition/README.md) |
| System functions | [Task 208 FHA](../safety/mil-std-882e/02-hazard-identification/task-208-functional-hazard-analysis/README.md) |
| Candidate requirements SYS-001..006 | [Task 203 SRHA](../safety/mil-std-882e/02-hazard-identification/task-203-system-requirements-hazard-analysis/README.md) |
| Flight-control candidate | [`integrations/px4`](../integrations/px4/README.md) |

## Folder contents

| Item | Description | State |
|---|---|---|
| [`CONOPS.md`](CONOPS.md) | Missions, modes, scenarios, human factors, candidate requirements | present |
| [`architecture.md`](architecture.md) | Preliminary decomposition, interfaces, safety principles | present |
| [`trade-studies.md`](trade-studies.md) | TS-001..TS-004, no winners selected | present |
| [`ConceptOperations.sysml`](ConceptOperations.sysml) | SysML v2 modes and scenarios | present |
| [`figures.yaml`](figures.yaml) | Figure specs; render with `python3 tools/figures/build_figures.py` | present |
| [`figures/`](figures/) | Generated SVG figures (do not edit) | generated |
