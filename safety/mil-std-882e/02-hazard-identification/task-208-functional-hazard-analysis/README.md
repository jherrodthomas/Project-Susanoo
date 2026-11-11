# Task 208 · Functional Hazard Analysis (FHA)

> **Status:** Scaffold v0.1 — structure, diagrams and model views only
>
> Planning artifact. No completed hazard analysis, verified mitigation, risk acceptance, certification or MIL-STD-882E compliance is claimed. Category names follow MIL-STD-882E; confirm definitions against the controlled standard and the approved SSPP before formal use.

| Field | Value |
|---|---|
| MIL-STD-882E element | 2 — Identify and document hazards |
| Tasks | [Task 208 — Functional Hazard Analysis](../../../../docs/wiki/MIL-STD-882E-Task-208.md) |
| Lifecycle gate | G1–G2 |
| Applicability | Selected |
| Accountable role | Safety lead with software safety lead |
| Parent folder | [02 · Identify and Document Hazards](../README.md) |

## Purpose

Analyses system functions for loss, erroneous, untimely and unintended operation, and identifies
safety-significant functions and their software allocation. The SUS-A1 aircraft FHA under
ARP4761A is a separate artifact with a separate classification scale.

## Position in the MIL-STD-882E flow

Highlighted node(s) show where this folder sits in the eight-element iterative flow. Dotted links are feedback and hazard-tracking-system interactions.

```mermaid
flowchart LR
  E1["1 · Document approach"]
  E2["2 · Identify hazards"]
  E3["3 · Assess risk"]
  E4["4 · Identify mitigations"]
  E5["5 · Reduce risk"]
  E6["6 · Verify risk reduction"]
  E7["7 · Accept risk"]
  E8["8 · Manage life-cycle risk"]
  E1 --> E2 --> E3 --> E4 --> E5 --> E6 --> E7 --> E8
  E8 -. "change, deficiency or mishap" .-> E2
  HTS[("Hazard tracking system · Task 106")]
  E2 & E3 & E4 & E6 & E7 & E8 -.- HTS
  T208["Task 208 · Functional Hazard Analysis"]
  E2 --- T208
  class E1 work
  class E2 safety
  class E3 work
  class E4 work
  class E5 work
  class E6 work
  class E7 work
  class E8 work
  class HTS work
  class T208 current
  classDef system fill:#dceaf7,stroke:#55758f,color:#17324d
  classDef safety fill:#fff0d9,stroke:#b28a3d,color:#513c16
  classDef external fill:#e8f1e9,stroke:#63886a,color:#23412c
  classDef interface fill:#eae7f5,stroke:#8370a3,color:#30254a
  classDef muted fill:#f4f4f4,stroke:#b5b5b5,color:#8a8a8a,stroke-dasharray: 4 3
  classDef current fill:#b28a3d,stroke:#513c16,color:#ffffff,stroke-width:2px
  classDef work fill:#ffffff,stroke:#55758f,color:#17324d
```

## Block diagram

System elements of SUS-I1 in scope for this folder are coloured (blue = system, amber = safety function, purple = interface); greyed blocks are out of scope. Source of truth: [`SusanooSystem.sysml`](../../00-system-definition/sysml/SusanooSystem.sysml).

