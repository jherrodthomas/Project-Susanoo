# Software Contribution to System Risk (Section 4.4)

> **Status:** Scaffold v0.1 — structure, diagrams and model views only
>
> Planning artifact. No completed hazard analysis, verified mitigation, risk acceptance, certification or MIL-STD-882E compliance is claimed. Category names follow MIL-STD-882E; confirm definitions against the controlled standard and the approved SSPP before formal use.

| Field | Value |
|---|---|
| Lifecycle gate | G1–G5 |
| Applicability | Selected |
| Accountable role | Software safety lead |
| Procedure | [`docs/wiki/MIL-STD-882E-Software-Safety.md`](../../../docs/wiki/MIL-STD-882E-Software-Safety.md) |
| Parent folder | [MIL-STD-882E System Safety Work Products](../README.md) |

## Purpose

Software control category, software safety criticality and level-of-rigor assignments for
walker motion control, protective stop, pilot HMI, dock interlocks and PX4. MIL-STD-882E
criticality is kept distinct from any DO-178C assurance level.

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
  X["Software Contribution to System Risk (Section 4.4)"]
  X -.- E3 & E4 & E5 & E6
  class E1 work
  class E2 work
  class E3 work
  class E4 work
  class E5 work
  class E6 work
  class E7 work
  class E8 work
  class HTS safety
  class X current
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
  class SUS_M1_PIL system
  class SUS_M1_PWR muted
  class SUS_M1_CTL system
  class SUS_M1_SAF safety
  class SUS_M1_DCK interface
  class SUS_A1_FCS system
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

Dashed frame = **Safety-significant software** boundary. Everything outside it is an external entity or another folder's scope.

```mermaid
flowchart LR
  subgraph BND["Boundary: Safety-significant software"]
    direction TB
    SUS_M1_CTL["SUS-M1-CTL: Motion & balance control SW"]
    SUS_M1_SAF["SUS-M1-SAF: Safety monitor & protective stop"]
    SUS_M1_DCK["SUS-M1-DCK: UAV dock - retention, power, data"]
    SUS_A1_FCS["SUS-A1-FCS: Flight control - PX4 candidate"]
  end
  PX4_upstream_project["PX4 upstream project"]
  Toolchain_and_dependencies["Toolchain and dependencies"]
  EXT_PILOT["EXT-PILOT: Pilot / operator"]
  PX4_upstream_project -->|"pinned version and parameters"| SUS_A1_FCS
  Toolchain_and_dependencies -->|"build inputs"| SUS_M1_CTL
  EXT_PILOT -->|"commands via HMI"| SUS_M1_CTL
  SUS_M1_SAF -->|"independent inhibit"| SUS_M1_CTL
  class SUS_M1_CTL system
  class SUS_M1_SAF safety
  class SUS_M1_DCK interface
  class SUS_A1_FCS system
  class PX4_upstream_project external
  class Toolchain_and_dependencies external
  class EXT_PILOT external
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
| PX4 upstream project | SUS-A1-FCS: Flight control - PX4 candidate | pinned version and parameters |
| Toolchain and dependencies | SUS-M1-CTL: Motion & balance control SW | build inputs |
| EXT-PILOT: Pilot / operator | SUS-M1-CTL: Motion & balance control SW | commands via HMI |
| SUS-M1-SAF: Safety monitor & protective stop | SUS-M1-CTL: Motion & balance control SW | independent inhibit |

## SysML model

SysML v2 textual view: [`SoftwareSafety.sysml`](SoftwareSafety.sysml) (generated from the catalog; imports [`SusanooSystem`](../00-system-definition/sysml/SusanooSystem.sysml) and [`SusanooSafety`](../00-system-definition/sysml/SusanooSafety.sysml)). The Mermaid rendering below is a reading aid; the `.sysml` file is the model of record.

### Block definition (bdd) — software criticality assignment

```mermaid
classDiagram
  class SoftwareFunctionAssessment {
    <<item>>
    +String functionId
    +SoftwareControlCategory controlCategory
    +SeverityCategory severity
    +String levelOfRigor
    +Boolean independentMitigation
  }
  class SoftwareControlCategory {
    <<enumeration>>
    Autonomous
    SemiAutonomous
    RedundantFaultTolerant
    Influential
    NoSafetyImpact
  }
```

<details><summary>SysML v2 source</summary>

```sysml
// SoftwareSafety — generated by tools/gen_safety_docs.py from safety/mil-std-882e/catalog.yaml.
// Do not edit by hand: change the catalog and regenerate.
// Status: planning view only; not evidence of completed analysis or verification.

package SoftwareSafety {
    private import ScalarValues::*;
    private import SusanooSystem::*;
    private import SusanooSafety::*;
    item def SoftwareFunctionAssessment {
        attribute functionId : String;
        attribute controlCategory : SoftwareControlCategory;
        attribute severity : SeverityCategory;
        attribute levelOfRigor : String;
        attribute independentMitigation : Boolean;
    }
    enum def SoftwareControlCategory {
        enum Autonomous;
        enum SemiAutonomous;
        enum RedundantFaultTolerant;
        enum Influential;
        enum NoSafetyImpact;
    }
}
```

</details>

## Inputs and outputs

```mermaid
flowchart LR
  SWS["Software Contribution to System Risk (Section 4.4)"]
  in0["Task 208 · Functional Hazard Analysis (FHA)"] -->|"Safety-significant functions"| SWS
  class in0 work
  in1["Task 204 · Subsystem Hazard Analysis (SSHA)"] -->|"Software causal factors"| SWS
  class in1 work
  in2["integrations/px4/README.md"] -->|"PX4 integration plan"| SWS
  class in2 external
  SWS -->|"Software safety requirements"| out0["Safety Requirements Register"]
  class out0 work
  SWS -->|"Level-of-rigor verification tasks"| out1["Task 401 · Safety Verification"]
  class out1 work
  class SWS current
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
| Safety-significant functions | [Task 208 · Functional Hazard Analysis (FHA)](../02-hazard-identification/task-208-functional-hazard-analysis/README.md) |
| Software causal factors | [Task 204 · Subsystem Hazard Analysis (SSHA)](../02-hazard-identification/task-204-subsystem-hazard-analysis/README.md) |
| PX4 integration plan | [`integrations/px4/README.md`](../../../integrations/px4/README.md) |

| Output | Destination |
|---|---|
| Software safety requirements | [Safety Requirements Register](../05-risk-reduction/safety-requirements/README.md) |
| Level-of-rigor verification tasks | [Task 401 · Safety Verification](../06-verification/task-401-safety-verification/README.md) |

## Folder contents

| Item | Description | State |
|---|---|---|
| `swci-assessment.csv` | Function x control category x severity x LOR | planned |
| [`SoftwareSafety.sysml`](SoftwareSafety.sysml) | Generated SysML v2 view | generated |

<!-- END GENERATED: content below this line is human-authored and preserved -->

## Working content

_No analysis content yet. Add authored material below this heading._
