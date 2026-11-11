# Preliminary architecture — SUS-M1 + SUS-A1

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

## Safety architecture principles
Independent emergency-stop path where feasible; mechanical load support for loss of power; pressure relief and isolation; positive docking retention; rotor inhibit when secured; explicit UAV approach abort; safety state and authority allocation per operating mode.

## Initial system requirements candidates (not yet baselined)
- SYS-001: System shall inhibit leg actuation until pilot station readiness conditions are satisfied.
- SYS-002: System shall provide an operator-requested protective stop with defined behavior for each operating mode.
- SYS-003: UAV shall be prevented from rotor startup while mechanically retained, except under an approved maintenance procedure.
- SYS-004: System shall detect loss of essential feedback and transition to a documented degraded state.
- SYS-005: Docking interface shall report positively confirmed retained/unretained state.
- SYS-006: UAV launch and recovery shall be inhibited outside a verified operational envelope.

All thresholds, safe-state choices and performance claims remain TBD pending hazard analysis and trade studies.
