# 01 · Document the System Safety Approach

> **Status:** Scaffold v0.1 — structure, diagrams and model views only
>
> Planning artifact. No completed hazard analysis, verified mitigation, risk acceptance, certification or MIL-STD-882E compliance is claimed. Category names follow MIL-STD-882E; confirm definitions against the controlled standard and the approved SSPP before formal use.

| Field | Value |
|---|---|
| MIL-STD-882E element | 1 — Document the system safety approach |
| Lifecycle gate | G0–G1, updated at each gate |
| Applicability | Selected |
| Accountable role | Safety lead |
| Parent folder | [MIL-STD-882E System Safety Work Products](../README.md) |

## Purpose

Plans and governs the program: how hazards will be identified, assessed, mitigated, verified,
accepted and tracked for SUS-I1, who holds which authority, and which tasks are selected.
Management tasks 101–105 and 108 live here.

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
  class E1 current
  class E2 work
  class E3 work
  class E4 work
  class E5 work
  class E6 work
  class E7 work
  class E8 work
  class HTS work
  classDef system fill:#dceaf7,stroke:#55758f,color:#17324d
  classDef safety fill:#fff0d9,stroke:#b28a3d,color:#513c16
  classDef external fill:#e8f1e9,stroke:#63886a,color:#23412c
  classDef interface fill:#eae7f5,stroke:#8370a3,color:#30254a
  classDef muted fill:#f4f4f4,stroke:#b5b5b5,color:#8a8a8a,stroke-dasharray: 4 3
  classDef current fill:#b28a3d,stroke:#513c16,color:#ffffff,stroke-width:2px
  classDef work fill:#ffffff,stroke:#55758f,color:#17324d
```

## Block diagram

System elements of SUS-I1 in scope for this folder are coloured (blue = system, amber = safety function, purple = interface); greyed blocks are out of scope. Source of truth: [`SusanooSystem.sysml`](../00-system-definition/sysml/SusanooSystem.sysml).

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
  class SUS_M1_WLK system
  class SUS_M1_MAN system
  class SUS_M1_PIL system
  class SUS_M1_PWR system
  class SUS_M1_CTL system
  class SUS_M1_SAF safety
  class SUS_M1_DCK interface
  class SUS_A1_FCS system
  class SUS_A1_PRP system
  class SUS_A1_PWR system
  class SUS_A1_NAV system
  class SUS_A1_PLD system
  class SUS_GSE_SUP system
  class SUS_GSE_CHG system
  class SUS_GSE_TST system
  classDef system fill:#dceaf7,stroke:#55758f,color:#17324d
  classDef safety fill:#fff0d9,stroke:#b28a3d,color:#513c16
  classDef external fill:#e8f1e9,stroke:#63886a,color:#23412c
  classDef interface fill:#eae7f5,stroke:#8370a3,color:#30254a
  classDef muted fill:#f4f4f4,stroke:#b5b5b5,color:#8a8a8a,stroke-dasharray: 4 3
  classDef current fill:#b28a3d,stroke:#513c16,color:#ffffff,stroke-width:2px
  classDef work fill:#ffffff,stroke:#55758f,color:#17324d
```

## Boundary diagram

Dashed frame = **Safety program management** boundary. Everything outside it is an external entity or another folder's scope.

```mermaid
flowchart LR
  subgraph BND["Boundary: Safety program management"]
    direction TB
    SSPP_and_HMP["SSPP and HMP"]
    Task_selection_and_tailoring["Task selection and tailoring"]
    IPT_and_roles["IPT and roles"]
  end
  EXT_AUTH["EXT-AUTH: Risk acceptance authority"]
  Program_management["Program management"]
  Suppliers["Suppliers"]
  Standards_bodies["Standards bodies"]
  Program_management -->|"schedule, resources, contract terms"| SSPP_and_HMP
  Standards_bodies -->|"controlled standard editions"| Task_selection_and_tailoring
  SSPP_and_HMP -->|"risk acceptance authority matrix"| EXT_AUTH
  IPT_and_roles -->|"safety data requirements"| Suppliers
  class SSPP_and_HMP work
  class Task_selection_and_tailoring work
  class IPT_and_roles work
  class EXT_AUTH external
  class Program_management external
  class Suppliers external
  class Standards_bodies external
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
| Program management | SSPP and HMP | schedule, resources, contract terms |
| Standards bodies | Task selection and tailoring | controlled standard editions |
| SSPP and HMP | EXT-AUTH: Risk acceptance authority | risk acceptance authority matrix |
| IPT and roles | Suppliers | safety data requirements |

## SysML model

SysML v2 textual view: [`SafetyApproach.sysml`](SafetyApproach.sysml) (generated from the catalog; imports [`SusanooSystem`](../00-system-definition/sysml/SusanooSystem.sysml) and [`SusanooSafety`](../00-system-definition/sysml/SusanooSafety.sysml)). The Mermaid rendering below is a reading aid; the `.sysml` file is the model of record.

### Block definition (bdd) — safety program plan set

```mermaid
classDiagram
  class SafetyProgram {
    <<part>>
    +String configurationId
    +String standardEdition
  }
  SafetyProgram o-- "1" SystemSafetyProgramPlan : sspp
  SafetyProgram o-- "1" HazardManagementPlan : hmp
  SafetyProgram o-- "0..1" HazMatManagementPlan : hmmp
  SafetyProgram *-- "1" SafetyIPT : ipt
  class SystemSafetyProgramPlan {
    <<item>>
    +String revision
    +String approvalRecord
  }
  class HazardManagementPlan {
    <<item>>
    +String riskMatrixRef
    +String closureCriteria
  }
  class HazMatManagementPlan {
    <<item>>
    +String inventoryRef
  }
  class SafetyIPT {
    <<part>>
    +String charter
  }
