# SUS-M1 Concept of Operations — draft v0.2

## Purpose and boundary
A human operator pilots a powered, legged mechanized platform for **non-weaponized** logistics, material handling, inspection and field support. A compact dockable SUS-A1 UAV provides local aerial observation. The system boundary includes walker, pilot station, power/actuation, UAV, docking and servicing interface, mission displays and ground support equipment.

## Stakeholders
Pilot, ground safety observer, maintenance technician, mission supervisor, safety engineer and verification team.

## Operational modes
| Mode | Description | Principal controls to study |
|---|---|---|
| OFF/SECURED | Isolated energy and mechanically secured joints | Lockout, supports, stored-energy discharge |
| STARTUP | Pilot ingress, health checks, energy enable | Interlocks, readiness checks |
| STANDBY | Stable posture, controls armed but no locomotion | Brakes, limits, operator presence |
| PILOTED WALK | Human commands assisted leg movement | Stability envelope, fall detection, speed limits |
| MANIPULATION | Arms handle nonhazardous loads | Load limits, crush-zone exclusion |
| UAV PREPARE | UAV power, health, docking release checks | Clearance and inhibit logic |
| UAV FLIGHT | UAV observes; pilot retains ground controls | Attention management, lost-link behavior |
| UAV RECOVERY | UAV approaches and docks in defined envelope | Rotor separation, approach abort, retention |
| DEGRADED | Controlled stop/pose/landing per fault | Fault isolation and safe-state analysis |
| MAINTENANCE | Supported structure, energy isolation | Mechanical supports and LOTO |

## Initial use case
Pilot enters and secures restraints; platform starts and performs self-test; pilot walks to a designated material-handling area; pilot moves a bounded payload; pilot requests UAV observation; UAV launches under a defined stationary-platform envelope; UAV returns and docks; pilot returns, secures and shuts down the walker.

## Exclusions and constraints
No weapons, combat functions, autonomous targeting, or human-carrying flight. No unsupported claim of operation near bystanders. Physical human-wearable or piloted testing is out of scope until risk controls, independent review, structural support, emergency egress and controlled test procedures exist.

## Open decisions
Pilot seated versus standing; enclosure and rollover protection; mass and center-of-gravity limits; energy source; hydraulic versus electric joints; leg count and stability; UAV docking position; ground observer and remote stop architecture.
