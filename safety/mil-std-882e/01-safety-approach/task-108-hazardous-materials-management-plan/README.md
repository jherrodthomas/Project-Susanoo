# Task 108 · Hazardous Materials Management Plan (HMMP)

> **Status:** Scaffold v0.1 — structure, diagrams and model views only
>
> Planning artifact. No completed hazard analysis, verified mitigation, risk acceptance, certification or MIL-STD-882E compliance is claimed. Category names follow MIL-STD-882E; confirm definitions against the controlled standard and the approved SSPP before formal use.

| Field | Value |
|---|---|
| MIL-STD-882E element | 1 — Document the system safety approach |
| Tasks | [Task 108 — Hazardous Materials Management Plan](../../../../docs/wiki/MIL-STD-882E-Task-108.md) |
| Lifecycle gate | G1–G3 |
| Applicability | Selected |
| Accountable role | Environmental / HSE lead |
| Parent folder | [01 · Document the System Safety Approach](../README.md) |

## Purpose

Inventories and manages hazardous materials: engine fuel, hydraulic fluid (if electrohydraulic
actuation is chosen), lithium-ion cells in SUS-M1 and SUS-A1, coolants and lubricants.

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
  T108["Task 108 · Hazardous Materials Management Plan"]
  E1 --- T108
  class E1 safety
  class E2 work
  class E3 work
  class E4 work
  class E5 work
  class E6 work
  class E7 work
  class E8 work
  class HTS work
  class T108 current
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
  class SUS_M1_MAN muted
  class SUS_M1_PIL muted
  class SUS_M1_PWR system
  class SUS_M1_CTL muted
  class SUS_M1_SAF muted
  class SUS_M1_DCK muted
  class SUS_A1_FCS muted
  class SUS_A1_PRP muted
  class SUS_A1_PWR system
  class SUS_A1_NAV muted
  class SUS_A1_PLD muted
  class SUS_GSE_SUP muted
  class SUS_GSE_CHG system
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

Dashed frame = **Hazardous materials** boundary. Everything outside it is an external entity or another folder's scope.

```mermaid
flowchart LR
  subgraph BND["Boundary: Hazardous materials"]
    direction TB
    SUS_M1_PWR["SUS-M1-PWR: Series-hybrid power & isolation"]
    SUS_A1_PWR["SUS-A1-PWR: UAV battery & power mgmt"]
    SUS_M1_WLK["SUS-M1-WLK: Structure, legs, joints & brakes"]
    SUS_GSE_CHG["SUS-GSE-CHG: Charging & fuelling equipment"]
  end
  EXT_CREW["EXT-CREW: Ground crew & maintainers"]
  EXT_ENV["EXT-ENV: Natural environment & receptors"]
  EXT_SITE["EXT-SITE: Site infrastructure & logistics"]
  SUS_GSE_CHG -->|"fuel and charge transfer"| SUS_M1_PWR
  SUS_M1_WLK -->|"hydraulic leak or spill"| EXT_ENV
  SUS_A1_PWR -->|"cell thermal event exposure"| EXT_CREW
  EXT_SITE -->|"storage and disposal"| SUS_GSE_CHG
  class SUS_M1_PWR system
  class SUS_A1_PWR system
  class SUS_M1_WLK system
  class SUS_GSE_CHG system
  class EXT_CREW external
  class EXT_ENV external
  class EXT_SITE external
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
| SUS-GSE-CHG: Charging & fuelling equipment | SUS-M1-PWR: Series-hybrid power & isolation | fuel and charge transfer |
| SUS-M1-WLK: Structure, legs, joints & brakes | EXT-ENV: Natural environment & receptors | hydraulic leak or spill |
| SUS-A1-PWR: UAV battery & power mgmt | EXT-CREW: Ground crew & maintainers | cell thermal event exposure |
| EXT-SITE: Site infrastructure & logistics | SUS-GSE-CHG: Charging & fuelling equipment | storage and disposal |

## SysML model

SysML v2 textual view: [`Task108_HMMP.sysml`](Task108_HMMP.sysml) (generated from the catalog; imports [`SusanooSystem`](../../00-system-definition/sysml/SusanooSystem.sysml) and [`SusanooSafety`](../../00-system-definition/sysml/SusanooSafety.sysml)). The Mermaid rendering below is a reading aid; the `.sysml` file is the model of record.

### Block definition (bdd) — hazardous material inventory

```mermaid
classDiagram
  class HazMatInventory {
    <<part>>
  }
  HazMatInventory o-- "0..*" HazMatEntry : entries
  class HazMatEntry {
    <<item>>
    +String material
    +String location
    +Real quantity
    +String sdsRef
    +String disposal
  }
  class MaterialClass {
    <<enumeration>>
    Fuel
    HydraulicFluid
    LithiumIonCell
    Coolant
    Lubricant
  }
```

<details><summary>SysML v2 source</summary>

```sysml
// Task108_HMMP — generated by tools/gen_safety_docs.py from safety/mil-std-882e/catalog.yaml.
// Do not edit by hand: change the catalog and regenerate.
// Status: planning view only; not evidence of completed analysis or verification.

package Task108_HMMP {
    private import ScalarValues::*;
    private import SusanooSystem::*;
    private import SusanooSafety::*;
    part def HazMatInventory {
        ref item entries : HazMatEntry[0..*];
    }
    item def HazMatEntry {
        attribute material : String;
        attribute location : String;
        attribute quantity : Real;
        attribute sdsRef : String;
        attribute disposal : String;
    }
    enum def MaterialClass {
        enum Fuel;
        enum HydraulicFluid;
        enum LithiumIonCell;
        enum Coolant;
        enum Lubricant;
    }
}
```

</details>

## Inputs and outputs

```mermaid
flowchart LR
  T108["Task 108 · Hazardous Materials Management Plan (HMMP)"]
  in0["00 · System Definition and Analysis Baseline"] -->|"Bill of materials (when available)"| T108
  class in0 work
  T108 -->|"Exposure sources"| out0["Task 207 · Health Hazard Analysis (HHA)"]
  class out0 work
  T108 -->|"Environmental releases"| out1["Task 210 · Environmental Hazard Analysis (EHA)"]
  class out1 work
  class T108 current
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
| Bill of materials (when available) | [00 · System Definition and Analysis Baseline](../../00-system-definition/README.md) |

| Output | Destination |
|---|---|
| Exposure sources | [Task 207 · Health Hazard Analysis (HHA)](../../02-hazard-identification/task-207-health-hazard-analysis/README.md) |
| Environmental releases | [Task 210 · Environmental Hazard Analysis (EHA)](../../02-hazard-identification/task-210-environmental-hazard-analysis/README.md) |

## Folder contents

| Item | Description | State |
|---|---|---|
| `hazmat-inventory.csv` | Material | planned |
| [`Task108_HMMP.sysml`](Task108_HMMP.sysml) | Generated SysML v2 view | generated |

<!-- END GENERATED: content below this line is human-authored and preserved -->

## Working content

_No analysis content yet. Add authored material below this heading._
