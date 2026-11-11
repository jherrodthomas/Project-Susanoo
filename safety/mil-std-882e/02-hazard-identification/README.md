# 02 · Identify and Document Hazards

> **Status:** Scaffold v0.1 — structure, diagrams and model views only
>
> Planning artifact. No completed hazard analysis, verified mitigation, risk acceptance, certification or MIL-STD-882E compliance is claimed. Category names follow MIL-STD-882E; confirm definitions against the controlled standard and the approved SSPP before formal use.

| Field | Value |
|---|---|
| MIL-STD-882E element | 2 — Identify and document hazards |
| Lifecycle gate | G0–G5 |
| Applicability | Selected progressively |
| Accountable role | Safety lead |
| Parent folder | [MIL-STD-882E System Safety Work Products](../README.md) |

## Purpose

All hazard analysis tasks (200-series). Analyses are iterative and feed each other; arrows in
the SysML activity are information flow, not a mandatory waterfall. Every hazard found here is
recorded in the hazard tracking system.

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
  class E2 current
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

Dashed frame = **Hazard analysis scope** boundary. Everything outside it is an external entity or another folder's scope.

```mermaid
flowchart LR
  subgraph BND["Boundary: Hazard analysis scope"]
    direction TB
    SUS_M1["SUS-M1: Piloted walker"]
    SUS_A1["SUS-A1: Observation UAV"]
    SUS_GSE["SUS-GSE: Ground support equipment"]
  end
  EXT_PILOT["EXT-PILOT: Pilot / operator"]
  EXT_CREW["EXT-CREW: Ground crew & maintainers"]
  EXT_BYST["EXT-BYST: Bystanders & nearby workers"]
  EXT_AIR["EXT-AIR: Airspace, GNSS & RF environment"]
  EXT_ENV["EXT-ENV: Natural environment & receptors"]
  EXT_PILOT -->|"operator error and workload"| SUS_M1
  SUS_M1 -->|"crush / impact / fall"| EXT_BYST
  SUS_A1 -->|"rotor strike / crash"| EXT_BYST
  EXT_AIR -->|"link loss / GNSS denial"| SUS_A1
  EXT_CREW -->|"maintenance exposure"| SUS_GSE
  SUS_M1 -->|"releases"| EXT_ENV
  class SUS_M1 system
  class SUS_A1 system
  class SUS_GSE system
  class EXT_PILOT external
  class EXT_CREW external
  class EXT_BYST external
  class EXT_AIR external
  class EXT_ENV external
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
| EXT-PILOT: Pilot / operator | SUS-M1: Piloted walker | operator error and workload |
| SUS-M1: Piloted walker | EXT-BYST: Bystanders & nearby workers | crush / impact / fall |
| SUS-A1: Observation UAV | EXT-BYST: Bystanders & nearby workers | rotor strike / crash |
| EXT-AIR: Airspace, GNSS & RF environment | SUS-A1: Observation UAV | link loss / GNSS denial |
| EXT-CREW: Ground crew & maintainers | SUS-GSE: Ground support equipment | maintenance exposure |
| SUS-M1: Piloted walker | EXT-ENV: Natural environment & receptors | releases |

## SysML model

SysML v2 textual view: [`HazardAnalyses.sysml`](HazardAnalyses.sysml) (generated from the catalog; imports [`SusanooSystem`](../00-system-definition/sysml/SusanooSystem.sysml) and [`SusanooSafety`](../00-system-definition/sysml/SusanooSafety.sysml)). The Mermaid rendering below is a reading aid; the `.sysml` file is the model of record.

### Activity (act) — analysis information flow

```mermaid
flowchart TD
  start((start))
  phl["Task 201 PHL"]
  pha["Task 202 PHA"]
  fha["Task 208 FHA"]
  srha["Task 203 SRHA"]
  ssha["Task 204 SSHA"]
  sha["Task 205 SHA"]
  osha["Task 206 O&SHA"]
  start --> phl
  phl --> pha
  pha --> fha
  fha --> srha
  srha --> ssha
  ssha --> sha
  sha --> osha
  osha --> done((done))
  sha -. "interface cause found" .-> ssha
  osha -. "new operating scenario" .-> pha
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
// HazardAnalyses — generated by tools/gen_safety_docs.py from safety/mil-std-882e/catalog.yaml.
// Do not edit by hand: change the catalog and regenerate.
// Status: planning view only; not evidence of completed analysis or verification.

