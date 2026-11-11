# Task 102 · System Safety Program Plan (SSPP)

> **Status:** Scaffold v0.1 — structure, diagrams and model views only
>
> Planning artifact. No completed hazard analysis, verified mitigation, risk acceptance, certification or MIL-STD-882E compliance is claimed. Category names follow MIL-STD-882E; confirm definitions against the controlled standard and the approved SSPP before formal use.

| Field | Value |
|---|---|
| MIL-STD-882E element | 1 — Document the system safety approach |
| Tasks | [Task 102 — System Safety Program Plan](../../../../docs/wiki/MIL-STD-882E-Task-102.md) |
| Lifecycle gate | G0, revised at G2 and G6 |
| Applicability | Selected |
| Accountable role | Safety lead; approval by program authority |
| Parent folder | [01 · Document the System Safety Approach](../README.md) |

## Purpose

The SSPP: scope, organisation, authority, selected tasks, methods, risk matrix, hazard tracking,
software approach, verification and acceptance. Start from `templates/sspp-outline.md`.

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
  T102["Task 102 · System Safety Program Plan"]
  E1 --- T102
  class E1 safety
  class E2 work
  class E3 work
  class E4 work
  class E5 work
  class E6 work
  class E7 work
  class E8 work
  class HTS work
  class T102 current
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

Dashed frame = **SSPP scope** boundary. Everything outside it is an external entity or another folder's scope.

```mermaid
flowchart LR
  subgraph BND["Boundary: SSPP scope"]
    direction TB
    SUS_M1["SUS-M1: Piloted walker"]
    SUS_A1["SUS-A1: Observation UAV"]
    SUS_GSE["SUS-GSE: Ground support equipment"]
  end
  EXT_AUTH["EXT-AUTH: Risk acceptance authority"]
  Program_management["Program management"]
  PX4_upstream_project["PX4 upstream project"]
  Program_management -->|"resources and schedule"| BND
  BND -->|"acceptance requests per risk level"| EXT_AUTH
  PX4_upstream_project -->|"COTS / open-source software baseline"| SUS_A1
  class SUS_M1 system
  class SUS_A1 system
  class SUS_GSE system
  class EXT_AUTH external
  class Program_management external
  class PX4_upstream_project external
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
| Program management | _SSPP scope (boundary)_ | resources and schedule |
| _SSPP scope (boundary)_ | EXT-AUTH: Risk acceptance authority | acceptance requests per risk level |
| PX4 upstream project | SUS-A1: Observation UAV | COTS / open-source software baseline |

## SysML model

SysML v2 textual view: [`Task102_SSPP.sysml`](Task102_SSPP.sysml) (generated from the catalog; imports [`SusanooSystem`](../../00-system-definition/sysml/SusanooSystem.sysml) and [`SusanooSafety`](../../00-system-definition/sysml/SusanooSafety.sysml)). The Mermaid rendering below is a reading aid; the `.sysml` file is the model of record.

### Requirements (req) — plan-level requirements

```mermaid
requirementDiagram
  requirement SSPP_001 {
    id: "SSPP-001"
    text: "SSPP shall name the risk acceptance authority for each risk level"
    risk: High
    verifymethod: Inspection
  }
  requirement SSPP_002 {
    id: "SSPP-002"
    text: "SSPP shall record selected and tailored tasks with rationale"
    risk: Medium
    verifymethod: Inspection
  }
  requirement SSPP_003 {
    id: "SSPP-003"
    text: "SSPP shall keep 882E risk and ARP4761A failure-condition scales distinct"
    risk: Medium
    verifymethod: Inspection
  }
  requirement SSPP_004 {
    id: "SSPP-004"
    text: "SSPP shall define the software contribution to system risk approach"
    risk: High
    verifymethod: Inspection
  }
  element SSPP_REVIEW {
    type: "verification"
  }
  SSPP_REVIEW - verifies -> SSPP_001
  SSPP_REVIEW - verifies -> SSPP_002
  SSPP_REVIEW - verifies -> SSPP_003
  SSPP_REVIEW - verifies -> SSPP_004
```

<details><summary>SysML v2 source</summary>

```sysml
// Task102_SSPP — generated by tools/gen_safety_docs.py from safety/mil-std-882e/catalog.yaml.
// Do not edit by hand: change the catalog and regenerate.
// Status: planning view only; not evidence of completed analysis or verification.

package Task102_SSPP {
    private import ScalarValues::*;
    private import SusanooSystem::*;
    private import SusanooSafety::*;
    requirement def <'SSPP-001'> DefineRiskAuthority {
        doc /* SSPP shall name the risk acceptance authority for each risk level */
    }
    requirement sspp_001 : DefineRiskAuthority;
    requirement def <'SSPP-002'> DefineTaskSelection {
        doc /* SSPP shall record selected and tailored tasks with rationale */
    }
    requirement sspp_002 : DefineTaskSelection;
    requirement def <'SSPP-003'> SeparateRiskScales {
        doc /* SSPP shall keep 882E risk and ARP4761A failure-condition scales distinct */
    }
    requirement sspp_003 : SeparateRiskScales;
    requirement def <'SSPP-004'> DefineSoftwareApproach {
        doc /* SSPP shall define the software contribution to system risk approach */
    }
    requirement sspp_004 : DefineSoftwareApproach;
    verification def <'SSPP-REVIEW'> SsppReview {
        objective { verify sspp_001; }
    }
    verification def <'SSPP-REVIEW'> SsppReview {
        objective { verify sspp_002; }
    }
    verification def <'SSPP-REVIEW'> SsppReview {
        objective { verify sspp_003; }
    }
    verification def <'SSPP-REVIEW'> SsppReview {
        objective { verify sspp_004; }
    }
}
```

</details>

## Inputs and outputs

```mermaid
flowchart LR
  T102["Task 102 · System Safety Program Plan (SSPP)"]
  in0["safety/mil-std-882e/templates/sspp-outline.md"] -->|"SSPP outline"| T102
  class in0 external
  in1["01 · Document the System Safety Approach"] -->|"Task applicability"| T102
  class in1 work
  T102 -->|"Plan baseline"| out0["Task 103 · Hazard Management Plan (HMP)"]
  class out0 work
  T102 -->|"Risk matrix definition"| out1["03 · Assess and Document Risk"]
  class out1 work
  T102 -->|"Software safety approach"| out2["Software Contribution to System Risk (Section 4.4)"]
  class out2 work
  class T102 current
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
| SSPP outline | [`safety/mil-std-882e/templates/sspp-outline.md`](../../templates/sspp-outline.md) |
| Task applicability | [01 · Document the System Safety Approach](../README.md) |

| Output | Destination |
|---|---|
| Plan baseline | [Task 103 · Hazard Management Plan (HMP)](../task-103-hazard-management-plan/README.md) |
| Risk matrix definition | [03 · Assess and Document Risk](../../03-risk-assessment/README.md) |
| Software safety approach | [Software Contribution to System Risk (Section 4.4)](../../software-safety/README.md) |

## Folder contents

| Item | Description | State |
|---|---|---|
| `sspp.md` | System Safety Program Plan (draft until approved) | planned |
| [`Task102_SSPP.sysml`](Task102_SSPP.sysml) | Generated SysML v2 view | generated |

<!-- END GENERATED: content below this line is human-authored and preserved -->

## Working content

_No analysis content yet. Add authored material below this heading._
