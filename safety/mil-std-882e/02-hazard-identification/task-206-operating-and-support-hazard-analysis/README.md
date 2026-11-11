# Task 206 · Operating and Support Hazard Analysis (O&SHA)

> **Status:** Scaffold v0.1 — structure, diagrams and model views only
>
> Planning artifact. No completed hazard analysis, verified mitigation, risk acceptance, certification or MIL-STD-882E compliance is claimed. Category names follow MIL-STD-882E; confirm definitions against the controlled standard and the approved SSPP before formal use.

| Field | Value |
|---|---|
| MIL-STD-882E element | 2 — Identify and document hazards |
| Tasks | [Task 206 — Operating and Support Hazard Analysis](../../../../docs/wiki/MIL-STD-882E-Task-206.md) |
| Lifecycle gate | G3–G5 |
| Applicability | Selected |
| Accountable role | Safety lead with human factors lead |
| Parent folder | [02 · Identify and Document Hazards](../README.md) |

## Purpose

Analyses hazards in operation, maintenance, ingress/egress, transport, testing, UAV launch and
recovery, and procedures. Human-occupied testing requires its own authorization.

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
  T206["Task 206 · Operating and Support Hazard Analysis"]
  E2 --- T206
  class E1 work
  class E2 safety
  class E3 work
  class E4 work
  class E5 work
  class E6 work
  class E7 work
  class E8 work
  class HTS work
  class T206 current
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
  class SUS_M1_WLK muted
  class SUS_M1_MAN muted
  class SUS_M1_PIL system
  class SUS_M1_PWR muted
  class SUS_M1_CTL muted
  class SUS_M1_SAF muted
  class SUS_M1_DCK interface
  class SUS_A1_FCS muted
  class SUS_A1_PRP muted
  class SUS_A1_PWR muted
  class SUS_A1_NAV muted
  class SUS_A1_PLD muted
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

Dashed frame = **Operating and support tasks** boundary. Everything outside it is an external entity or another folder's scope.

```mermaid
flowchart LR
  subgraph BND["Boundary: Operating and support tasks"]
    direction TB
    Operating_modes["Operating modes"]
    Maintenance_procedures["Maintenance procedures"]
    SUS_GSE["SUS-GSE: Ground support equipment"]
  end
  EXT_PILOT["EXT-PILOT: Pilot / operator"]
  EXT_CREW["EXT-CREW: Ground crew & maintainers"]
  EXT_BYST["EXT-BYST: Bystanders & nearby workers"]
  EXT_PILOT -->|"mode selection, ingress / egress"| Operating_modes
  EXT_CREW -->|"lockout / support / service"| Maintenance_procedures
  Operating_modes -->|"exclusion zones"| EXT_BYST
  SUS_GSE -->|"supports, chargers"| Maintenance_procedures
  class Operating_modes work
  class Maintenance_procedures work
  class SUS_GSE system
  class EXT_PILOT external
  class EXT_CREW external
  class EXT_BYST external
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
| EXT-PILOT: Pilot / operator | Operating modes | mode selection, ingress / egress |
| EXT-CREW: Ground crew & maintainers | Maintenance procedures | lockout / support / service |
| Operating modes | EXT-BYST: Bystanders & nearby workers | exclusion zones |
| SUS-GSE: Ground support equipment | Maintenance procedures | supports, chargers |

## SysML model

SysML v2 textual view: [`Task206_OSHA.sysml`](Task206_OSHA.sysml) (generated from the catalog; imports [`SusanooSystem`](../../00-system-definition/sysml/SusanooSystem.sysml) and [`SusanooSafety`](../../00-system-definition/sysml/SusanooSafety.sysml)). The Mermaid rendering below is a reading aid; the `.sysml` file is the model of record.

### State machine (stm) — operating modes analysed

```mermaid
stateDiagram-v2
  [*] --> Shutdown
  Shutdown : Shutdown - energy isolated
  MaintenanceLocked : MaintenanceLocked - supported and locked out
  Standby : Standby - pilot seated
  Walk : Walk
  Manipulate : Manipulate
  UAVLaunchRecovery : UAVLaunchRecovery - walker stationary
  ProtectiveStop : ProtectiveStop - safe state
  Shutdown --> MaintenanceLocked : lockout applied
  MaintenanceLocked --> Shutdown : lockout removed
  Shutdown --> Standby : readiness confirmed
  Standby --> Walk : pilot enable
  Walk --> Standby : pilot hold
  Standby --> Manipulate : arm enable
  Manipulate --> Standby : arm disable
  Standby --> UAVLaunchRecovery : envelope valid
  UAVLaunchRecovery --> Standby : UAV docked or clear
  Walk --> ProtectiveStop : stop request or fault
  Manipulate --> ProtectiveStop : stop request or fault
  UAVLaunchRecovery --> ProtectiveStop : abort
  ProtectiveStop --> Standby : reset after review
  Standby --> Shutdown : power down
