# Task 303 · Test and Evaluation Participation

> **Status:** Scaffold v0.1 — structure, diagrams and model views only
>
> Planning artifact. No completed hazard analysis, verified mitigation, risk acceptance, certification or MIL-STD-882E compliance is claimed. Category names follow MIL-STD-882E; confirm definitions against the controlled standard and the approved SSPP before formal use.

| Field | Value |
|---|---|
| MIL-STD-882E element | 6 — Verify, validate and document risk reduction |
| Tasks | [Task 303 — Test and Evaluation Participation](../../../../docs/wiki/MIL-STD-882E-Task-303.md) |
| Lifecycle gate | G4–G5 |
| Applicability | Selected |
| Accountable role | Safety lead with test lead |
| Parent folder | [06 · Verify, Validate and Document Risk Reduction](../README.md) |

## Purpose

Safety participation in test planning and execution: test hazard analysis, safety releases for
rig and human-in-the-loop tests, and use of test data to update hazards.

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
  T303["Task 303 · Test and Evaluation Participation"]
  E6 --- T303
  class E1 work
  class E2 work
  class E3 work
  class E4 work
  class E5 work
  class E6 safety
  class E7 work
  class E8 work
  class HTS work
  class T303 current
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
  class SUS_GSE_SUP muted
  class SUS_GSE_CHG muted
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

Dashed frame = **Test events** boundary. Everything outside it is an external entity or another folder's scope.

```mermaid
flowchart LR
  subgraph BND["Boundary: Test events"]
    direction TB
    SUS_GSE_TST["SUS-GSE-TST: Test rigs, HIL & simulation"]
    Test_safety_release["Test safety release"]
  end
  EXT_PILOT["EXT-PILOT: Pilot / operator"]
  EXT_CREW["EXT-CREW: Ground crew & maintainers"]
  Test_range_or_site["Test range or site"]
  Test_safety_release -->|"authorization for occupied test"| EXT_PILOT
  SUS_GSE_TST -->|"exclusion zone"| EXT_CREW
  Test_range_or_site -->|"site rules"| SUS_GSE_TST
  class SUS_GSE_TST system
  class Test_safety_release work
  class EXT_PILOT external
  class EXT_CREW external
  class Test_range_or_site external
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
| Test safety release | EXT-PILOT: Pilot / operator | authorization for occupied test |
| SUS-GSE-TST: Test rigs, HIL & simulation | EXT-CREW: Ground crew & maintainers | exclusion zone |
| Test range or site | SUS-GSE-TST: Test rigs, HIL & simulation | site rules |

## SysML model

SysML v2 textual view: [`Task303_TestParticipation.sysml`](Task303_TestParticipation.sysml) (generated from the catalog; imports [`SusanooSystem`](../../00-system-definition/sysml/SusanooSystem.sysml) and [`SusanooSafety`](../../00-system-definition/sysml/SusanooSafety.sysml)). The Mermaid rendering below is a reading aid; the `.sysml` file is the model of record.

### State machine (stm) — TestSafetyRelease

```mermaid
stateDiagram-v2
  [*] --> Planned
  Planned : Planned
  HazardsReviewed : HazardsReviewed
  Released : Released - authorized for stated configuration
  Executed : Executed
  Suspended : Suspended - stop-test condition
  Planned --> HazardsReviewed : test hazard analysis complete
  HazardsReviewed --> Released : independent review approves
  Released --> Executed : test complete
  Released --> Suspended : stop condition
  Suspended --> HazardsReviewed : anomaly dispositioned
  Executed --> [*]
```

<details><summary>SysML v2 source</summary>

```sysml
// Task303_TestParticipation — generated by tools/gen_safety_docs.py from safety/mil-std-882e/catalog.yaml.
// Do not edit by hand: change the catalog and regenerate.
// Status: planning view only; not evidence of completed analysis or verification.

package Task303_TestParticipation {
    private import ScalarValues::*;
    private import SusanooSystem::*;
    private import SusanooSafety::*;
    attribute def AnomalyDispositioned;
    attribute def IndependentReviewApproves;
    attribute def StopCondition;
    attribute def TestComplete;
    attribute def TestHazardAnalysisComplete;
    state def TestSafetyRelease {
        entry; then Planned;
        state Planned;
        state HazardsReviewed;
        state Released { doc /* authorized for stated configuration */ }
        state Executed;
        state Suspended { doc /* stop-test condition */ }
        transition t1 first Planned accept TestHazardAnalysisComplete then HazardsReviewed;
        transition t2 first HazardsReviewed accept IndependentReviewApproves then Released;
        transition t3 first Released accept TestComplete then Executed;
        transition t4 first Released accept StopCondition then Suspended;
        transition t5 first Suspended accept AnomalyDispositioned then HazardsReviewed;
    }
}
```

</details>

## Inputs and outputs

```mermaid
flowchart LR
  T303["Task 303 · Test and Evaluation Participation"]
  in0["Task 206 · Operating and Support Hazard Analysis (O&SHA)"] -->|"Operating hazards"| T303
  class in0 work
  in1["Safety Requirements Register"] -->|"Requirements under test"| T303
  class in1 work
  T303 -->|"Test results"| out0["Task 401 · Safety Verification"]
  class out0 work
  T303 -->|"Test anomalies"| out1["Task 304 · Review of Changes, Deficiencies, Mishaps and Deviations"]
  class out1 work
  class T303 current
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
| Operating hazards | [Task 206 · Operating and Support Hazard Analysis (O&SHA)](../../02-hazard-identification/task-206-operating-and-support-hazard-analysis/README.md) |
| Requirements under test | [Safety Requirements Register](../../05-risk-reduction/safety-requirements/README.md) |

| Output | Destination |
|---|---|
| Test results | [Task 401 · Safety Verification](../task-401-safety-verification/README.md) |
| Test anomalies | [Task 304 · Review of Changes, Deficiencies, Mishaps and Deviations](../../08-lifecycle-risk-management/task-304-review-changes-deficiencies-mishaps-deviations/README.md) |

## Folder contents

| Item | Description | State |
|---|---|---|
| `test-safety-releases/` | One release record per test event | planned |
| [`Task303_TestParticipation.sysml`](Task303_TestParticipation.sysml) | Generated SysML v2 view | generated |

<!-- END GENERATED: content below this line is human-authored and preserved -->

## Working content

_No analysis content yet. Add authored material below this heading._
