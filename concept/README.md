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

Preliminary decomposition from [`architecture.md`](architecture.md). Amber = protective function,
purple = interface. Dashed outline = subject of an open trade study (TS-xxx).

```mermaid
flowchart TB
  subgraph I1["SUS-I1 Integrated mech + UAV system"]
    direction TB
    subgraph M1["SUS-M1 Piloted walker"]
      direction TB
      WLK["SUS-M1-WLK<br/>Chassis, legs, feet<br/>TS-001 actuation, TS-003 locomotion"]
      MAN["SUS-M1-MAN<br/>Manipulator arms"]
      PIL["SUS-M1-PIL<br/>Pilot station<br/>TS-002 pilot architecture"]
      PWR["SUS-M1-PWR<br/>Power, isolation, thermal"]
      SAF["SUS-M1-SAF<br/>Independent safety monitor"]
      DCK["SUS-M1-DCK<br/>UAV dock<br/>TS-004 dock location"]
    end
    subgraph A1["SUS-A1 Observation UAV"]
      direction TB
      FCS["Flight control<br/>PX4 candidate"]
      UAVP["Airframe, propulsion,<br/>battery, sensors, link"]
    end
    GSE["SUS-GSE<br/>Supports, charging, test rigs"]
  end
  PIL -->|"intent"| WLK
  PIL -->|"intent"| MAN
  PWR -->|"power"| WLK
  SAF -->|"protective stop"| WLK
  SAF -->|"isolate"| PWR
  DCK <-->|"retention, charge, data"| A1
  GSE -->|"support, charging"| M1
  class WLK,MAN,PWR,FCS,UAVP,GSE system
  class SAF safety
  class DCK interface
  class PIL system
  classDef system fill:#dceaf7,stroke:#55758f,color:#17324d
  classDef safety fill:#fff0d9,stroke:#b28a3d,color:#513c16
  classDef interface fill:#eae7f5,stroke:#8370a3,color:#30254a
  style WLK stroke-dasharray: 5 4
  style PIL stroke-dasharray: 5 4
  style DCK stroke-dasharray: 5 4
```

## Boundary diagram

System boundary per CONOPS section 2. Green = external entities and stakeholders.

```mermaid
flowchart LR
  subgraph BND["Boundary: SUS-I1 concept system"]
    direction TB
    M1["SUS-M1 Piloted walker"]
    A1["SUS-A1 Observation UAV"]
    GSE["SUS-GSE Ground support"]
  end
  PILOT["Pilot"]
  OBS["Safety observer"]
  SUP["Mission supervisor"]
  MNT["Maintainer"]
  TER["Terrain, weather"]
  AIR["Airspace, GNSS, RF"]
  PPL["Personnel and bystanders"]
  PILOT -->|"commands, emergency intervention"| M1
  M1 -->|"status, alarms, UAV video"| PILOT
  OBS -->|"exclusion zone, intervention"| BND
  SUP -->|"operational limits"| BND
  MNT -->|"isolation, service"| GSE
  TER -->|"ground loads, weather"| M1
  AIR -->|"navigation, link"| A1
  M1 -->|"motion envelope, crush zones"| PPL
  A1 -->|"rotor and impact hazards"| PPL
  class M1,A1,GSE system
  class PILOT,OBS,SUP,MNT,TER,AIR,PPL external
  classDef system fill:#dceaf7,stroke:#55758f,color:#17324d
  classDef external fill:#e8f1e9,stroke:#63886a,color:#23412c
  style BND fill:none,stroke:#b28a3d,stroke-width:2px,stroke-dasharray: 6 4
```

| From | To | Crossing |
|---|---|---|
| Pilot | SUS-M1 | Commands, emergency intervention |
| SUS-M1 | Pilot | Status, alarms, UAV video |
| Safety observer / mission supervisor | SUS-I1 | Exclusion zone, operational limits |
| Maintainer | SUS-GSE | Isolation and service |
| Terrain, weather / airspace | SUS-M1 / SUS-A1 | Loads, navigation, link |
| SUS-M1 / SUS-A1 | Personnel | Motion, crush, rotor and impact hazards |

