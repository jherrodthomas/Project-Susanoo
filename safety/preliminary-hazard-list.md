# Preliminary Hazard List (PHL) — SUS-M1 / SUS-A1

**ID:** SUS-PHL-001 · **Revision:** 0.3-draft · **Status:** Draft, not reviewed

<!-- GENERATED PAGE: written by tools/pdac/generate.py from pdac/items/hazards.yaml. Edit the records, then regenerate. -->

> **Generated from [`pdac/items/hazards.yaml`](../pdac/items/hazards.yaml)** (author: Claude (AI-drafted), independence I0, 2026-11-11).
> Every rating below is a **proposed initial risk**, before mitigation, made from the concept description alone. None has been reviewed by the safety lead, and **no risk has been accepted**. This list is an input to the Preliminary Hazard Analysis, not a substitute for it.

## 1. Method

The Preliminary Hazard List follows the MIL-STD-882E system safety method used as the project's integrated safety method ([standards applicability](../framework/standards-applicability.md)). Hazards were identified from the operating modes and scenarios of the [CONOPS](../concept/CONOPS.md) and from each energy source the concept contains: hydraulic pressure, stored mechanical energy, gravity (an elevated, legged platform), kinetic energy of limbs and payloads, rotor energy, electrical energy, heat and battery chemistry.

Each hazard is rated for its **worst credible mishap** with a severity category and a probability level, and the MIL-STD-882E risk assessment matrix gives the risk level. The validator recomputes every risk level from the matrix (check P5). Hazards that depend on an open trade study are rated for the alternative with the highest energy; they are re-rated when the study decides.

These are MIL-STD-882E ratings only. Aircraft failure conditions of the SUS-A1 UAV are classified separately with ARP4761A in its Functional Hazard Assessment and are never converted to or from these levels.

## 2. Summary

23 hazards: **9 high**, **10 serious**, **4 medium**.

*Hazard count per cell of the MIL-STD-882E risk assessment matrix (initial risk). Each cell shows the risk level the matrix assigns.*

| Probability \ Severity | Catastrophic | Critical | Marginal | Negligible |
|---|---|---|---|---|
| Frequent | High | High | Serious | Medium |
| Probable | High · **1** | High | Serious | Medium |
| Occasional | High · **8** | Serious · **5** | Medium · **1** | Low |
| Remote | Serious · **5** | Medium · **3** | Medium | Low |
| Improbable | Medium | Medium | Medium | Low |

## 3. Hazard list