```

<details><summary>SysML v2 source</summary>

```sysml
// Task206_OSHA — generated by tools/gen_safety_docs.py from safety/mil-std-882e/catalog.yaml.
// Do not edit by hand: change the catalog and regenerate.
// Status: planning view only; not evidence of completed analysis or verification.

package Task206_OSHA {
    private import ScalarValues::*;
    private import SusanooSystem::*;
    private import SusanooSafety::*;
    attribute def UavDockedOrClear;
    attribute def Abort;
    attribute def ArmDisable;
    attribute def ArmEnable;
    attribute def EnvelopeValid;
    attribute def LockoutApplied;
    attribute def LockoutRemoved;
    attribute def PilotEnable;
    attribute def PilotHold;
    attribute def PowerDown;
    attribute def ReadinessConfirmed;
    attribute def ResetAfterReview;
    attribute def StopRequestOrFault;
    state def OperatingModes {
        entry; then Shutdown;
        state Shutdown { doc /* energy isolated */ }
        state MaintenanceLocked { doc /* supported and locked out */ }
        state Standby { doc /* pilot seated */ }
        state Walk;
        state Manipulate;
        state UAVLaunchRecovery { doc /* walker stationary */ }
        state ProtectiveStop { doc /* safe state */ }
        transition t1 first Shutdown accept LockoutApplied then MaintenanceLocked;
        transition t2 first MaintenanceLocked accept LockoutRemoved then Shutdown;
        transition t3 first Shutdown accept ReadinessConfirmed then Standby;
        transition t4 first Standby accept PilotEnable then Walk;
        transition t5 first Walk accept PilotHold then Standby;
        transition t6 first Standby accept ArmEnable then Manipulate;
        transition t7 first Manipulate accept ArmDisable then Standby;
        transition t8 first Standby accept EnvelopeValid then UAVLaunchRecovery;
        transition t9 first UAVLaunchRecovery accept UavDockedOrClear then Standby;
        transition t10 first Walk accept StopRequestOrFault then ProtectiveStop;
        transition t11 first Manipulate accept StopRequestOrFault then ProtectiveStop;
        transition t12 first UAVLaunchRecovery accept Abort then ProtectiveStop;
        transition t13 first ProtectiveStop accept ResetAfterReview then Standby;
        transition t14 first Standby accept PowerDown then Shutdown;
    }
}
```

</details>

## Inputs and outputs

```mermaid
flowchart LR
  T206["Task 206 · Operating and Support Hazard Analysis (O&SHA)"]
  in0["concept/CONOPS.md"] -->|"Operating scenarios"| T206
  class in0 external
  in1["Task 202 · Preliminary Hazard Analysis (PHA)"] -->|"PHA"| T206
  class in1 work
  T206 -->|"Procedural and design requirements"| out0["Safety Requirements Register"]
  class out0 work
  T206 -->|"Test hazard controls"| out1["Task 303 · Test and Evaluation Participation"]
  class out1 work
  T206 -->|"Operating hazards"| out2["Task 106 · Hazard Tracking System (Hazard Log)"]
  class out2 work
  class T206 current
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
| Operating scenarios | [`concept/CONOPS.md`](../../../../concept/CONOPS.md) |
| PHA | [Task 202 · Preliminary Hazard Analysis (PHA)](../task-202-preliminary-hazard-analysis/README.md) |

| Output | Destination |
|---|---|
| Procedural and design requirements | [Safety Requirements Register](../../05-risk-reduction/safety-requirements/README.md) |
| Test hazard controls | [Task 303 · Test and Evaluation Participation](../../06-verification/task-303-test-and-evaluation-participation/README.md) |
| Operating hazards | [Task 106 · Hazard Tracking System (Hazard Log)](../../hazard-tracking-system/README.md) |

## Folder contents

| Item | Description | State |
|---|---|---|
| `osha.csv` | Task-step hazard worksheet | planned |
| [`Task206_OSHA.sysml`](Task206_OSHA.sysml) | Generated SysML v2 view | generated |

<!-- END GENERATED: content below this line is human-authored and preserved -->

## Working content

_No analysis content yet. Add authored material below this heading._