**Explicitly excluded:** weapons or armament, amphibious mobility, authorized human-occupied operation
(requires separate review and test authorization).

## SysML model

SysML v2 textual model: [`ConceptOperations.sysml`](ConceptOperations.sysml) — the CONOPS operating
modes as a state machine and the nominal scenarios as use cases. It imports
[`SusanooSystem`](../safety/mil-std-882e/00-system-definition/sysml/SusanooSystem.sysml). The `.sysml`
file is the model of record; diagrams below are reading aids.

### State machine (stm) — operating modes MOD-01..MOD-10

```mermaid
stateDiagram-v2
  [*] --> MOD01
  MOD01 : MOD-01 Off / secured
  MOD02 : MOD-02 Startup
  MOD03 : MOD-03 Standby
  MOD04 : MOD-04 Piloted walk
  MOD05 : MOD-05 Manipulation
  MOD06 : MOD-06 UAV prepare
  MOD07 : MOD-07 UAV flight
  MOD08 : MOD-08 UAV recovery
  MOD09 : MOD-09 Degraded / emergency
  MOD10 : MOD-10 Maintenance
  MOD01 --> MOD02 : power up
  MOD02 --> MOD03 : readiness confirmed
  MOD02 --> MOD01 : self-test failed
  MOD03 --> MOD04 : walk enable
  MOD04 --> MOD03 : hold
  MOD03 --> MOD05 : manipulate enable
  MOD05 --> MOD03 : hold
  MOD03 --> MOD06 : UAV prepare
  MOD06 --> MOD07 : launch permitted
  MOD07 --> MOD08 : recovery requested
  MOD08 --> MOD03 : retention confirmed
  MOD04 --> MOD09 : fault
  MOD05 --> MOD09 : fault
  MOD08 --> MOD09 : fault
  MOD09 --> MOD03 : fault cleared
  MOD03 --> MOD01 : shutdown
  MOD01 --> MOD10 : service requested
  MOD10 --> MOD01 : service complete
```

### Use cases — nominal scenarios SCN-001..SCN-006

```mermaid
flowchart LR
  PILOT(["Pilot"])
  CREW(["Ground crew"])
  AIR(["Airspace / GNSS"])
  subgraph SYS["SUS-I1 : IntegratedSystem"]
    direction TB
    S1(["SCN-001 Ingress / startup"])
    S2(["SCN-002 Travel"])
    S3(["SCN-003 Handling"])
    S4(["SCN-004 Observation"])
    S5(["SCN-005 Recovery"])
    S6(["SCN-006 Shutdown"])
  end
  PILOT --- S1 & S2 & S3 & S4 & S5 & S6
  CREW --- S1 & S6
  AIR --- S4
  class PILOT,CREW,AIR external
  class S1,S2,S3,S4,S5,S6 system
  classDef system fill:#dceaf7,stroke:#55758f,color:#17324d
  classDef external fill:#e8f1e9,stroke:#63886a,color:#23412c
  style SYS fill:none,stroke:#55758f,stroke-dasharray: 6 4
```

## Inputs and outputs

```mermaid
flowchart LR
  IN1["Stakeholder needs"] -->|"missions, users"| C["Concept"]
  IN2["framework/standards-applicability.md"] -->|"assurance approach"| C
  C -->|"modes, scenarios"| O1["Task 201 PHL / Task 206 O&SHA"]
  C -->|"decomposition, interfaces"| O2["00 System definition"]
  C -->|"functions"| O3["Task 208 FHA"]
  C -->|"candidate SYS-001..006"| O4["Task 203 SRHA"]
  C -->|"PX4 candidate"| O5["integrations/px4"]
  class C current
  class IN1,IN2 external
  class O1,O2,O3,O4,O5 work
  classDef current fill:#b28a3d,stroke:#513c16,color:#ffffff
  classDef external fill:#e8f1e9,stroke:#63886a,color:#23412c
  classDef work fill:#ffffff,stroke:#55758f,color:#17324d
```

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
