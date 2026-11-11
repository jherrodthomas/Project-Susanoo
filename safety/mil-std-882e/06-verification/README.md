# 06 · Verify, Validate and Document Risk Reduction

> **Status:** Scaffold v0.1 — structure, diagrams and model views only
>
> Planning artifact. No completed hazard analysis, verified mitigation, risk acceptance, certification or MIL-STD-882E compliance is claimed. Category names follow MIL-STD-882E; confirm definitions against the controlled standard and the approved SSPP before formal use.

| Field | Value |
|---|---|
| MIL-STD-882E element | 6 — Verify, validate and document risk reduction |
| Lifecycle gate | G4–G5 |
| Applicability | Selected |
| Accountable role | Test lead with safety lead |
| Parent folder | [MIL-STD-882E System Safety Work Products](../README.md) |

## Purpose

Plans and records evidence that mitigations are implemented and effective: analysis,
inspection, demonstration, simulation and test, including fault injection. Simulated evidence
is labelled as simulated.

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
  class E1 work
  class E2 work
  class E3 work
  class E4 work
  class E5 work
  class E6 current
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

Dashed frame = **Verification program** boundary. Everything outside it is an external entity or another folder's scope.

```mermaid
flowchart LR
  subgraph BND["Boundary: Verification program"]
    direction TB
    SUS_GSE_TST["SUS-GSE-TST: Test rigs, HIL & simulation"]
    Test_procedures["Test procedures"]
    Evidence_records["Evidence records"]
  end
  SUS_M1["SUS-M1: Piloted walker"]
  SUS_A1["SUS-A1: Observation UAV"]
  EXT_AUTH["EXT-AUTH: Risk acceptance authority"]
  SUS_GSE_TST -->|"supported rig tests"| SUS_M1
  SUS_GSE_TST -->|"HIL / SITL"| SUS_A1
  Evidence_records -->|"verification summary"| EXT_AUTH
  class SUS_GSE_TST system
  class Test_procedures work
  class Evidence_records work
  class SUS_M1 external
  class SUS_A1 external
  class EXT_AUTH external
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
| SUS-GSE-TST: Test rigs, HIL & simulation | SUS-M1: Piloted walker | supported rig tests |
| SUS-GSE-TST: Test rigs, HIL & simulation | SUS-A1: Observation UAV | HIL / SITL |
| Evidence records | EXT-AUTH: Risk acceptance authority | verification summary |

## SysML model

SysML v2 textual view: [`SafetyVerification.sysml`](SafetyVerification.sysml) (generated from the catalog; imports [`SusanooSystem`](../00-system-definition/sysml/SusanooSystem.sysml) and [`SusanooSafety`](../00-system-definition/sysml/SusanooSafety.sysml)). The Mermaid rendering below is a reading aid; the `.sysml` file is the model of record.

### Activity (act) — VerifyRiskReduction

```mermaid
flowchart TD
  start((start))
  planVerification["Select method per requirement"]
  confirmTestSafety["Confirm test hazards controlled"]
  execute["Execute analysis, test or demonstration"]
  recordEvidence["Record evidence with provenance and hash"]
  assessEffectiveness["Assess mitigation effectiveness"]
  start --> planVerification
  planVerification --> confirmTestSafety
  confirmTestSafety --> execute
  execute --> recordEvidence
  recordEvidence --> assessEffectiveness
  assessEffectiveness --> done((done))
  assessEffectiveness -. "failed or inconclusive" .-> planVerification
  class confirmTestSafety safety
  classDef system fill:#dceaf7,stroke:#55758f,color:#17324d
  classDef safety fill:#fff0d9,stroke:#b28a3d,color:#513c16
  classDef external fill:#e8f1e9,stroke:#63886a,color:#23412c
  classDef interface fill:#eae7f5,stroke:#8370a3,color:#30254a
  classDef muted fill:#f4f4f4,stroke:#b5b5b5,color:#8a8a8a,stroke-dasharray: 4 3
  classDef current fill:#b28a3d,stroke:#513c16,color:#ffffff,stroke-width:2px
  classDef work fill:#ffffff,stroke:#55758f,color:#17324d
```

<details><summary>SysML v2 source</summary>

```sysml
// SafetyVerification — generated by tools/gen_safety_docs.py from safety/mil-std-882e/catalog.yaml.
// Do not edit by hand: change the catalog and regenerate.
// Status: planning view only; not evidence of completed analysis or verification.

package SafetyVerification {
    private import ScalarValues::*;
    private import SusanooSystem::*;
    private import SusanooSafety::*;
    action def VerifyRiskReduction {
        action planVerification { doc /* Select method per requirement */ }
        action confirmTestSafety { doc /* Confirm test hazards controlled */ }
        action execute { doc /* Execute analysis, test or demonstration */ }
        action recordEvidence { doc /* Record evidence with provenance and hash */ }
        action assessEffectiveness { doc /* Assess mitigation effectiveness */ }
        first start;
        then planVerification;
        first planVerification then confirmTestSafety;
        first confirmTestSafety then execute;
        first execute then recordEvidence;
        first recordEvidence then assessEffectiveness;
        first assessEffectiveness then done;
        // iteration: assessEffectiveness -> planVerification when failed or inconclusive (informal; merge node omitted)
    }
}
```

</details>

## Inputs and outputs

```mermaid
flowchart LR
  E6["06 · Verify, Validate and Document Risk Reduction"]
  in0["Safety Requirements Register"] -->|"Requirements"| E6
  class in0 work
  in1["05 · Reduce Risk"] -->|"Implemented mitigations"| E6
  class in1 work
  E6 -->|"Verified residual risk"| out0["07 · Accept Risk and Document"]
  class out0 work
  E6 -->|"evidence_ids"| out1["Task 106 · Hazard Tracking System (Hazard Log)"]
  class out1 work
  class E6 current
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
| Requirements | [Safety Requirements Register](../05-risk-reduction/safety-requirements/README.md) |
| Implemented mitigations | [05 · Reduce Risk](../05-risk-reduction/README.md) |

| Output | Destination |
|---|---|
| Verified residual risk | [07 · Accept Risk and Document](../07-risk-acceptance/README.md) |
| evidence_ids | [Task 106 · Hazard Tracking System (Hazard Log)](../hazard-tracking-system/README.md) |

## Folder contents

| Item | Description | State |
|---|---|---|
| [`task-303-test-and-evaluation-participation/`](task-303-test-and-evaluation-participation/README.md) | Task 303 · Test and Evaluation Participation | folder |
| [`task-401-safety-verification/`](task-401-safety-verification/README.md) | Task 401 · Safety Verification | folder |
| [`task-402-explosives-hazard-classification-data/`](task-402-explosives-hazard-classification-data/README.md) | Task 402 · Explosives Hazard Classification Data | folder |
| [`task-403-explosive-ordnance-disposal-data/`](task-403-explosive-ordnance-disposal-data/README.md) | Task 403 · Explosive Ordnance Disposal Data | folder |
| [`SafetyVerification.sysml`](SafetyVerification.sysml) | Generated SysML v2 view | generated |

<!-- END GENERATED: content below this line is human-authored and preserved -->

## Working content

_No analysis content yet. Add authored material below this heading._
