# Task 209 · System-of-Systems Hazard Analysis (SoSHA)

> **Status:** Scaffold v0.1 — structure, diagrams and model views only
>
> Planning artifact. No completed hazard analysis, verified mitigation, risk acceptance, certification or MIL-STD-882E compliance is claimed. Category names follow MIL-STD-882E; confirm definitions against the controlled standard and the approved SSPP before formal use.

| Field | Value |
|---|---|
| MIL-STD-882E element | 2 — Identify and document hazards |
| Tasks | [Task 209 — System-of-Systems Hazard Analysis](../../../../docs/wiki/MIL-STD-882E-Task-209.md) |
| Lifecycle gate | G2–G5 |
| Applicability | Conditional — external systems not yet baselined |
| Accountable role | Safety lead |
| Parent folder | [02 · Identify and Document Hazards](../README.md) |

## Purpose

Analyses hazards from SUS-I1 interacting with external systems: GNSS, RF spectrum, airspace
users, site power and logistics, other vehicles and remote observers.

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
  T209["Task 209 · System-of-Systems Hazard Analysis"]
  E2 --- T209
  class E1 work
  class E2 safety
  class E3 work
  class E4 work
  class E5 work
  class E6 work
  class E7 work
  class E8 work
  class HTS work
  class T209 current
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

Dashed frame = **SUS-I1 as constituent system** boundary. Everything outside it is an external entity or another folder's scope.

```mermaid
flowchart LR
  subgraph BND["Boundary: SUS-I1 as constituent system"]
    direction TB
    SUS_I1["SUS-I1: Integrated mech + UAV system"]
  end
  EXT_AIR["EXT-AIR: Airspace, GNSS & RF environment"]
  EXT_SITE["EXT-SITE: Site infrastructure & logistics"]
  Other_site_vehicles["Other site vehicles"]
  Remote_video_consumers["Remote video consumers"]
  EXT_AIR -->|"GNSS, RF spectrum, airspace"| SUS_I1
  EXT_SITE -->|"power, fuel, transport"| SUS_I1
  SUS_I1 -->|"shared workspace"| Other_site_vehicles
  SUS_I1 -->|"observation feed"| Remote_video_consumers
  class SUS_I1 system
  class EXT_AIR external
  class EXT_SITE external
  class Other_site_vehicles external
  class Remote_video_consumers external
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
| EXT-AIR: Airspace, GNSS & RF environment | SUS-I1: Integrated mech + UAV system | GNSS, RF spectrum, airspace |
| EXT-SITE: Site infrastructure & logistics | SUS-I1: Integrated mech + UAV system | power, fuel, transport |
| SUS-I1: Integrated mech + UAV system | Other site vehicles | shared workspace |
| SUS-I1: Integrated mech + UAV system | Remote video consumers | observation feed |

## SysML model

SysML v2 textual view: [`Task209_SoSHA.sysml`](Task209_SoSHA.sysml) (generated from the catalog; imports [`SusanooSystem`](../../00-system-definition/sysml/SusanooSystem.sysml) and [`SusanooSafety`](../../00-system-definition/sysml/SusanooSafety.sysml)). The Mermaid rendering below is a reading aid; the `.sysml` file is the model of record.

### Internal block / context (ibd) — system-of-systems context

```mermaid
flowchart LR
  subgraph CTX["SoSContext : context"]
    sus["sus : IntegratedSystem"]
    gnss["gnss : GnssConstellation"]
    airspace["airspace : AirspaceUsers"]
    site["site : SiteInfrastructureSystem"]
    vehicles["vehicles : SiteVehicles"]
  end
  gnss <-->|"navigation signals"| sus
  airspace <-->|"deconfliction"| sus
  site <-->|"power, fuel, comms"| sus
  vehicles <-->|"shared workspace"| sus
  class sus system
  class gnss external
  class airspace external
  class site external
  class vehicles external
  style CTX fill:none,stroke:#55758f,stroke-dasharray: 6 4
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
// Task209_SoSHA — generated by tools/gen_safety_docs.py from safety/mil-std-882e/catalog.yaml.
// Do not edit by hand: change the catalog and regenerate.
// Status: planning view only; not evidence of completed analysis or verification.

package Task209_SoSHA {
    private import ScalarValues::*;
    private import SusanooSystem::*;
    private import SusanooSafety::*;
    part def GnssConstellation;
    part def AirspaceUsers;
    part def SiteInfrastructureSystem;
    part def SiteVehicles;
    part def SoSContext {
        part sus : IntegratedSystem;
        part gnss : GnssConstellation;
        part airspace : AirspaceUsers;
        part site : SiteInfrastructureSystem;
        part vehicles : SiteVehicles;
        connection c1 connect gnss to sus { doc /* navigation signals */ }
        connection c2 connect airspace to sus { doc /* deconfliction */ }
        connection c3 connect site to sus { doc /* power, fuel, comms */ }
        connection c4 connect vehicles to sus { doc /* shared workspace */ }
    }
}
```

</details>

## Inputs and outputs

```mermaid
flowchart LR
  T209["Task 209 · System-of-Systems Hazard Analysis (SoSHA)"]
  in0["Task 205 · System Hazard Analysis (SHA)"] -->|"System hazards"| T209
  class in0 work
  in1["01 · Document the System Safety Approach"] -->|"Applicability decision"| T209
  class in1 work
  T209 -->|"SoS hazards"| out0["Task 106 · Hazard Tracking System (Hazard Log)"]
  class out0 work
  class T209 current
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
| System hazards | [Task 205 · System Hazard Analysis (SHA)](../task-205-system-hazard-analysis/README.md) |
| Applicability decision | [01 · Document the System Safety Approach](../../01-safety-approach/README.md) |

| Output | Destination |
|---|---|
| SoS hazards | [Task 106 · Hazard Tracking System (Hazard Log)](../../hazard-tracking-system/README.md) |

## Folder contents

| Item | Description | State |
|---|---|---|
| `sosha.csv` | External interaction worksheet | planned |
| [`Task209_SoSHA.sysml`](Task209_SoSHA.sysml) | Generated SysML v2 view | generated |

<!-- END GENERATED: content below this line is human-authored and preserved -->

## Working content

_No analysis content yet. Add authored material below this heading._
