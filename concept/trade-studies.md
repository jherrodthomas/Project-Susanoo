# Architecture trade studies

**ID:** SUS-TRADE-001 · **Revision:** 0.4-draft · **Status:** Draft, not reviewed

## TS-001 Actuation
Alternatives: centralized hydraulic; distributed electrohydraulic; electromechanical. Compare power density, controllability, leakage/fire risk, stored energy, maintainability, mass, noise, heat, fault response, supply chain, simulation fidelity and cost. **No winner selected.**

## TS-002 Pilot architecture
Alternatives: seated protected cockpit; standing open-frame pilot; remote operator. Compare ergonomics, ingress/egress, restraint, fall/rollover protection, visibility, emergency extraction, human-machine interface and structural packaging.

## TS-003 Locomotion — decided: bipedal
Alternatives were: bipedal; quadrupedal; hybrid leg-wheel. **Decided by the project lead on 2026-11-11: bipedal.** The decision is a product-direction choice; the comparison of stability, complexity, energy consumption, terrain capability, fall consequences and testability was not carried out. Consequence to carry forward: a biped cannot stand without active balance (see the static margin of every layout in [SUS-CAD-001](../cad/README.md)), so fall, loss-of-actuation and protective-stop hazards (HAZ-005, HAZ-006, HAZ-021) and requirements SYS-008, SYS-009 and SYS-010 carry the safety weight of this choice. An approval record formalising the decision is pending.

## TS-004 UAV docking
Alternatives: rear backpack dock; shoulder-mounted dock; separate portable station. Compare rotor clearance, center of gravity, accessibility, charging, environmental protection, approach geometry, emergency separation and operator exposure.

## Decision process
Each study records criteria, weights, assumptions, quantitative evidence, safety impact, reviewer, decision authority, selected baseline and linked change request. Rendered concepts are not evidence of feasibility.
