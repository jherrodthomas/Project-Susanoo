# Preliminary architecture — SUS-M1 + SUS-A1

**ID:** SUS-ARCH-001 · **Revision:** 0.7-draft · **Status:** Draft, not reviewed

## System decomposition
- **SUS-M1-WLK:** walker chassis, legs, feet, stability sensing and actuation
- **SUS-M1-MAN:** two manipulation arms, end effectors, payload sensors
- **SUS-M1-PIL:** human station, restraints, displays, controls, ingress/egress
- **SUS-M1-PWR:** power generation/storage, distribution, isolation, thermal control
- **SUS-M1-SAF:** independent safety monitoring, protective stop and fault handling
- **SUS-M1-DCK:** UAV mechanical retention, power/data interface, release and capture
- **SUS-A1:** compact unarmed observation UAV, flight control, sensors, communications
- **SUS-GSE:** maintenance supports, charging and test equipment

## Interfaces requiring explicit control
| Interface | Key data/energy | Primary hazard concern |
|---|---|---|
| Pilot ↔ controls | Intent, status, alerts | Unintended movement, cognitive overload |
| Controller ↔ actuators | Motion command, feedback, power | Runaway motion, trapped energy |
| Walker ↔ ground | Contact loads, terrain sensing | Instability and fall |
| Walker ↔ UAV | Release, docking, charge, telemetry | Rotor strike, failed retention |
| UAV ↔ pilot | Video, state, alerts | Misleading or distracting information |
| Maintenance ↔ walker | Support, isolation, service | Crush/entrapment and residual pressure |

The interfaces are recorded as IF-01 to IF-06 in [`pdac/items/architecture.yaml`](../pdac/items/architecture.yaml). **Open finding F-ARCH-01:** the decomposition has no explicit motion-control component, so the endpoints of the controller ↔ actuators interface (IF-02) are provisional.

## Safety architecture principles
Independent emergency-stop path where feasible; mechanical load support for loss of power; pressure relief and isolation; positive docking retention; rotor inhibit when secured; explicit UAV approach abort; safety state and authority allocation per operating mode.

## Initial system requirements candidates (not yet baselined)
Generated from [`pdac/items/requirements.yaml`](../pdac/items/requirements.yaml) by `tools/pdac/generate.py`; the records are the source of truth. SYS-001 to SYS-006 keep their original wording; SYS-007 to SYS-018 were added to cover scenarios that had no requirement; SYS-019 (kneel posture for ingress and egress) comes from the CL-05 reference layout.

