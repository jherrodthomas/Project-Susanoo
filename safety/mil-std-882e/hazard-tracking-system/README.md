# Task 106 · Hazard Tracking System (Hazard Log)

> **Status:** Scaffold v0.1 — structure, diagrams and model views only
>
> Planning artifact. No completed hazard analysis, verified mitigation, risk acceptance, certification or MIL-STD-882E compliance is claimed. Category names follow MIL-STD-882E; confirm definitions against the controlled standard and the approved SSPP before formal use.

| Field | Value |
|---|---|
| Tasks | [Task 106 — Hazard Tracking System](../../../docs/wiki/MIL-STD-882E-Task-106.md) |
| Lifecycle gate | G0 onward |
| Applicability | Selected |
| Accountable role | Safety lead |
| Parent folder | [MIL-STD-882E System Safety Work Products](../README.md) |

## Purpose

Closed-loop hazard log used by every element. One YAML record per hazard using
`templates/hazard-record.yaml`; CI resolves every ID link (traceability rule 1).

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
  class E6 work
  class E7 work
  class E8 work
  class HTS current
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

Dashed frame = **Hazard log** boundary. Everything outside it is an external entity or another folder's scope.

```mermaid
flowchart LR
  subgraph BND["Boundary: Hazard log"]
    direction TB
    Hazard_records["Hazard records"]
  end
  Analyses["Analyses"]
  Safety_requirements["Safety requirements"]
  Evidence_store["Evidence store"]
  EXT_AUTH["EXT-AUTH: Risk acceptance authority"]
  Analyses -->|"new hazards"| Hazard_records
  Hazard_records -->|"requirement_ids"| Safety_requirements
  Evidence_store -->|"verification_evidence_ids"| Hazard_records
  EXT_AUTH -->|"risk_acceptance"| Hazard_records
  class Hazard_records work
  class Analyses external
  class Safety_requirements external
  class Evidence_store external
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
| Analyses | Hazard records | new hazards |
| Hazard records | Safety requirements | requirement_ids |
| Evidence store | Hazard records | verification_evidence_ids |
| EXT-AUTH: Risk acceptance authority | Hazard records | risk_acceptance |

## SysML model

SysML v2 textual view: [`HazardTrackingSystem.sysml`](HazardTrackingSystem.sysml) (generated from the catalog; imports [`SusanooSystem`](../00-system-definition/sysml/SusanooSystem.sysml) and [`SusanooSafety`](../00-system-definition/sysml/SusanooSafety.sysml)). The Mermaid rendering below is a reading aid; the `.sysml` file is the model of record.

### Block definition (bdd) — hazard record links

```mermaid
classDiagram
  class HazardLog {
    <<part>>
    +String configurationId
  }
  HazardLog *-- "0..*" Hazard : records
```

### State machine (stm) — record status

```mermaid
stateDiagram-v2
  [*] --> Open
  Open : Open
  Mitigated : Mitigated
  Verified : Verified
  Accepted : Accepted
  Closed : Closed
  Open --> Mitigated : mitigation linked
  Mitigated --> Verified : evidence linked
  Verified --> Accepted : decision_record linked
  Accepted --> Closed : closure criteria met
  Accepted --> Open : change reopens
  Closed --> [*]
```

<details><summary>SysML v2 source</summary>

```sysml
// HazardTrackingSystem — generated by tools/gen_safety_docs.py from safety/mil-std-882e/catalog.yaml.
// Do not edit by hand: change the catalog and regenerate.
// Status: planning view only; not evidence of completed analysis or verification.

package HazardTrackingSystem {
    private import ScalarValues::*;
    private import SusanooSystem::*;
    private import SusanooSafety::*;
    part def HazardLog {
        attribute configurationId : String;
        part records : Hazard[0..*];
    }

    attribute def ChangeReopens;
    attribute def ClosureCriteriaMet;
    attribute def DecisionRecordLinked;
    attribute def EvidenceLinked;
    attribute def MitigationLinked;
    state def HazardRecordStatus {
        entry; then Open;
        state Open;
        state Mitigated;
        state Verified;
        state Accepted;
        state Closed;
        transition t1 first Open accept MitigationLinked then Mitigated;
        transition t2 first Mitigated accept EvidenceLinked then Verified;
        transition t3 first Verified accept DecisionRecordLinked then Accepted;
        transition t4 first Accepted accept ClosureCriteriaMet then Closed;
        transition t5 first Accepted accept ChangeReopens then Open;
    }
}
```

</details>

## Inputs and outputs

```mermaid
flowchart LR
  HTS["Task 106 · Hazard Tracking System (Hazard Log)"]
  in0["02 · Identify and Document Hazards"] -->|"Hazards"| HTS
  class in0 work
  in1["Safety Requirements Register"] -->|"Requirement links"| HTS
  class in1 work
  in2["Task 401 · Safety Verification"] -->|"Evidence links"| HTS
  class in2 work
  in3["Risk Acceptance Records"] -->|"Acceptance links"| HTS
  class in3 work
  HTS -->|"Status snapshot"| out0["Task 107 · Hazard Management Progress Report"]
  class out0 work
  HTS -->|"Hazard log"| out1["Task 301 · Safety Assessment Report (SAR)"]
  class out1 work
  class HTS current
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
| Hazards | [02 · Identify and Document Hazards](../02-hazard-identification/README.md) |
| Requirement links | [Safety Requirements Register](../05-risk-reduction/safety-requirements/README.md) |
| Evidence links | [Task 401 · Safety Verification](../06-verification/task-401-safety-verification/README.md) |
| Acceptance links | [Risk Acceptance Records](../07-risk-acceptance/acceptance-records/README.md) |

| Output | Destination |
|---|---|
| Status snapshot | [Task 107 · Hazard Management Progress Report](../08-lifecycle-risk-management/task-107-hazard-management-progress-report/README.md) |
| Hazard log | [Task 301 · Safety Assessment Report (SAR)](../07-risk-acceptance/task-301-safety-assessment-report/README.md) |

## Folder contents

| Item | Description | State |
|---|---|---|
| `hazards/` | HAZ-<nnn>.yaml records | planned |
| [`HazardTrackingSystem.sysml`](HazardTrackingSystem.sysml) | Generated SysML v2 view | generated |

<!-- END GENERATED: content below this line is human-authored and preserved -->

## Working content

_No analysis content yet. Add authored material below this heading._
