# SUS-M1 / SUS-A1 Concept of Operations (CONOPS)

**ID:** SUS-CONOPS-001 · **Revision:** 0.3-draft · **Status:** Unapproved concept

## 1. Mission and scope
A human-piloted, unarmed mechanized walker (SUS-M1) and dockable observation UAV (SUS-A1) support bounded material handling, logistics, inspection and field support. SUS-I1 is the integrated product. The project is simulation-first and demonstrates Product Development as Code (PDaC). It is not a combat system, flight-qualified aircraft or authorized human-occupied prototype.

## 2. System boundary
Walker: chassis, legs, feet, manipulation arms, operator station, actuation and power, safety monitor, communications, docking and charging. UAV: airframe, propulsion, sensors, flight control, data link and docking interface. Ground support: test stands, maintenance isolation, charging, observer and supervision tools. External environment: terrain, weather, airspace, communications and personnel.

## 3. Stakeholders
Pilot (commands and emergency intervention), safety observer (exclusion zone and intervention), mission supervisor (operational limits), maintainer (isolation and service), systems lead (architecture), safety lead (hazard management), UAV lead (aircraft assurance), verification lead (test evidence).

## 4. Assumptions and operating envelope
Initial operation is digital simulation and supported bench rigs. Terrain slope, payload, speed, center of gravity, endurance, wind, docking tolerance and radio range are TBD. Future occupied tests require independent safety review, mechanical supports, egress procedures and test authorization. Amphibious mobility is excluded.

## 5. Modes
| ID | Mode | Entry / function | Safe transition concern |
|---|---|---|---|
| MOD-01 | OFF/SECURED | Energy isolated, supported | Residual pressure and restraint |
| MOD-02 | STARTUP | Pilot readiness and self-test | Inhibit unexpected actuation |
| MOD-03 | STANDBY | Stable pose, motion inhibited | Retention and posture |
| MOD-04 | PILOTED WALK | Bounded operator locomotion | Stability and feedback loss |
| MOD-05 | MANIPULATION | Controlled payload handling | Crushing and overload |
| MOD-06 | UAV PREPARE | Dock, clearance and preflight | Rotor inhibit and release |
| MOD-07 | UAV FLIGHT | Observation and return | Lost link and pilot attention |
| MOD-08 | UAV RECOVERY | Approach, capture, retention | Collision and capture failure |
| MOD-09 | DEGRADED/EMERGENCY | Mode-specific fault response | Avoid collapse or entrapment |
| MOD-10 | MAINTENANCE | Supported, isolated service | Stored energy and egress |

## 6. Nominal scenarios
**SCN-001 Ingress/startup:** Crew confirms supports, exclusion zone and pilot readiness; failed checks inhibit motion.

**SCN-002 Travel:** Pilot commands walking inside a defined stability envelope; feedback and state supervision monitor hazards.

**SCN-003 Handling:** Pilot manipulates a bounded nonhazardous payload, with load and exclusion-zone checks.

**SCN-004 Observation:** Pilot requests UAV launch from a permitted stationary state; aircraft collects imagery and returns.

**SCN-005 Recovery:** UAV approaches only with dock ready; capture and positive retention precede charging or rotor-inhibit state change.

**SCN-006 Shutdown:** UAV accounted for; walker reaches a supported posture, isolates energy and allows pilot egress.

## 7. Off-nominal scenarios
**SCN-101:** Joint control disagreement or runaway movement. **SCN-102:** Hydraulic pressure loss, leak or stored pressure. **SCN-103:** Loss of balance, fall or overturn. **SCN-104:** Pilot incapacitation or blocked egress. **SCN-105:** UAV lost link, misleading imagery or pilot distraction. **SCN-106:** UAV approaches moving or unready dock. **SCN-107:** Unexpected rotor startup while retained. **SCN-108:** Thermal or electrical event near pilot.

Each scenario must derive hazards, controls, verification and mode-specific contingencies. Emergency stop must not be assumed to mean instant zero torque if that could cause collapse.

## 8. Human factors and safety
Assess ingress/egress, restraints, visibility, alarms, workload, manual authority, observer intervention, safe posture, crush zones, rotor clearance, hot surfaces, energy isolation and maintenance support. Establish actual limits only after analysis and verification.

## 9. Candidate requirements
| Source | Candidate |
|---|---|
| SCN-001 | SYS-001 pilot-readiness actuation interlock |
| SCN-002/101 | SYS-004 feedback fault detection and degraded behavior |
| SCN-003 | Payload and stability limits (TBD) |
| SCN-004/105 | UAV lost-link behavior and display integrity (TBD) |
| SCN-005/106 | SYS-005 docking retention; SYS-006 envelope inhibit |
| SCN-107 | SYS-003 docked rotor inhibit |
| SCN-108 | Isolation and emergency egress (TBD) |

## 10. Design alternatives and open decisions
Hydraulic, electrohydraulic or electromechanical actuation; seated or standing pilot; biped, quadruped or hybrid locomotion; rear/shoulder/separate UAV dock. Selection requires trade studies and safety review. No concept rendering establishes feasibility.

## 11. Success criteria and assurance
Demonstrate simulated locomotion, manipulation, UAV observation/recovery, fault response, traceable requirements/hazards/tests and a controlled PDaC release. Quantitative acceptance criteria remain TBD. MIL-STD-882E is the integrated safety method; machinery/human factors techniques support walker analysis; ARP4754B/ARP4761A are voluntarily applied to UAV development and safety assessment. None implies certification.

## 12. Baseline approval
**Draft only.** Systems, safety, human factors and UAV reviewers must disposition open issues before approval. Changes trigger impact review across requirements, hazards, interfaces, tests and release configuration.