<!-- BEGIN GENERATED: requirements (tools/pdac/generate.py) -->
| ID | Requirement | Type | Mitigates | Allocated to | Verification (planned) | Status |
|---|---|---|---|---|---|---|
| SYS-001 | System shall inhibit leg actuation until pilot station readiness conditions are satisfied. *TBD: readiness conditions (restraint, seat, controls neutral, supports, exclusion zone).* | safety | HAZ-002 | SUS-M1-SAF, SUS-M1-PIL | simulation, test | candidate |
| SYS-002 | System shall provide an operator-requested protective stop with defined behavior for each operating mode. *TBD: stop behavior per mode (controlled stop to supported posture, not instant zero torque); stop time and distance.* | safety | HAZ-001, HAZ-009, HAZ-021 | SUS-M1-SAF, SUS-M1-PIL | analysis, simulation, test | candidate |
| SYS-003 | UAV shall be prevented from rotor startup while mechanically retained, except under an approved maintenance procedure. | safety | HAZ-011 | SUS-A1, SUS-M1-DCK | analysis, test | candidate |
| SYS-004 | System shall detect loss of essential feedback and transition to a documented degraded state. *TBD: list of essential feedback signals; detection time; degraded state per mode.* | safety | HAZ-001, HAZ-006 | SUS-M1-SAF, SUS-M1-WLK | simulation, test | candidate |
| SYS-005 | Docking interface shall report positively confirmed retained/unretained state. *Depends on TS-004.* | safety | HAZ-011, HAZ-013 | SUS-M1-DCK | analysis, test | candidate |
| SYS-006 | UAV launch and recovery shall be inhibited outside a verified operational envelope. *TBD: envelope: walker motion state, wind, clearance, dock-ready conditions.* *Depends on TS-004.* | safety | HAZ-012, HAZ-016 | SUS-M1-DCK, SUS-A1, SUS-M1-SAF | simulation, test | candidate |
| SYS-007 | System shall provide means to isolate, relieve and verify the absence of stored hydraulic, mechanical and electrical energy before maintenance and before egress from a supported posture. *Depends on TS-001.* | safety | HAZ-003, HAZ-004 | SUS-M1-PWR, SUS-GSE | inspection, test | candidate |
| SYS-008 | On loss of actuation power or pressure, the walker shall hold or reach a supported posture without uncontrolled descent or motion. *TBD: maximum descent rate; load-holding means (valves, brakes, mechanical locks).* *Depends on TS-001, TS-003.* | safety | HAZ-005, HAZ-021 | SUS-M1-WLK, SUS-M1-PWR, SUS-M1-SAF | analysis, simulation, test | candidate |
| SYS-009 | System shall estimate stability margin and limit commanded motion and payload so that the margin stays above a defined threshold within the operating envelope. *TBD: stability metric and threshold; slope, speed, payload and CG envelope.* *Depends on TS-003.* | safety | HAZ-006, HAZ-010 | SUS-M1-WLK, SUS-M1-SAF | analysis, simulation | candidate |
| SYS-010 | The pilot station shall protect the restrained pilot against fall and overturn loads within a defined envelope. *TBD: protective-structure load cases; restraint type.* *Depends on TS-002, TS-003.* | safety | HAZ-006 | SUS-M1-PIL | analysis, test | candidate |
| SYS-011 | System shall detect absence of valid pilot input or responsiveness for longer than a defined time and transition to a supported safe state. *TBD: responsiveness detection method; time limit; observer remote stop interaction.* | safety | HAZ-007 | SUS-M1-SAF, SUS-M1-PIL | simulation, test | candidate |
| SYS-012 | The pilot shall be able to egress, and external personnel to extract the pilot, from any posture including after a fall, within a defined time and without relying on platform power. *TBD: egress and extraction times; postures considered; emergency hatch clear opening (concept: 0.62 x 0.72 m); descent aid and fall protection from about 3.2 m; release force and operation from inside and outside.* *Depends on TS-002.* | human-factors | HAZ-008, HAZ-017, HAZ-023 | SUS-M1-PIL | analysis, demonstration | candidate |
| SYS-013 | System shall limit manipulator force, speed and payload to defined values and inhibit manipulation while the exclusion zone is not confirmed clear. System shall inhibit walking until both manipulator arms are confirmed stowed and locked, and shall hold the arms stowed until walking has stopped. *TBD: force, speed and payload limits; exclusion-zone confirmation means; stowed arm position and tolerance (concept CL-05: upper arm 45 deg down, forearm 80 deg); stow detection and locking means; response if an arm leaves the stowed position while walking; whether any payload may be carried while walking.* | safety | HAZ-009, HAZ-010 | SUS-M1-MAN, SUS-M1-SAF | simulation, test | candidate |
| SYS-014 | On loss of command link for longer than a defined time, the UAV shall execute a predefined contingency (hold, return or land) that remains inside the approved operating area. *TBD: link-loss time; contingency selection logic; operating-area containment.* | safety | HAZ-014 | SUS-A1 | simulation, test | candidate |
| SYS-015 | The pilot display shall annunciate stale, frozen or invalid UAV imagery and telemetry within a defined time. *TBD: staleness detection time; annunciation design.* | human-factors | HAZ-015 | SUS-M1-PIL, SUS-A1 | simulation, test | candidate |
| SYS-016 | Walker locomotion shall be inhibited or limited while the pilot is actively tasking the UAV, and UAV tasks shall not require pilot attention while the walker is in motion. *TBD: permitted walker motion during UAV tasking.* | human-factors | HAZ-016 | SUS-M1-PIL, SUS-M1-SAF | analysis, simulation | candidate |
| SYS-017 | System shall detect battery thermal, overcurrent and insulation faults, isolate the affected source and alert the pilot within a defined time; energy sources shall be separated or shielded from the pilot station. *TBD: detection and alert times; separation and shielding concept.* | safety | HAZ-017, HAZ-018, HAZ-019 | SUS-M1-PWR, SUS-M1-PIL | analysis, test | candidate |
| SYS-018 | Pressurized lines and components within reach of the pilot or crew shall be shielded or routed to prevent fluid injection and spray onto hot or electrical surfaces. *Depends on TS-001.* | safety | HAZ-003, HAZ-020 | SUS-M1-PWR, SUS-M1-WLK, SUS-M1-PIL | inspection, analysis | candidate |
| SYS-019 | The walker shall provide a controlled lowered posture for ingress and egress, with the cockpit floor at or below a defined height, entered and left only while the area under and around the pod and legs is confirmed clear. *TBD: maximum sill and step heights when lowered (placeholder: 0.40 m largest rise); clear-zone confirmation means; lowering and rising speed; ladder stow interlock while walking; access-system standard (ISO 2867 candidate).* | safety | HAZ-008, HAZ-022 | SUS-M1-WLK, SUS-M1-PIL, SUS-M1-SAF | analysis, simulation, demonstration | candidate |
<!-- END GENERATED: requirements -->

All thresholds, safe-state choices and performance claims remain TBD pending hazard analysis and trade studies.
