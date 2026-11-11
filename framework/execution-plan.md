# Execution roadmap — SUS-M1/SUS-A1

**ID:** SUS-FW-006 · **Revision:** 0.3-draft · **Status:** Draft, not reviewed

1. **Concept baseline:** CONOPS, system boundaries, mission and operating modes, architecture trade studies.
2. **System safety planning:** SSPP, initial PHL/PHA, pilot safety, emergency stop/egress and energy isolation concepts.
3. **Requirements/MBSE:** stakeholder/system requirements, interfaces, functional decomposition and traceability.
4. **Preliminary analyses:** walker machinery risk, stability, hydraulics; UAV FHA/PSSA; docking hazards.
5. **Simulation and bench models:** supported actuator test rig, walker dynamics model, UAV simulator and interface tests.
6. **Detailed assurance:** SSHA/SHA/O&SHA, UAV SSA, verification procedures, fault injection and discrepancies.
7. **PDaC executable lifecycle:** schemas, validators, change impact, evidence manifest, version/configuration control.
8. **Release:** reviewed simulation demonstrator and documented limitations, never unsubstantiated certification claims.

**First implementation priority:** human safety architecture, actuation trade study, pilot/egress concept and UAV docking hazards before selecting physical hardware.

## Progress
| Step | State |
|---|---|
| 1 Concept baseline | CONOPS 0.4-draft, architecture and trade studies drafted; trade studies open; nothing reviewed |
| 2 System safety planning | Preliminary Hazard List drafted as records ([SUS-PHL-001](../safety/preliminary-hazard-list.md)); System Safety Program Plan not started |
| 3 Requirements | 18 system requirement candidates as records, traced to scenarios and hazards |
| 7 PDaC executable lifecycle | Schema, validator (checks P1–P9), generated views and CI in place ([pdac/README.md](../pdac/README.md)); change impact and evidence manifest planned |
