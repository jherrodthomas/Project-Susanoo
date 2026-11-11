# PX4 Integration — SUS-A1 Candidate Flight-Control Baseline

> **Status:** proposed, not integrated or verified. This is an engineering integration plan, not a claim that PX4 or SUS-A1 is certified or airworthy.

| Field | Value |
|---|---|
| System element | SUS-A1-FCS (flight control) and its SUS-I1 interfaces |
| Lifecycle gate | G2 (architecture) through G4 (simulation readiness) |
| Accountable role | UAV lead with software safety lead |
| Interface contract | [`interface-contract.md`](interface-contract.md) |
| Documentation standard | [`framework/documentation-standard.md`](../../framework/documentation-standard.md) |

## Purpose

Adopt [PX4 Autopilot](https://github.com/PX4/PX4-Autopilot) as the **candidate** SUS-A1 flight-control software baseline. Keep PX4 upstream and version-pinned as an external dependency; do not vendor or fork PX4 in Susanoo until an actual divergence is justified.

**License:** BSD 3-Clause. Preserve original source/license notices when redistributing. External dependency review shall capture licenses and third-party notices.

### Functional split
- PX4: flight stabilization, navigation, flight modes, configured onboard failsafes and vehicle telemetry.
- SUS-A1 companion/integration: payload observation, mission interface and UAV dock handshake, avoiding unsafe simultaneous control authorities.
- SUS-M1: piloted walking/manipulation and pilot station. SUS-M1 does **not** use PX4 to control walker joints.
- SUS-I1 supervisory layer: coordinate readiness, UAV launch/recovery, operator alerting, docking interlocks, and system safety.
- QGroundControl: development/flight monitoring and parameter configuration, not a substitute for an approved operations procedure.

### Proposed interfaces
1. ROS 2 and uXRCE-DDS for telemetry and high-level integration where supported.
2. MAVLink/MAVSDK for mission-management operations under explicit state/authority constraints.
3. Defined application interface for dock readiness, retained state, mechanical release, rotor inhibit, launch clearance, approach permit and abort.
4. PDaC trace links from PX4 version/configuration through scenarios, safety analyses, requirements and tests.

## Block diagram

PX4 and the Susanoo-owned integration parts. Blue = system, amber = protective/authority function,
purple = interface, grey = external dependency or tool.

```mermaid
flowchart TB
  subgraph I1["SUS-I1 Integrated system"]
    direction TB
    subgraph A1["SUS-A1 Observation UAV"]
      direction TB
      PX4["PX4 Autopilot (pinned)<br/>stabilisation, navigation,<br/>flight modes, failsafes"]
      ADP["UAV control adapter<br/>validated, fail-closed"]
      CMP["Companion / payload<br/>observation, mission interface"]
      PRP["Motors, ESCs, propellers"]
      NAV["Nav sensors, GNSS, telemetry"]
    end
    subgraph M1["SUS-M1 Piloted walker"]
      direction TB
      DCK["SUS-M1-DCK Dock<br/>retention, charge, rotor inhibit"]
      HMI["SUS-M1-PIL Pilot HMI"]
      CTL["SUS-M1-CTL Walker control<br/>(no PX4)"]
    end
    SUP["SUS-I1 integration supervisor<br/>readiness, launch / recovery permit"]
  end
  QGC["QGroundControl<br/>dev monitoring only"]
  ADP -->|"MAVLink / MAVSDK"| PX4
  PX4 -->|"thrust"| PRP
  NAV -->|"state estimate"| PX4
  PX4 -->|"ROS 2 / uXRCE-DDS telemetry"| SUP
  SUP -->|"permit / revoke / abort"| ADP
  DCK -->|"retained state"| SUP
  CTL -->|"posture / stationary"| SUP
  SUP -->|"alerts"| HMI
  CMP -->|"video, cues"| HMI
  DCK -->|"charge / rotor inhibit"| PX4
  QGC -.->|"parameters"| PX4
  class PX4,CMP,PRP,NAV,HMI,CTL system
  class ADP,SUP safety
  class DCK interface
  class QGC muted
  classDef system fill:#dceaf7,stroke:#55758f,color:#17324d
  classDef safety fill:#fff0d9,stroke:#b28a3d,color:#513c16
  classDef interface fill:#eae7f5,stroke:#8370a3,color:#30254a
  classDef muted fill:#f4f4f4,stroke:#b5b5b5,color:#8a8a8a,stroke-dasharray: 4 3
```

## Boundary diagram

Dashed frame = the **PX4 flight-control assurance boundary**. It is distinct from the walker
motion-control boundary; every crossing is an IF-PX4 contract item.

```mermaid
flowchart LR
  subgraph BND["Boundary: PX4 flight-control assurance"]
    direction TB
    PX4["PX4 Autopilot + pinned parameters"]
    ADP["UAV control adapter"]
  end
  SUP["SUS-I1 integration supervisor"]
  DCK["SUS-M1-DCK dock"]
  WLK["SUS-M1 walker posture"]
  HMI["Pilot HMI"]
  UP["PX4 upstream project"]
  AIR["Airspace, GNSS, RF"]
  PX4 -->|"IF-PX4-001/002 state, health, arming"| SUP
  SUP -->|"IF-PX4-005/006 permit, recovery, abort"| ADP
  DCK -->|"IF-PX4-003 occupied / retained"| SUP
  WLK -->|"IF-PX4-004 posture / stationary"| SUP
  BND -->|"IF-PX4-007 video, mission cues"| HMI
  SUP <-->|"IF-PX4-008 fault notifications"| BND
  DCK <-->|"IF-PX4-009 power handshake, rotor inhibit"| PX4
  UP -->|"tagged release + SHA"| PX4
  AIR -->|"navigation, link"| PX4
  class PX4,ADP system
  class SUP safety
  class DCK interface
  class WLK,HMI system
  class UP,AIR external
  classDef system fill:#dceaf7,stroke:#55758f,color:#17324d
  classDef safety fill:#fff0d9,stroke:#b28a3d,color:#513c16
  classDef interface fill:#eae7f5,stroke:#8370a3,color:#30254a
  classDef external fill:#e8f1e9,stroke:#63886a,color:#23412c
  style BND fill:none,stroke:#b28a3d,stroke-width:2px,stroke-dasharray: 6 4
```

| Crossing | Interface | Control / safety concern |
|---|---|---|
| PX4 → supervisor | IF-PX4-001/002 | Freshness, source validity, disagreement |
| Dock / walker → supervisor | IF-PX4-003/004 | Independent plausibility, launch envelope |
| Supervisor → adapter | IF-PX4-005/006 | Explicit authorisation, fail-closed, lost-link contingency |
| UAV → pilot HMI | IF-PX4-007 | Latency, distraction, trust |
| Both directions | IF-PX4-008 | Time stamping and priority |
| Dock ↔ UAV power | IF-PX4-009 | Rotor inhibit, energy isolation |

**Explicitly excluded:** PX4 controlling walker joints; PX4 as a pilot-safety controller for SUS-M1;
QGroundControl as an operations procedure; weapons or autonomous targeting.

## SysML model

SysML v2 textual model: [`PX4Integration.sysml`](PX4Integration.sysml) — integration context (parts and
IF-PX4 connections), the fail-closed launch-permit state machine and the integration requirements derived
from the contract's acceptance tests. It imports
[`SusanooSystem`](../../safety/mil-std-882e/00-system-definition/sysml/SusanooSystem.sysml); `PX4Autopilot`
specialises `SusanooSystem::FlightControl`.

### Internal block / context (ibd) — PX4IntegrationContext

```mermaid
flowchart LR
  subgraph CTX["PX4IntegrationContext : context"]
    px4["px4 : PX4Autopilot"]
    adapter["adapter : UAVControlAdapter"]
    supervisor["supervisor : IntegrationSupervisor"]
    dock["dock : UAVDock"]
    walker["walker : PilotedWalker"]
    gcs["gcs : GroundControlStation"]
  end
  px4 <-->|"if001 telemetry"| supervisor
  supervisor <-->|"if005 permit"| adapter
  adapter <-->|"ifMav MAVLink"| px4
  dock <-->|"if003 retained"| supervisor
  walker <-->|"if004 posture"| supervisor
  dock <-->|"if009 power, rotor inhibit"| px4
  gcs <-->|"gcsLink"| px4
  class px4,walker system
  class adapter,supervisor safety
  class dock interface
  class gcs muted
  classDef system fill:#dceaf7,stroke:#55758f,color:#17324d
  classDef safety fill:#fff0d9,stroke:#b28a3d,color:#513c16
  classDef interface fill:#eae7f5,stroke:#8370a3,color:#30254a
  classDef muted fill:#f4f4f4,stroke:#b5b5b5,color:#8a8a8a,stroke-dasharray: 4 3
  style CTX fill:none,stroke:#55758f,stroke-dasharray: 6 4
```

### State machine (stm) — LaunchPermit (fail-closed)

```mermaid
stateDiagram-v2
  [*] --> denied
  denied : denied - default, any stale input returns here
  armable : armable - dock fresh, walker stationary
  permitted : permitted - explicit pilot request
  airborne : airborne - PX4 owns flight
  contingency : contingency - analysed lost-link on aircraft AND walker
  denied --> armable : posture stationary + dock retained fresh
  armable --> permitted : pilot requests launch
  armable --> denied : stale or inconsistent state
  permitted --> denied : stale state or permit revoked
  permitted --> airborne : UAV clear of dock
  airborne --> contingency : link lost
  airborne --> denied : recovered
  contingency --> denied : recovered
```

### Requirements (req) — integration requirements

```mermaid
requirementDiagram
  requirement PX4_R_001 {
    id: "PX4-R-001"
    text: "Launch authorised only in correct walker posture and dock state"
    risk: High
    verifymethod: Test
  }
  requirement PX4_R_002 {
    id: "PX4-R-002"
    text: "Stale or inconsistent dock state prevents launch authorisation"
    risk: High
    verifymethod: Test
  }
  requirement PX4_R_003 {
    id: "PX4-R-003"
    text: "Flight and ground controller authority collision prevented"
    risk: High
    verifymethod: Analysis
  }
  requirement PX4_R_004 {
    id: "PX4-R-004"
    text: "Lost link during docking aborts and does not command walker movement"
    risk: High
    verifymethod: Test
  }
  element SUP {
    type: "IntegrationSupervisor"
  }
  element ADP {
    type: "UAVControlAdapter"
  }
  element SITL {
    type: "PX4 SITL test (P3-P4)"
  }
  SUP - satisfies -> PX4_R_001
  SUP - satisfies -> PX4_R_002
  ADP - satisfies -> PX4_R_003
  SUP - satisfies -> PX4_R_004
  SITL - verifies -> PX4_R_001
  SITL - verifies -> PX4_R_002
  SITL - verifies -> PX4_R_004
```

## Inputs and outputs

```mermaid
flowchart LR
  I1["PX4 upstream release"] -->|"source, license, docs"| X["PX4 integration"]
  I2["concept/CONOPS.md"] -->|"SCN-004/005, modes 06-08"| X
  I3["Task 203 SRHA"] -->|"SYS-003, SYS-005, SYS-006"| X
  I4["Task 208 FHA"] -->|"safety-significant functions"| X
  X -->|"PX4 version, parameters, SW functions"| O1["software-safety"]
  X -->|"IF-PX4 interfaces"| O2["Task 205 SHA"]
  X -->|"SITL / HIL evidence"| O3["Task 401 Safety verification"]
  X -->|"aircraft FHA / PSSA inputs"| O4["ARP4761A assessment (separate)"]
  class X current
  class I1,I2,O4 external
  class I3,I4,O1,O2,O3 work
  classDef current fill:#b28a3d,stroke:#513c16,color:#ffffff
  classDef external fill:#e8f1e9,stroke:#63886a,color:#23412c
  classDef work fill:#ffffff,stroke:#55758f,color:#17324d
```

| Input | Source |
|---|---|
| Source, license, documentation | [PX4 Autopilot](https://github.com/PX4/PX4-Autopilot) (pinned tag + SHA, TBD) |
| Observation and recovery scenarios, UAV modes | [`concept/CONOPS.md`](../../concept/CONOPS.md) |
| SYS-003, SYS-005, SYS-006 | [Task 203 SRHA](../../safety/mil-std-882e/02-hazard-identification/task-203-system-requirements-hazard-analysis/README.md) |
| Safety-significant functions | [Task 208 FHA](../../safety/mil-std-882e/02-hazard-identification/task-208-functional-hazard-analysis/README.md) |

| Output | Destination |
|---|---|
| PX4 version, parameters, software functions | [Software safety](../../safety/mil-std-882e/software-safety/README.md) |
| IF-PX4 interface hazards | [Task 205 SHA](../../safety/mil-std-882e/02-hazard-identification/task-205-system-hazard-analysis/README.md) |
| SITL / HIL evidence | [Task 401 Safety verification](../../safety/mil-std-882e/06-verification/task-401-safety-verification/README.md) |
| Aircraft FHA / PSSA inputs | ARP4761A assessment (separate scale; not yet created) |

## Folder contents

| Item | Description | State |
|---|---|---|
| [`interface-contract.md`](interface-contract.md) | IF-PX4-001..009, authority principles, acceptance tests | present |
| [`PX4Integration.sysml`](PX4Integration.sysml) | SysML v2 context, launch permit, requirements | present |
| `dependency-baseline.yaml` | Pinned PX4, airframe, parameters, ROS 2, simulator versions | planned |

## Dependency baseline register
| Item | Required baseline information |
|---|---|
| PX4 version | Tagged release and exact commit SHA (TBD) |
| Airframe | Model/geometry and airframe ID (TBD) |
| Firmware target | Board and OS (TBD) |
| Parameters | Exported configured parameter set (TBD) |
| ROS 2 | Distribution, px4_msgs branch/version and DDS bridge (TBD) |
| Gazebo | Tested simulator version and world model (TBD) |
| MAVLink/MAVSDK | Version and messages/API contract (TBD) |
| QGroundControl | Version and configuration (TBD) |
| Licenses/SBOM | Recorded and verified (TBD) |

## Incremental integration
**P0:** Run unmodified PX4 multicopter SITL; record build and simulator versions.  
**P1:** Connect QGroundControl and collect telemetry/logs.  
**P2:** Connect ROS 2 telemetry only; record message compatibility and time sync.  
**P3:** Implement simulation-only launch/recover mission state machine with explicit authority and mode checks.  
**P4:** Add simulated docking sensors, rotor inhibit and abort; inject faults.  
**P5:** Conduct UAV FHA, PSSA and system interface hazard analyses, close design gaps.  
**P6:** Evaluate HIL and physical test readiness through formal safety reviews; no automatic flight authorization.

## Offboard control warning
Do not publish setpoints indiscriminately. PX4's own documentation warns that ROS 2 setpoints can collide with onboard controller publishers. Use documented control modes and verify loss-of-offboard behavior. Prefer the PX4 ROS 2 Interface Library for custom modes if justified; experimental interfaces must be pinned and assessed.

## Review references
- https://github.com/PX4/PX4-Autopilot
- https://docs.px4.io/main/en/ros2/
- https://docs.px4.io/main/en/simulation/
- https://docs.px4.io/main/en/flight_modes/offboard.html
- https://github.com/PX4/px4_msgs

**Non-goals:** weapons, autonomous targeting, using PX4 as a pilot-safety controller for SUS-M1, or asserting DO-178C/ARP4761A qualification without evidence.
