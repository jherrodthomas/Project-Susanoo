# Task 401 · Safety Verification

> **Status:** Scaffold v0.1 — structure, diagrams and model views only
>
> Planning artifact. No completed hazard analysis, verified mitigation, risk acceptance, certification or MIL-STD-882E compliance is claimed. Category names follow MIL-STD-882E; confirm definitions against the controlled standard and the approved SSPP before formal use.

| Field | Value |
|---|---|
| MIL-STD-882E element | 6 — Verify, validate and document risk reduction |
| Tasks | [Task 401 — Safety Verification](../../../../docs/wiki/MIL-STD-882E-Task-401.md) |
| Lifecycle gate | G4–G5 |
| Applicability | Selected |
| Accountable role | Test lead with safety lead |
| Parent folder | [06 · Verify, Validate and Document Risk Reduction](../README.md) |

## Purpose

Verifies each safety requirement and the effectiveness of each mitigation. Each evidence record
states provenance, version, integrity hash and whether it is simulated (traceability rule 6).

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
  T401["Task 401 · Safety Verification"]
  E6 --- T401
  class E1 work
  class E2 work
  class E3 work
  class E4 work
  class E5 work
  class E6 safety
  class E7 work
  class E8 work
  class HTS work
  class T401 current
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
  class SUS_M1_CTL muted
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

Dashed frame = **Verified safety requirements** boundary. Everything outside it is an external entity or another folder's scope.

```mermaid
flowchart LR
  subgraph BND["Boundary: Verified safety requirements"]
    direction TB
    SUS_M1_SAF["SUS-M1-SAF: Safety monitor & protective stop"]
    SUS_M1_DCK["SUS-M1-DCK: UAV dock - retention, power, data"]
    SUS_M1_PIL["SUS-M1-PIL: Pilot station, restraints & HMI"]
  end
  SUS_GSE_TST["SUS-GSE-TST: Test rigs, HIL & simulation"]
  Evidence_store["Evidence store"]
  SUS_GSE_TST -->|"fault injection"| SUS_M1_SAF
  SUS_GSE_TST -->|"latch state tests"| SUS_M1_DCK
  SUS_M1_SAF -->|"results with hash"| Evidence_store
  class SUS_M1_SAF safety
  class SUS_M1_DCK interface
  class SUS_M1_PIL system
  class SUS_GSE_TST external
  class Evidence_store external
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
| SUS-GSE-TST: Test rigs, HIL & simulation | SUS-M1-SAF: Safety monitor & protective stop | fault injection |
| SUS-GSE-TST: Test rigs, HIL & simulation | SUS-M1-DCK: UAV dock - retention, power, data | latch state tests |
| SUS-M1-SAF: Safety monitor & protective stop | Evidence store | results with hash |

## SysML model

SysML v2 textual view: [`Task401_SafetyVerification.sysml`](Task401_SafetyVerification.sysml) (generated from the catalog; imports [`SusanooSystem`](../../00-system-definition/sysml/SusanooSystem.sysml) and [`SusanooSafety`](../../00-system-definition/sysml/SusanooSafety.sysml)). The Mermaid rendering below is a reading aid; the `.sysml` file is the model of record.

### Requirements (req) — verification relationships

```mermaid
requirementDiagram
  requirement SYS_001 {
    id: "SYS-001"
    text: "Inhibit leg actuation until pilot readiness satisfied"
    risk: High
    verifymethod: Test
  }
  requirement SYS_002 {
    id: "SYS-002"
    text: "Operator-requested protective stop per mode"
    risk: High
    verifymethod: Test
  }
  requirement SYS_003 {
    id: "SYS-003"
    text: "No rotor startup while retained"
    risk: High
    verifymethod: Test
  }
  element VER_001 {
    type: "verification"
  }
  element VER_002 {
    type: "verification"
  }
  element VER_003 {
    type: "verification"
  }
  VER_001 - verifies -> SYS_001
  VER_002 - verifies -> SYS_002
  VER_003 - verifies -> SYS_003
```

<details><summary>SysML v2 source</summary>

```sysml
// Task401_SafetyVerification — generated by tools/gen_safety_docs.py from safety/mil-std-882e/catalog.yaml.
// Do not edit by hand: change the catalog and regenerate.
// Status: planning view only; not evidence of completed analysis or verification.

package Task401_SafetyVerification {
    private import ScalarValues::*;
    private import SusanooSystem::*;
    private import SusanooSafety::*;
    private import Task203_SRHA::*;
    requirement sys_001 : Task203_SRHA::PilotReadinessInterlock;
    requirement sys_002 : Task203_SRHA::ProtectiveStop;
    requirement sys_003 : Task203_SRHA::RetainedRotorInhibit;
    verification def <'VER-001'> Ver001 {
        objective { verify sys_001; }
    }
    verification def <'VER-002'> Ver002 {
        objective { verify sys_002; }
    }
    verification def <'VER-003'> Ver003 {
        objective { verify sys_003; }
    }
}
```

</details>

## Inputs and outputs

```mermaid
flowchart LR
  T401["Task 401 · Safety Verification"]
  in0["Safety Requirements Register"] -->|"Requirements"| T401
  class in0 work
  in1["Task 303 · Test and Evaluation Participation"] -->|"Test results"| T401
  class in1 work
  T401 -->|"Verification status"| out0["Task 106 · Hazard Tracking System (Hazard Log)"]
  class out0 work
  T401 -->|"Verification summary"| out1["Task 301 · Safety Assessment Report (SAR)"]
  class out1 work
  class T401 current
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
| Requirements | [Safety Requirements Register](../../05-risk-reduction/safety-requirements/README.md) |
| Test results | [Task 303 · Test and Evaluation Participation](../task-303-test-and-evaluation-participation/README.md) |

| Output | Destination |
|---|---|
| Verification status | [Task 106 · Hazard Tracking System (Hazard Log)](../../hazard-tracking-system/README.md) |
| Verification summary | [Task 301 · Safety Assessment Report (SAR)](../../07-risk-acceptance/task-301-safety-assessment-report/README.md) |

## Folder contents

| Item | Description | State |
|---|---|---|
| `verification-matrix.csv` | Requirement x method x evidence x result | planned |
| [`Task401_SafetyVerification.sysml`](Task401_SafetyVerification.sysml) | Generated SysML v2 view | generated |

<!-- END GENERATED: content below this line is human-authored and preserved -->

## Working content

_No analysis content yet. Add authored material below this heading._