```mermaid
flowchart TB
  subgraph SUS_I1["SUS-I1: Integrated mech + UAV system"]
    direction TB
    subgraph SUS_M1["SUS-M1: Piloted walker"]
      direction TB
      SUS_M1_WLK["SUS-M1-WLK: Structure, legs, joints & brakes"]
      SUS_M1_MAN["SUS-M1-MAN: Manipulator arms & end effectors"]
      SUS_M1_PIL["SUS-M1-PIL: Pilot station, restraints & HMI"]
      SUS_M1_PWR["SUS-M1-PWR: Series-hybrid power & isolation"]
      SUS_M1_CTL["SUS-M1-CTL: Motion & balance control SW"]
      SUS_M1_SAF["SUS-M1-SAF: Safety monitor & protective stop"]
      SUS_M1_DCK["SUS-M1-DCK: UAV dock - retention, power, data"]
    end
    subgraph SUS_A1["SUS-A1: Observation UAV"]
      direction TB
      SUS_A1_FCS["SUS-A1-FCS: Flight control - PX4 candidate"]
      SUS_A1_PRP["SUS-A1-PRP: Motors, ESCs & propellers"]
      SUS_A1_PWR["SUS-A1-PWR: UAV battery & power mgmt"]
      SUS_A1_NAV["SUS-A1-NAV: Navigation & telemetry link"]
      SUS_A1_PLD["SUS-A1-PLD: Observation payload"]
    end
    subgraph SUS_GSE["SUS-GSE: Ground support equipment"]
      direction TB
      SUS_GSE_SUP["SUS-GSE-SUP: Maintenance supports & lockout"]
      SUS_GSE_CHG["SUS-GSE-CHG: Charging & fuelling equipment"]
      SUS_GSE_TST["SUS-GSE-TST: Test rigs, HIL & simulation"]
    end
  end
  SUS_M1_PIL -->|"commands"| SUS_M1_CTL
  SUS_M1_CTL -->|"joint actuation"| SUS_M1_WLK
  SUS_M1_CTL -->|"arm actuation"| SUS_M1_MAN
  SUS_M1_PWR -->|"DC power"| SUS_M1_WLK
  SUS_M1_SAF -->|"torque inhibit"| SUS_M1_CTL
  SUS_M1_SAF -->|"energy isolation"| SUS_M1_PWR
  SUS_M1_DCK -->|"dock charging"| SUS_A1_PWR
  SUS_M1_DCK -->|"dock data / rotor inhibit"| SUS_A1_FCS
  SUS_A1_NAV -->|"state estimate"| SUS_A1_FCS
  SUS_A1_FCS -->|"thrust command"| SUS_A1_PRP
  SUS_GSE_SUP -->|"mechanical support"| SUS_M1_WLK
  SUS_GSE_CHG -->|"shore charging"| SUS_M1_PWR
  class SUS_M1_WLK muted
  class SUS_M1_MAN muted
  class SUS_M1_PIL system
  class SUS_M1_PWR muted
  class SUS_M1_CTL system
  class SUS_M1_SAF safety
  class SUS_M1_DCK interface
  class SUS_A1_FCS system
  class SUS_A1_PRP muted
  class SUS_A1_PWR muted
  class SUS_A1_NAV muted
  class SUS_A1_PLD muted
  class SUS_GSE_SUP muted
  class SUS_GSE_CHG muted
  class SUS_GSE_TST muted
  classDef system fill:#dceaf7,stroke:#55758f,color:#17324d
  classDef safety fill:#fff0d9,stroke:#b28a3d,color:#513c16
  classDef external fill:#e8f1e9,stroke:#63886a,color:#23412c
  classDef interface fill:#eae7f5,stroke:#8370a3,color:#30254a
  classDef muted fill:#f4f4f4,stroke:#b5b5b5,color:#8a8a8a,stroke-dasharray: 4 3
  classDef current fill:#b28a3d,stroke:#513c16,color:#ffffff,stroke-width:2px
  classDef work fill:#ffffff,stroke:#55758f,color:#17324d
```

## Boundary diagram

Dashed frame = **System functions** boundary. Everything outside it is an external entity or another folder's scope.

```mermaid
flowchart LR
  subgraph BND["Boundary: System functions"]
    direction TB
    Locomotion_and_balance["Locomotion and balance"]
    Protective_stop["Protective stop"]
    Pilot_command["Pilot command"]
    Dock_retention["Dock retention"]
    UAV_flight_control["UAV flight control"]
  end
  Physical_implementation["Physical implementation"]
  ARP4761A_aircraft_FHA["ARP4761A aircraft FHA"]
  Pilot_command -->|"intent"| Locomotion_and_balance
  Protective_stop -->|"inhibit"| Locomotion_and_balance
  Dock_retention -->|"rotor inhibit"| UAV_flight_control
  Locomotion_and_balance -->|"allocation"| Physical_implementation
  UAV_flight_control -->|"cross-reference only"| ARP4761A_aircraft_FHA
  class Locomotion_and_balance work
  class Protective_stop work
  class Pilot_command work
  class Dock_retention work
  class UAV_flight_control work
  class Physical_implementation external
  class ARP4761A_aircraft_FHA external
  style BND fill:none,stroke:#b28a3d,stroke-width:2px,stroke-dasharray: 6 4
  classDef system fill:#dceaf7,stroke:#55758f,color:#17324d
  classDef safety fill:#fff0d9,stroke:#b28a3d,color:#513c16
  classDef external fill:#e8f1e9,stroke:#63886a,color:#23412c
  classDef interface fill:#eae7f5,stroke:#8370a3,color:#30254a
  classDef muted fill:#f4f4f4,stroke:#b5b5b5,color:#8a8a8a,stroke-dasharray: 4 3
  classDef current fill:#b28a3d,stroke:#513c16,color:#ffffff,stroke-width:2px
  classDef work fill:#ffffff,stroke:#55758f,color:#17324d
```

| From | To | Crossing / interaction |
|---|---|---|
| Pilot command | Locomotion and balance | intent |
| Protective stop | Locomotion and balance | inhibit |
| Dock retention | UAV flight control | rotor inhibit |
| Locomotion and balance | Physical implementation | allocation |
| UAV flight control | ARP4761A aircraft FHA | cross-reference only |

## SysML model

SysML v2 textual view: [`Task208_FHA.sysml`](Task208_FHA.sysml) (generated from the catalog; imports [`SusanooSystem`](../../00-system-definition/sysml/SusanooSystem.sysml) and [`SusanooSafety`](../../00-system-definition/sysml/SusanooSafety.sysml)). The Mermaid rendering below is a reading aid; the `.sysml` file is the model of record.

### Activity (act) — functional chain under analysis

