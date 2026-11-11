# Task 103 · Hazard Management Plan (HMP)

> **Status:** Scaffold v0.1 — structure, diagrams and model views only
>
> Planning artifact. No completed hazard analysis, verified mitigation, risk acceptance, certification or MIL-STD-882E compliance is claimed. Category names follow MIL-STD-882E; confirm definitions against the controlled standard and the approved SSPP before formal use.

| Field | Value |
|---|---|
| MIL-STD-882E element | 1 — Document the system safety approach |
| Tasks | [Task 103 — Hazard Management Plan](../../../../docs/wiki/MIL-STD-882E-Task-103.md) |
| Lifecycle gate | G0–G1 |
| Applicability | Selected |
| Accountable role | Safety lead |
| Parent folder | [01 · Document the System Safety Approach](../README.md) |

## Purpose

Defines how hazards move through their lifecycle, closure criteria, who may change status,
and how the hazard tracking system is operated.

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
  T103["Task 103 · Hazard Management Plan"]
  E1 --- T103
  class E1 safety
  class E2 work
  class E3 work
  class E4 work
  class E5 work
  class E6 work
  class E7 work
  class E8 work
  class HTS work
  class T103 current
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

Dashed frame = **Hazard management process** boundary. Everything outside it is an external entity or another folder's scope.

```mermaid
flowchart LR
  subgraph BND["Boundary: Hazard management process"]
    direction TB
    Hazard_lifecycle_rules["Hazard lifecycle rules"]
    Closure_criteria["Closure criteria"]
    HTS_operation["HTS operation"]
  end
  EXT_AUTH["EXT-AUTH: Risk acceptance authority"]
  Change_control_board["Change control board"]
  Verification_program["Verification program"]
  Verification_program -->|"evidence of effectiveness"| Closure_criteria
  Closure_criteria -->|"acceptance request"| EXT_AUTH
  Change_control_board -->|"reopen triggers"| Hazard_lifecycle_rules
  class Hazard_lifecycle_rules work
  class Closure_criteria work
  class HTS_operation work
  class EXT_AUTH external
  class Change_control_board external
  class Verification_program external
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
| Verification program | Closure criteria | evidence of effectiveness |
| Closure criteria | EXT-AUTH: Risk acceptance authority | acceptance request |
| Change control board | Hazard lifecycle rules | reopen triggers |

## SysML model

SysML v2 textual view: [`Task103_HMP.sysml`](Task103_HMP.sysml) (generated from the catalog; imports [`SusanooSystem`](../../00-system-definition/sysml/SusanooSystem.sysml) and [`SusanooSafety`](../../00-system-definition/sysml/SusanooSafety.sysml)). The Mermaid rendering below is a reading aid; the `.sysml` file is the model of record.

### State machine (stm) — hazard status lifecycle

```mermaid
stateDiagram-v2
  [*] --> Open
  Open : Open - identified and recorded
  Mitigated : Mitigated - controls allocated and implemented
  Verified : Verified - effectiveness evidenced
  PendingAcceptance : PendingAcceptance - residual risk awaiting decision
  Accepted : Accepted - authorized decision recorded
  Closed : Closed
  Monitor : Monitor - tracked in service
  Open --> Mitigated : mitigation recorded
  Mitigated --> Verified : evidence accepted
  Verified --> Mitigated : verification failed
  Verified --> PendingAcceptance : acceptance requested
  PendingAcceptance --> Accepted : authority approves
  PendingAcceptance --> Mitigated : authority rejects
  Accepted --> Monitor : fielded
  Monitor --> Open : change or mishap
  Accepted --> Closed : hazard eliminated or retired
  Closed --> [*]
```

<details><summary>SysML v2 source</summary>

```sysml
// Task103_HMP — generated by tools/gen_safety_docs.py from safety/mil-std-882e/catalog.yaml.
// Do not edit by hand: change the catalog and regenerate.
// Status: planning view only; not evidence of completed analysis or verification.

package Task103_HMP {
    private import ScalarValues::*;
    private import SusanooSystem::*;
    private import SusanooSafety::*;
    attribute def AcceptanceRequested;
    attribute def AuthorityApproves;
    attribute def AuthorityRejects;
    attribute def ChangeOrMishap;
    attribute def EvidenceAccepted;
    attribute def Fielded;
    attribute def HazardEliminatedOrRetired;
    attribute def MitigationRecorded;
    attribute def VerificationFailed;
    state def HazardLifecycle {
        doc /* Status transitions governed by the HMP; values match SusanooSafety::HazardStatus. */
        entry; then Open;
        state Open { doc /* identified and recorded */ }
        state Mitigated { doc /* controls allocated and implemented */ }
        state Verified { doc /* effectiveness evidenced */ }
        state PendingAcceptance { doc /* residual risk awaiting decision */ }
        state Accepted { doc /* authorized decision recorded */ }
        state Closed;
        state Monitor { doc /* tracked in service */ }
        transition t1 first Open accept MitigationRecorded then Mitigated;
        transition t2 first Mitigated accept EvidenceAccepted then Verified;
        transition t3 first Verified accept VerificationFailed then Mitigated;
        transition t4 first Verified accept AcceptanceRequested then PendingAcceptance;
        transition t5 first PendingAcceptance accept AuthorityApproves then Accepted;
        transition t6 first PendingAcceptance accept AuthorityRejects then Mitigated;
        transition t7 first Accepted accept Fielded then Monitor;
        transition t8 first Monitor accept ChangeOrMishap then Open;
        transition t9 first Accepted accept HazardEliminatedOrRetired then Closed;
    }
}
```

</details>

## Inputs and outputs

```mermaid
flowchart LR
  T103["Task 103 · Hazard Management Plan (HMP)"]
  in0["Task 102 · System Safety Program Plan (SSPP)"] -->|"SSPP"| T103
  class in0 work
  in1["03 · Assess and Document Risk"] -->|"Risk matrix"| T103
  class in1 work
  T103 -->|"Hazard workflow rules"| out0["Task 106 · Hazard Tracking System (Hazard Log)"]
  class out0 work
  T103 -->|"Closure criteria"| out1["07 · Accept Risk and Document"]
  class out1 work
  class T103 current
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
| SSPP | [Task 102 · System Safety Program Plan (SSPP)](../task-102-system-safety-program-plan/README.md) |
| Risk matrix | [03 · Assess and Document Risk](../../03-risk-assessment/README.md) |

| Output | Destination |
|---|---|
| Hazard workflow rules | [Task 106 · Hazard Tracking System (Hazard Log)](../../hazard-tracking-system/README.md) |
| Closure criteria | [07 · Accept Risk and Document](../../07-risk-acceptance/README.md) |

## Folder contents

| Item | Description | State |
|---|---|---|
| `hmp.md` | Hazard Management Plan | planned |
| [`Task103_HMP.sysml`](Task103_HMP.sysml) | Generated SysML v2 view | generated |

<!-- END GENERATED: content below this line is human-authored and preserved -->

## Working content

_No analysis content yet. Add authored material below this heading._