package HazardAnalyses {
    private import ScalarValues::*;
    private import SusanooSystem::*;
    private import SusanooSafety::*;
    action def HazardAnalysisRelationships {
        action phl { doc /* Task 201 PHL */ }
        action pha { doc /* Task 202 PHA */ }
        action fha { doc /* Task 208 FHA */ }
        action srha { doc /* Task 203 SRHA */ }
        action ssha { doc /* Task 204 SSHA */ }
        action sha { doc /* Task 205 SHA */ }
        action osha { doc /* Task 206 O&SHA */ }
        first start;
        then phl;
        first phl then pha;
        first pha then fha;
        first fha then srha;
        first srha then ssha;
        first ssha then sha;
        first sha then osha;
        first osha then done;
        // iteration: sha -> ssha when interface cause found (informal; merge node omitted)
        // iteration: osha -> pha when new operating scenario (informal; merge node omitted)
    }
}
```

</details>

## Inputs and outputs

```mermaid
flowchart LR
  E2["02 · Identify and Document Hazards"]
  in0["00 · System Definition and Analysis Baseline"] -->|"System baseline"| E2
  class in0 work
  in1["01 · Document the System Safety Approach"] -->|"Selected tasks"| E2
  class in1 work
  E2 -->|"Hazard records"| out0["Task 106 · Hazard Tracking System (Hazard Log)"]
  class out0 work
  E2 -->|"Hazards for risk assessment"| out1["03 · Assess and Document Risk"]
  class out1 work
  class E2 current
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
| Selected tasks | [01 · Document the System Safety Approach](../01-safety-approach/README.md) |

| Output | Destination |
|---|---|
| Hazard records | [Task 106 · Hazard Tracking System (Hazard Log)](../hazard-tracking-system/README.md) |
| Hazards for risk assessment | [03 · Assess and Document Risk](../03-risk-assessment/README.md) |

## Folder contents

| Item | Description | State |
|---|---|---|
| [`task-201-preliminary-hazard-list/`](task-201-preliminary-hazard-list/README.md) | Task 201 · Preliminary Hazard List (PHL) | folder |
| [`task-202-preliminary-hazard-analysis/`](task-202-preliminary-hazard-analysis/README.md) | Task 202 · Preliminary Hazard Analysis (PHA) | folder |
| [`task-203-system-requirements-hazard-analysis/`](task-203-system-requirements-hazard-analysis/README.md) | Task 203 · System Requirements Hazard Analysis (SRHA) | folder |
| [`task-204-subsystem-hazard-analysis/`](task-204-subsystem-hazard-analysis/README.md) | Task 204 · Subsystem Hazard Analysis (SSHA) | folder |
| [`task-205-system-hazard-analysis/`](task-205-system-hazard-analysis/README.md) | Task 205 · System Hazard Analysis (SHA) | folder |
| [`task-206-operating-and-support-hazard-analysis/`](task-206-operating-and-support-hazard-analysis/README.md) | Task 206 · Operating and Support Hazard Analysis (O&SHA) | folder |
| [`task-207-health-hazard-analysis/`](task-207-health-hazard-analysis/README.md) | Task 207 · Health Hazard Analysis (HHA) | folder |
| [`task-208-functional-hazard-analysis/`](task-208-functional-hazard-analysis/README.md) | Task 208 · Functional Hazard Analysis (FHA) | folder |
| [`task-209-system-of-systems-hazard-analysis/`](task-209-system-of-systems-hazard-analysis/README.md) | Task 209 · System-of-Systems Hazard Analysis (SoSHA) | folder |
| [`task-210-environmental-hazard-analysis/`](task-210-environmental-hazard-analysis/README.md) | Task 210 · Environmental Hazard Analysis (EHA) | folder |
| [`HazardAnalyses.sysml`](HazardAnalyses.sysml) | Generated SysML v2 view | generated |

<!-- END GENERATED: content below this line is human-authored and preserved -->

## Working content

_No analysis content yet. Add authored material below this heading._