```mermaid
flowchart TD
  start((start))
  senseIntent["Sense pilot intent"]
  estimateState["Estimate walker state"]
  planMotion["Plan motion and balance"]
  actuateJoints["Actuate joints"]
  monitorSafety["Monitor and enforce protective stop"]
  start --> senseIntent
  senseIntent --> estimateState
  estimateState --> planMotion
  planMotion --> actuateJoints
  actuateJoints --> monitorSafety
  monitorSafety --> done((done))
  monitorSafety -. "inhibit on fault" .-> actuateJoints
  class monitorSafety safety
  classDef system fill:#dceaf7,stroke:#55758f,color:#17324d
  classDef safety fill:#fff0d9,stroke:#b28a3d,color:#513c16
  classDef external fill:#e8f1e9,stroke:#63886a,color:#23412c
  classDef interface fill:#eae7f5,stroke:#8370a3,color:#30254a
  classDef muted fill:#f4f4f4,stroke:#b5b5b5,color:#8a8a8a,stroke-dasharray: 4 3
  classDef current fill:#b28a3d,stroke:#513c16,color:#ffffff,stroke-width:2px
  classDef work fill:#ffffff,stroke:#55758f,color:#17324d
```

### Block definition (bdd) — functional failure condition

```mermaid
classDiagram
  class FunctionalFailure {
    <<item>>
    +String functionId
    +FunctionalFailureType failureType
    +String hazardId
    +SoftwareControlCategory swci
  }
  class FunctionalFailureType {
    <<enumeration>>
    Loss
    Erroneous
    Untimely
    Unintended
    Degraded
  }
```

<details><summary>SysML v2 source</summary>

```sysml
// Task208_FHA — generated by tools/gen_safety_docs.py from safety/mil-std-882e/catalog.yaml.
// Do not edit by hand: change the catalog and regenerate.
// Status: planning view only; not evidence of completed analysis or verification.

package Task208_FHA {
    private import ScalarValues::*;
    private import SusanooSystem::*;
    private import SusanooSafety::*;
    action def WalkerFunctionalChain {
        action senseIntent { doc /* Sense pilot intent */ }
        action estimateState { doc /* Estimate walker state */ }
        action planMotion { doc /* Plan motion and balance */ }
        action actuateJoints { doc /* Actuate joints */ }
        action monitorSafety { doc /* Monitor and enforce protective stop */ }
        first start;
        then senseIntent;
        first senseIntent then estimateState;
        first estimateState then planMotion;
        first planMotion then actuateJoints;
        first actuateJoints then monitorSafety;
        first monitorSafety then done;
        // iteration: monitorSafety -> actuateJoints when inhibit on fault (informal; merge node omitted)
    }

    item def FunctionalFailure {
        attribute functionId : String;
        attribute failureType : FunctionalFailureType;
        attribute hazardId : String;
        attribute swci : SoftwareControlCategory;
    }
    enum def FunctionalFailureType {
        enum Loss;
        enum Erroneous;
        enum Untimely;
        enum Unintended;
        enum Degraded;
    }
}
```

</details>

## Inputs and outputs

```mermaid
flowchart LR
  T208["Task 208 · Functional Hazard Analysis (FHA)"]
  in0["00 · System Definition and Analysis Baseline"] -->|"Function list"| T208
  class in0 work
  in1["Task 201 · Preliminary Hazard List (PHL)"] -->|"PHL"| T208
  class in1 work
  T208 -->|"Safety-significant functions"| out0["Software Contribution to System Risk (Section 4.4)"]
  class out0 work
  T208 -->|"Functional safety requirements"| out1["Task 203 · System Requirements Hazard Analysis (SRHA)"]
  class out1 work
  class T208 current
  classDef system fill:#dceaf7,stroke:#55758f,color:#17324d
  classDef safety fill:#fff0d9,stroke:#b28a3d,color:#513c16
  classDef external fill:#e8f1e9,stroke:#63886a,color:#23412c
  classDef interface fill:#eae7f5,stroke:#8370a3,color:#30254a
  classDef muted fill:#f4f4f4,stroke:#b5b5b5,color:#8a8a8a,stroke-dasharray: 4 3
  classDef current fill:#b28a3d,stroke:#513c16,color:#ffffff,stroke-width:2px
  classDef work fill:#ffffff,stroke:#55758f,color:#17324d
```

| Input | Source |
|---|---|
| Function list | [00 · System Definition and Analysis Baseline](../../00-system-definition/README.md) |
| PHL | [Task 201 · Preliminary Hazard List (PHL)](../task-201-preliminary-hazard-list/README.md) |

| Output | Destination |
|---|---|
| Safety-significant functions | [Software Contribution to System Risk (Section 4.4)](../../software-safety/README.md) |
| Functional safety requirements | [Task 203 · System Requirements Hazard Analysis (SRHA)](../task-203-system-requirements-hazard-analysis/README.md) |

## Folder contents

| Item | Description | State |
|---|---|---|
| `fha.csv` | Function x failure-type worksheet | planned |
| [`Task208_FHA.sysml`](Task208_FHA.sysml) | Generated SysML v2 view | generated |

<!-- END GENERATED: content below this line is human-authored and preserved -->

## Working content

_No analysis content yet. Add authored material below this heading._
