# 03 · Assess and Document Risk

> **Status:** Scaffold v0.1 — structure, diagrams and model views only
>
> Planning artifact. No completed hazard analysis, verified mitigation, risk acceptance, certification or MIL-STD-882E compliance is claimed. Category names follow MIL-STD-882E; confirm definitions against the controlled standard and the approved SSPP before formal use.

| Field | Value |
|---|---|
| MIL-STD-882E element | 3 — Assess and document risk |
| Lifecycle gate | G1 onward |
| Applicability | Selected |
| Accountable role | Safety lead |
| Parent folder | [MIL-STD-882E System Safety Work Products](../README.md) |

## Purpose

Holds the program risk assessment definitions: severity categories, probability levels, the
risk assessment matrix and risk levels, plus quantitative probability bands for SUS-I1 once
exposure is defined. Software contribution uses the separate criteria in `software-safety/`.

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
  class E3 current
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

Dashed frame = **Risk assessment criteria** boundary. Everything outside it is an external entity or another folder's scope.

```mermaid
flowchart LR
  subgraph BND["Boundary: Risk assessment criteria"]
    direction TB
    Severity_categories["Severity categories"]
    Probability_levels["Probability levels"]
    Risk_matrix["Risk matrix"]
  end
  EXT_AUTH["EXT-AUTH: Risk acceptance authority"]
  ARP4761A_classification["ARP4761A classification"]
  Hazard_records["Hazard records"]
  Hazard_records -->|"severity and probability"| Risk_matrix
  Risk_matrix -->|"risk level drives authority"| EXT_AUTH
  ARP4761A_classification -->|"kept separate - no mapping"| Risk_matrix
  class Severity_categories work
  class Probability_levels work
  class Risk_matrix work
  class EXT_AUTH external
  class ARP4761A_classification external
  class Hazard_records external
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
| Hazard records | Risk matrix | severity and probability |
| Risk matrix | EXT-AUTH: Risk acceptance authority | risk level drives authority |
| ARP4761A classification | Risk matrix | kept separate - no mapping |

## SysML model

SysML v2 textual view: [`RiskAssessment.sysml`](RiskAssessment.sysml) (generated from the catalog; imports [`SusanooSystem`](../00-system-definition/sysml/SusanooSystem.sysml) and [`SusanooSafety`](../00-system-definition/sysml/SusanooSafety.sysml)). The Mermaid rendering below is a reading aid; the `.sysml` file is the model of record.

### Block definition (bdd) — risk assessment types

```mermaid
classDiagram
  class SeverityCategory {
    <<enumeration>>
    Catastrophic
    Critical
    Marginal
    Negligible
  }
  class ProbabilityLevel {
    <<enumeration>>
    Frequent
    Probable
    Occasional
    Remote
    Improbable
    Eliminated
  }
  class RiskLevel {
    <<enumeration>>
    High
    Serious
    Medium
    Low
    Eliminated
  }
  class RiskAssessmentRecord {
    <<attribute>>
    +SeverityCategory severity
    +ProbabilityLevel probability
    +RiskLevel level
    +String rationale
  }
```

<details><summary>SysML v2 source</summary>

```sysml
// RiskAssessment — generated by tools/gen_safety_docs.py from safety/mil-std-882e/catalog.yaml.
// Do not edit by hand: change the catalog and regenerate.
// Status: planning view only; not evidence of completed analysis or verification.

package RiskAssessment {
    private import ScalarValues::*;
    private import SusanooSystem::*;
    private import SusanooSafety::*;
    enum def SeverityCategory {
        enum Catastrophic;
        enum Critical;
        enum Marginal;
        enum Negligible;
    }
    enum def ProbabilityLevel {
        enum Frequent;
        enum Probable;
        enum Occasional;
        enum Remote;
        enum Improbable;
        enum Eliminated;
    }
    enum def RiskLevel {
        enum High;
        enum Serious;
        enum Medium;
        enum Low;
        enum Eliminated;
    }
    attribute def RiskAssessmentRecord {
        attribute severity : SeverityCategory;
        attribute probability : ProbabilityLevel;
        attribute level : RiskLevel;
        attribute rationale : String;
    }
}
```

</details>

## Inputs and outputs

```mermaid
flowchart LR
  E3["03 · Assess and Document Risk"]
  in0["Task 102 · System Safety Program Plan (SSPP)"] -->|"Matrix approval"| E3
  class in0 work
  in1["02 · Identify and Document Hazards"] -->|"Hazards"| E3
  class in1 work
  E3 -->|"Prioritised risks"| out0["04 · Identify and Document Risk Mitigation Measures"]
  class out0 work
  E3 -->|"Risk levels for authority"| out1["07 · Accept Risk and Document"]
  class out1 work
  E3 -->|"Initial risk"| out2["Task 106 · Hazard Tracking System (Hazard Log)"]
  class out2 work
  class E3 current
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
| Matrix approval | [Task 102 · System Safety Program Plan (SSPP)](../01-safety-approach/task-102-system-safety-program-plan/README.md) |
| Hazards | [02 · Identify and Document Hazards](../02-hazard-identification/README.md) |

| Output | Destination |
|---|---|
| Prioritised risks | [04 · Identify and Document Risk Mitigation Measures](../04-mitigation-identification/README.md) |
| Risk levels for authority | [07 · Accept Risk and Document](../07-risk-acceptance/README.md) |
| Initial risk | [Task 106 · Hazard Tracking System (Hazard Log)](../hazard-tracking-system/README.md) |

## Folder contents

| Item | Description | State |
|---|---|---|
| `risk-matrix.yaml` | Machine-readable matrix used by PDaC checks | planned |
| [`RiskAssessment.sysml`](RiskAssessment.sysml) | Generated SysML v2 view | generated |

## Candidate risk assessment matrix

Reproduces the structure of MIL-STD-882E Table III for planning. **Confirm against the
controlled standard and record SSPP approval before use.**

| Probability \ Severity | Catastrophic (1) | Critical (2) | Marginal (3) | Negligible (4) |
|---|---|---|---|---|
| Frequent (A) | High | High | Serious | Medium |
| Probable (B) | High | High | Serious | Medium |
| Occasional (C) | High | Serious | Medium | Low |
| Remote (D) | Serious | Medium | Medium | Low |
| Improbable (E) | Medium | Medium | Medium | Low |
| Eliminated (F) | Eliminated | Eliminated | Eliminated | Eliminated |

<!-- END GENERATED: content below this line is human-authored and preserved -->

## Working content

_No analysis content yet. Add authored material below this heading._