| ID | Hazard | Worst credible mishap | Energy | Exposed | Scenarios | Initial risk | Candidate mitigations | Depends on |
|---|---|---|---|---|---|---|---|---|
| HAZ-001 | Uncommanded or runaway joint motion | A leg or arm strikes or crushes the pilot, the observer or a bystander. | kinetic, hydraulic-pressure, electrical | pilot, safety observer, bystander | SCN-101, SCN-002 | **High** (catastrophic, occasional) | SYS-002, SYS-004 | — |
| HAZ-002 | Unexpected actuation during ingress, startup or standby | The walker moves while the pilot is entering or a crew member is next to it. | kinetic, hydraulic-pressure, electrical | pilot, maintainer, safety observer | SCN-001 | **High** (catastrophic, occasional) | SYS-001 | — |
| HAZ-003 | High-pressure fluid injection or spray | Fluid jet penetrates skin or eyes of the pilot or crew. | hydraulic-pressure | pilot, maintainer, safety observer | SCN-102 | **Serious** (critical, occasional) | SYS-007, SYS-018 | TS-001 |
| HAZ-004 | Release of stored energy during maintenance or egress | A limb drops or moves, or a component releases pressure or charge, while a person is in contact. | hydraulic-pressure, gravitational, stored-mechanical, electrical | maintainer, pilot | SCN-102, SCN-006 | **High** (catastrophic, occasional) | SYS-007 | — |
| HAZ-005 | Uncontrolled descent or collapse on loss of actuation energy | The walker collapses with the pilot aboard or onto nearby personnel. | gravitational | pilot, safety observer, bystander | SCN-102, SCN-103 | **High** (catastrophic, occasional) | SYS-008 | TS-001 |
| HAZ-006 | Loss of balance, fall or overturn with the pilot aboard | The walker falls or rolls over; the pilot is injured by impact, or the walker lands on personnel. | gravitational, kinetic | pilot, safety observer, bystander | SCN-103, SCN-002 | **High** (catastrophic, probable) | SYS-004, SYS-009, SYS-010 | TS-002, TS-003 |
| HAZ-007 | Pilot incapacitation without transition to a safe state | The walker keeps moving or holds an unsafe posture after the pilot stops controlling it. | kinetic, gravitational | pilot, safety observer, bystander | SCN-104 | **Serious** (catastrophic, remote) | SYS-011 | — |
| HAZ-008 | Blocked or delayed emergency egress or extraction | The pilot cannot leave, or cannot be removed, during fire, injury or after a fall. | gravitational, thermal | pilot | SCN-104, SCN-108 | **Serious** (catastrophic, remote) | SYS-012, SYS-019 | TS-002 |
| HAZ-009 | Crushing or striking of personnel in the walking or manipulation envelope | A person inside the envelope is stepped on, struck or pinned. | kinetic, gravitational | safety observer, bystander, maintainer | SCN-002, SCN-003 | **High** (catastrophic, occasional) | SYS-002, SYS-013 | — |
| HAZ-010 | Payload drop, overload or loss of grip | A payload falls on personnel or destabilizes the walker. | gravitational | safety observer, bystander, pilot | SCN-003 | **Serious** (critical, occasional) | SYS-009, SYS-013 | — |
| HAZ-011 | Unexpected rotor start while the UAV is retained or handled | Rotor blades strike the pilot or a maintainer. | rotor-kinetic | pilot, maintainer | SCN-107 | **Serious** (critical, occasional) | SYS-003, SYS-005 | — |
| HAZ-012 | UAV collision with the walker, pilot or personnel during launch or recovery | The UAV or its rotors strike a person or the pilot station. | rotor-kinetic, kinetic | pilot, safety observer, bystander | SCN-004, SCN-005, SCN-106 | **Serious** (critical, occasional) | SYS-006 | TS-004 |
| HAZ-013 | Docking retention failure or unintended release | The UAV falls from the dock or is released while the walker moves. | gravitational, kinetic | pilot, safety observer, bystander | SCN-005, SCN-106 | **Medium** (critical, remote) | SYS-005 | TS-004 |
| HAZ-014 | UAV lost link or fly-away leaving the operating area | The UAV strikes people or property outside the controlled area. | kinetic, rotor-kinetic | bystander | SCN-105 | **Serious** (critical, occasional) | SYS-014 | — |
| HAZ-015 | Misleading UAV imagery or telemetry leading to pilot error | The pilot acts on stale or wrong information and moves the walker into a person or hazard. | kinetic | pilot, safety observer, bystander | SCN-105 | **Medium** (critical, remote) | SYS-015 | — |
| HAZ-016 | Pilot distraction or overload while the walker moves during UAV operations | The walker strikes a person or loses balance while the pilot attends to the UAV. | kinetic, gravitational | pilot, safety observer, bystander | SCN-004, SCN-105 | **High** (catastrophic, occasional) | SYS-006, SYS-016 | — |
| HAZ-017 | Battery thermal runaway, fire or toxic gas near the pilot | The pilot is burned or overcome by smoke or gas. | chemical, thermal | pilot, maintainer | SCN-108 | **Serious** (catastrophic, remote) | SYS-012, SYS-017 | — |
| HAZ-018 | Electric shock from high-voltage power distribution | The pilot or a maintainer contacts an energized conductor. | electrical | maintainer, pilot | SCN-108 | **Serious** (catastrophic, remote) | SYS-017 | TS-001 |
| HAZ-019 | Contact burns from hot surfaces | The pilot or a maintainer touches a hot pump, motor, manifold or battery case. | thermal | pilot, maintainer | SCN-108 | **Medium** (marginal, occasional) | SYS-017 | — |
| HAZ-020 | Hydraulic fluid fire | Sprayed or leaked fluid ignites near the pilot station. | chemical, thermal, hydraulic-pressure | pilot, maintainer | SCN-102, SCN-108 | **Serious** (catastrophic, remote) | SYS-018 | TS-001 |
| HAZ-021 | Protective or emergency stop causes collapse or uncontrolled posture change | Stopping by removing all actuator torque drops a statically unstable walker with the pilot aboard. | gravitational | pilot, safety observer, bystander | SCN-101, SCN-103 | **High** (catastrophic, occasional) | SYS-002, SYS-008 | — |
| HAZ-022 | Crushing under the pod or legs while lowering to or rising from the kneel posture | A crew member or bystander beside or under the walker is pinned by the descending pod or folding legs. | gravitational, kinetic, hydraulic-pressure | safety observer, maintainer, bystander | SCN-001, SCN-006 | **High** (catastrophic, occasional) | SYS-019 | — |
| HAZ-023 | Fall from height during emergency egress through a side hatch | The pilot falls about 3 m while leaving a standing walker by the side hatch and escape ladder, possibly injured or under smoke. | gravitational | pilot | SCN-104, SCN-108 | **Medium** (critical, remote) | SYS-012 | — |

## 4. Hazards that depend on open trade studies

Deciding a trade study re-rates these hazards and reopens these requirements.

| Trade study | Status | Hazards | Requirements |
|---|---|---|---|
| TS-001 Actuation | open | HAZ-003, HAZ-005, HAZ-018, HAZ-020 | SYS-007, SYS-008, SYS-018 |
| TS-002 Pilot architecture | open | HAZ-006, HAZ-008 | SYS-010, SYS-012 |
| TS-003 Locomotion | decided | HAZ-006 | SYS-008, SYS-009, SYS-010 |
| TS-004 UAV docking | open | HAZ-012, HAZ-013 | SYS-005, SYS-006 |

## 5. Open items

1. The safety lead reviews every rating and candidate mitigation; reviewed ratings get `rating_status: reviewed`.
2. The risk-acceptance authority for each risk level is not yet defined. Until it is, no hazard can be closed (check P6).
3. The SUS-A1 Functional Hazard Assessment (ARP4761A) has not started; HAZ-014 and HAZ-015 will link to its failure conditions.
4. Next analysis: Preliminary Hazard Analysis (PHA) — causes in detail, target risk per hazard and verification of each mitigation.
