# Work-Product Templates

> **Status:** Scaffold v0.1 — structure, diagrams and model views only
>
> Planning artifact. No completed hazard analysis, verified mitigation, risk acceptance, certification or MIL-STD-882E compliance is claimed. Category names follow MIL-STD-882E; confirm definitions against the controlled standard and the approved SSPP before formal use.

| Field | Value |
|---|---|
| Lifecycle gate | All |
| Accountable role | Safety lead |
| Parent folder | [MIL-STD-882E System Safety Work Products](../README.md) |

## Purpose

Record templates used across the tree. Templates mirror `SusanooSafety.sysml` so records,
models and checks share one vocabulary.

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
  class SUS_M1_WLK muted
  class SUS_M1_MAN muted
  class SUS_M1_PIL muted
  class SUS_M1_PWR muted
  class SUS_M1_CTL muted
  class SUS_M1_SAF muted
  class SUS_M1_DCK muted
  class SUS_A1_FCS muted
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

Dashed frame = **Templates** boundary. Everything outside it is an external entity or another folder's scope.

```mermaid
flowchart LR
  subgraph BND["Boundary: Templates"]
    direction TB
    hazard_record_yaml["hazard-record.yaml"]
    task_record_yaml["task-record.yaml"]
    pha_table_csv["pha-table.csv"]
    sspp_outline_md["sspp-outline.md"]
  end
  Work_product_folders["Work-product folders"]
  hazard_record_yaml -->|"hazard records"| Work_product_folders
  task_record_yaml -->|"task records"| Work_product_folders
  pha_table_csv -->|"PHA worksheets"| Work_product_folders
  sspp_outline_md -->|"SSPP"| Work_product_folders
  class hazard_record_yaml work
  class task_record_yaml work
  class pha_table_csv work
  class sspp_outline_md work
  class Work_product_folders external
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
| hazard-record.yaml | Work-product folders | hazard records |
| task-record.yaml | Work-product folders | task records |
| pha-table.csv | Work-product folders | PHA worksheets |
| sspp-outline.md | Work-product folders | SSPP |

## SysML model

SysML v2 textual view: [`TemplateSchemas.sysml`](TemplateSchemas.sysml) (generated from the catalog; imports [`SusanooSystem`](../00-system-definition/sysml/SusanooSystem.sysml) and [`SusanooSafety`](../00-system-definition/sysml/SusanooSafety.sysml)). The Mermaid rendering below is a reading aid; the `.sysml` file is the model of record.

### Block definition (bdd) — template schemas

```mermaid
classDiagram
  class TaskRecord {
    <<item>>
    +Integer taskId
    +String artifactId
    +String revision
    +String configurationId
    +String decision
  }
  TaskRecord *-- "0..*" Hazard : hazards
  TaskRecord *-- "0..*" SafetyRequirement : requirements
  TaskRecord *-- "0..*" VerificationEvidence : evidence
```

<details><summary>SysML v2 source</summary>

```sysml
// TemplateSchemas — generated by tools/gen_safety_docs.py from safety/mil-std-882e/catalog.yaml.
// Do not edit by hand: change the catalog and regenerate.
// Status: planning view only; not evidence of completed analysis or verification.

package TemplateSchemas {
    private import ScalarValues::*;
    private import SusanooSystem::*;
    private import SusanooSafety::*;
    item def TaskRecord {
        attribute taskId : Integer;
        attribute artifactId : String;
        attribute revision : String;
        attribute configurationId : String;
        attribute decision : String;
        part hazards : Hazard[0..*];
        part requirements : SafetyRequirement[0..*];
        part evidence : VerificationEvidence[0..*];
    }
}
```

</details>

## Inputs and outputs

```mermaid
flowchart LR
  TPL["Work-Product Templates"]
  in0["00 · System Definition and Analysis Baseline"] -->|"SusanooSafety vocabulary"| TPL
  class in0 work
  TPL -->|"Hazard record schema"| out0["Task 106 · Hazard Tracking System (Hazard Log)"]
  class out0 work
  class TPL current
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
| SusanooSafety vocabulary | [00 · System Definition and Analysis Baseline](../00-system-definition/README.md) |

| Output | Destination |
|---|---|
| Hazard record schema | [Task 106 · Hazard Tracking System (Hazard Log)](../hazard-tracking-system/README.md) |

## Folder contents

| Item | Description | State |
|---|---|---|
| [`hazard-record.yaml`](hazard-record.yaml) | Hazard record template | present |
| [`task-record.yaml`](task-record.yaml) | Task record template | present |
| [`pha-table.csv`](pha-table.csv) | PHA worksheet columns | present |
| [`sspp-outline.md`](sspp-outline.md) | SSPP outline | present |
| [`TemplateSchemas.sysml`](TemplateSchemas.sysml) | Generated SysML v2 view | generated |

<!-- END GENERATED: content below this line is human-authored and preserved -->

## Working content

_No analysis content yet. Add authored material below this heading._