```

<details><summary>SysML v2 source</summary>

```sysml
// SafetyApproach — generated by tools/gen_safety_docs.py from safety/mil-std-882e/catalog.yaml.
// Do not edit by hand: change the catalog and regenerate.
// Status: planning view only; not evidence of completed analysis or verification.

package SafetyApproach {
    private import ScalarValues::*;
    private import SusanooSystem::*;
    private import SusanooSafety::*;
    part def SafetyProgram {
        doc /* Plans and agreements that document the SUS-I1 safety approach. */
        attribute configurationId : String;
        attribute standardEdition : String;
        ref item sspp : SystemSafetyProgramPlan[1];
        ref item hmp : HazardManagementPlan[1];
        ref item hmmp : HazMatManagementPlan[0..1];
        part ipt : SafetyIPT[1];
    }
    item def SystemSafetyProgramPlan {
        attribute revision : String;
        attribute approvalRecord : String;
    }
    item def HazardManagementPlan {
        attribute riskMatrixRef : String;
        attribute closureCriteria : String;
    }
    item def HazMatManagementPlan {
        attribute inventoryRef : String;
    }
    part def SafetyIPT {
        attribute charter : String;
    }
}
```

</details>

## Inputs and outputs

```mermaid
flowchart LR
  E1["01 · Document the System Safety Approach"]
  in0["00 · System Definition and Analysis Baseline"] -->|"System baseline"| E1
  class in0 work
  in1["framework/standards-applicability.md"] -->|"Standards and tailoring"| E1
  class in1 external
  in2["framework/lifecycle.md"] -->|"Gates G0–G7"| E1
  class in2 external
  E1 -->|"Selected analysis tasks and methods"| out0["02 · Identify and Document Hazards"]
  class out0 work
  E1 -->|"Approved risk matrix reference"| out1["03 · Assess and Document Risk"]
  class out1 work
  E1 -->|"Acceptance authority matrix"| out2["07 · Accept Risk and Document"]
  class out2 work
  class E1 current
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
| System baseline | [00 · System Definition and Analysis Baseline](../00-system-definition/README.md) |
| Standards and tailoring | [`framework/standards-applicability.md`](../../../framework/standards-applicability.md) |
| Gates G0–G7 | [`framework/lifecycle.md`](../../../framework/lifecycle.md) |

| Output | Destination |
|---|---|
| Selected analysis tasks and methods | [02 · Identify and Document Hazards](../02-hazard-identification/README.md) |
| Approved risk matrix reference | [03 · Assess and Document Risk](../03-risk-assessment/README.md) |
| Acceptance authority matrix | [07 · Accept Risk and Document](../07-risk-acceptance/README.md) |

## Folder contents

| Item | Description | State |
|---|---|---|
| [`task-101-hazard-identification-and-mitigation-effort/`](task-101-hazard-identification-and-mitigation-effort/README.md) | Task 101 · Hazard Identification and Mitigation Effort | folder |
| [`task-102-system-safety-program-plan/`](task-102-system-safety-program-plan/README.md) | Task 102 · System Safety Program Plan (SSPP) | folder |
| [`task-103-hazard-management-plan/`](task-103-hazard-management-plan/README.md) | Task 103 · Hazard Management Plan (HMP) | folder |
| [`task-104-government-reviews-and-audits/`](task-104-government-reviews-and-audits/README.md) | Task 104 · Government Reviews and Audits | folder |
| [`task-105-integrated-product-team-support/`](task-105-integrated-product-team-support/README.md) | Task 105 · Integrated Product Team (IPT) Support | folder |
| [`task-108-hazardous-materials-management-plan/`](task-108-hazardous-materials-management-plan/README.md) | Task 108 · Hazardous Materials Management Plan (HMMP) | folder |
| `task-applicability.yaml` | Task selection and tailoring decisions (see Wiki applicability page) | planned |
| [`SafetyApproach.sysml`](SafetyApproach.sysml) | Generated SysML v2 view | generated |

<!-- END GENERATED: content below this line is human-authored and preserved -->

## Working content

_No analysis content yet. Add authored material below this heading._
