# Framework review against MIL-STD-882E, with build ideas

**Status:** Review and proposal, 2026-11. Nothing here claims compliance.
**Source reviewed:** MIL-STD-882E, *System Safety*, 11 May 2012 (base edition, not Change 1). Paragraph and table numbers below refer to that edition.

The question this review answers: can the v0.2 framework *produce and check* the evidence that the standard requires? It then proposes what to build so that it can.

## 1. Two findings that change how the framework should be built

**1.1 Section 4 is the mandatory core; the tasks are optional.** Para 4.1 and 5.2 say that when no tasks are specified, only Sections 3 and 4 apply, and that each task must be called out separately. Appendix A describes the tasks as optional. The current framework is built around the tasks: 25 wiki procedure pages and a task applicability table. The **eight-element process (4.3.1–4.3.8)** and the **software assessment (4.4)** have no structure of their own. The framework should be rebuilt on the eight elements and 4.4. The tasks then become a tailoring layer on top of that core.

**1.2 Edition mismatch.** The repository cites "MIL-STD-882E with Change 1" in 25 files, including every task page. The copy we hold is the 2012 base edition. Before any formal mapping, decide which edition is the baseline and obtain that controlled copy. The standard model should record the edition and date so the choice is explicit (6.2a asks acquisition documents to state title, number and date).

## 2. Gap analysis, clause by clause

| Clause | What the standard requires | Framework today | Gap |
|---|---|---|---|
| 4.3.1a–b | Document the approach; identify prescribed and derived requirements and flow them down | SSPP outline, standards register | No register of prescribed/derived safety requirements and no flow-down links |
| 4.3.1c, 4.3.7 | Formal acceptance by the appropriate authority; **user representative concurrence for all Serious and High acceptances**; acceptance **before** people, equipment or the environment are exposed | `risk_acceptance.authority` field | No user-concurrence field, no authority-by-risk-level mapping, and no rule that acceptance must come before human-occupied tests (gates G4/G5) |
| 4.3.1d, Task 106 | Closed-loop HTS with 19 data elements (106.2 a–s) | `hazard-record.yaml` | Covers about 8 of the 19 elements. See 2.1 |
| 4.3.2 | Systematic identification over hardware, software, human interfaces, environment and the whole life cycle | Procedures only | No hazard records exist |
| 4.3.3, Tables I–III | Severity 1–4, probability A–F, RAC to High/Serious/Medium/Low. Tailored matrices must be derived from Tables I–III and formally approved (4.3.3d). Numerical probability definitions must be documented (4.3.3e) | Fields set to `TBD` | Matrix not stored as data. No tailoring decision. Table I's dollar thresholds ($100K / $1M / $10M) mean little for a demonstrator, so a tailored severity definition is likely needed. No exposure basis for probability (Table A-II) |
| 4.3.3b | **Probability F (Eliminated) cannot be reached by doctrine, training, warnings, caution or PPE** | Not present | Needs a validator rule |
| 4.3.4 a–e | Design order of precedence. **For Catastrophic or Critical hazards, signage, procedures, training and PPE should not be the only mitigation** | Mitigations are an untyped list | No precedence field and no rule |
| 4.3.5 | Present current hazards, risk and status at technical reviews | Gates G0–G7 | No generated hazard status report for gate reviews |
| 4.3.6 | Verify and validate each selected mitigation by analysis, test, demonstration or inspection | `verification_evidence_ids` | No V&V method per mitigation |
| 4.3.8 | Maintain the HTS through the life cycle via configuration control; reassess risk when it increases | Task 304 page, G7 | No link from change requests to the hazards they affect |
| 4.4.1, Table IV | Software control category (SCC 1–5) for each safety-significant software function | Narrative page only | No SCC or safety-significant-function (SSF) records. PX4, the integration manager and walker motion control are not classified |
| 4.4.2, Table V | SwCI from SCC × severity, which sets the level-of-rigor (LOR) tasks. The SSCM is **not** a risk assessment | Not present | No SwCI and no LOR tracking |
| 4.4.3, Table VI | **If LOR tasks are incomplete, the software contribution is recorded at the risk level for that SwCI** (SwCI 1 → High, 2 → Serious, 3 → Medium, 4 → Low) and needs a PM decision | Not present | Needs a validator rule. Incomplete LOR work must raise the recorded risk automatically |
| 6.3 | 17 associated DIDs (for example DI-SAFT-81626 SSPP, DI-SAFT-80102 SAR, DI-SAFT-80101 Hazard Analysis Report) | Task pages say "verify DID" | Store the DIDs in the model and link each task output to one |
| App. A, Table A-I | Task applicability by acquisition phase (G / S / GC / N/A) | Prose table | Not linked to project gates. See 3.2 |

### 2.1 Hazard Tracking System coverage (Task 106.2)

| 106.2 element | Template field | Status |
|---|---|---|
| a Hazard | `hazardous_condition` | Present |
| b System, c Subsystem | `configuration_id`, `subsystem_ids` | Partial: no system ID |
| d Applicability (hardware/software version) | `configuration_id` | Partial: needs version-specific applicability |
| e Requirements references | `safety_requirement_ids` | Present |
| f System mode | — | **Missing** |
| g Causal factor (hardware, software, human, environment) | `causes[]` | Partial: no causal-factor type |
| h Effects | `consequences` | Present |
| i Mishap | — | **Missing** |
| j Initial RAC | `initial_risk` | Present |
| k Target RAC | — | **Missing** |
| l Event RAC(s) | `residual_risk` (single value) | Partial: the standard expects a list of event RACs |
| m Mitigations, identified **and** selected, traced to versions | `mitigations[]` | Partial |
| n Hazard status | `status: draft` | Partial: no status lifecycle |
| o V&V method | — | **Missing** |
| p Action person and organizational element | `owner` | Partial |
| q Acceptance record: authority title and org, user concurrence, date, location of the signed record | `risk_acceptance` | Partial |
| r Hazard management log | — | Can come from git history if records are only changed through PRs |
| s HAZMAT data elements | — | Missing (Task 108) |

`pha-table.csv` has a different, smaller field set. It should be generated from the YAML records instead of being a second template.

### 2.2 Other defects
- **Broken step numbering on 23 of the 25 task pages.** Step 2 was split on semicolons, so the pages read "2, 3, 3, 3". Tasks 205 and 206 skip from 2 to 4.
- **The framework is written twice.** `framework/*.md` and `docs/wiki/*.md` say the same things separately and will drift apart. One should be generated from the other.
- **Copyright rule.** "No copyrighted standards text" is correct for SAE, ISO, IEC and RTCA documents. MIL-STD-882E is a DoD standard practice, so Tables I–VI and A-I can probably be encoded exactly. Confirm the distribution statement on the controlled copy first.

## 3. Proposal: encode the standard as data

The framework currently *describes* how to follow the standard. The proposal is to encode the standard as data, check project records against it, and compute conformance status rather than assert it.

```
standards/mil-std-882e/model.yaml   ← the standard as data: elements, tables, tasks, DIDs
standards/tailoring/882e.yaml       ← project decisions: tailored matrix, authorities, task selection
pdac/schemas/*.json                 ← typed objects: Hazard, Mishap, Mitigation, SSF, Acceptance, …
safety/hazards/HAZ-*.yaml           ← the Hazard Tracking System, one file per hazard
safety/software/SSF-*.yaml          ← safety-significant software functions
tools/pdac/validate.py              ← schema, link and 882E rules
tools/pdac/report.py                ← generated HTS log, conformance matrix, gate readiness, SAR draft
```

### 3.1 Standard model (`model.yaml`)
- `edition`: number, date, change level
- `elements`: 4.3.1–4.3.8 and 4.4, each with its shall-statements reduced to checkable obligations (for example `E7.user_concurrence_serious_high`)
- `severity` (Table I), `probability` (Table II plus the A-II quantitative bands), `rac_matrix` (Table III)
- `mitigation_precedence`: 4.3.4 a–e
- `scc` (Table IV), `sscm` (Table V), `lor_tasks` by SwCI, `incomplete_lor_risk` (Table VI)
- `tasks`: ID, title, type (MGT or ENG), Table A-I applicability by phase, and the DIDs from 6.3
- `hts_elements`: 106.2 a–s, each mapped to a schema path. This mapping produces the coverage table in 2.1 automatically

### 3.2 Tailoring record (`tailoring/882e.yaml`)
- **Phase mapping:** MSA → G0–G1, TD → G2, EMD → G3–G5, P&D → G6, O&S → G7. The validator can then compare each task decision with Table A-I and require a rationale wherever the project departs from a "G" (generally applicable).
- **Tailored severity table** for a demonstrator: keep the injury and environmental criteria, rescale the dollar values. Record it with derivation and approval as 4.3.3d requires. The approval is marked simulated.
- **Probability bands** with an exposure basis (operating hours, docking cycles, sorties), as required by 4.3.3e and A.3.
- **Acceptance authority by risk level.** DoDI 5000.02 assigns these for real programs. For this project, use simulated roles: High → program executive role, Serious → program lead, Medium/Low → safety lead. Each role also names its user representative.
- **Task selection** with rationale, gate and re-evaluation trigger. This replaces the prose table.

### 3.3 Validator rules taken from the standard
1. RAC = `matrix[severity][probability]` for every initial, target and event assessment (4.3.3c).
2. Probability F is allowed only if a mitigation of precedence a ("eliminate through design") is selected and verified (4.3.3b, 4.3.4a).
3. Severity 1 or 2 with only precedence-e mitigations (signage, procedures, training, PPE) fails, unless a waiver rationale is recorded (4.3.4e).
4. Each selected mitigation has a V&V method and evidence before the hazard can be closed (4.3.6).
5. Acceptance by an authority at or above the level the risk requires. High and Serious also require user-representative concurrence (4.3.7).
6. **Exposure gate:** a test event with people aboard or nearby needs current acceptance records for every open hazard that applies to that configuration and mode (4.3.7). This turns the lifecycle rule "simulation is not permission for human-occupied operation" into an executable check.
7. Each SSF has an SCC. Its SwCI is computed from Table V. If its required LOR tasks are incomplete, the linked hazard's software contribution is raised to the Table VI risk level (4.4.1–4.4.3).
8. Records with probability or numeric severity must cite the tailored definitions (4.3.3e).
9. Every 106.2 element that has been selected is filled in, or marked N/A with a reason (Task 106).
10. A change request touching a mitigation, SSF or configuration reopens the linked hazards for reassessment. A risk increase needs a new acceptance (4.3.8, Task 304).
11. Any acceptance by a simulated authority keeps the release profile at `simulation-and-assurance-demonstrator` (project rule).

### 3.4 Generated outputs (CI on every PR)
- **Conformance matrix:** each element, shall-statement and selected task × evidence status (`not-started`, `in-work`, `evidenced`, `reviewed`). It never shows "compliant".
- **HTS log and risk view:** initial, target and event RAC on the Table III grid, published to the wiki (supports 4.3.5 at reviews).
- **Gate readiness:** for G0–G7, what is required, what exists and what blocks the gate.
- **Report skeletons** in DID structure: Task 107 progress report, Task 301 SAR (DI-SAFT-80102), Task 302 HMAR.

## 4. Prove it on real content
Seed the HTS with hazards taken from material the repo already has:

| Candidate hazard (mishap) | Mode | Source | Requirement | Software function to classify |
|---|---|---|---|---|
| Unintended leg motion during ingress/egress (crush) | Ingress | Pilot ↔ controls | SYS-001 | Motion-enable logic |
| Protective stop does not achieve a safe state (fall, impact) | All | Safety architecture | SYS-002 | Stop supervisor |
| Rotor start while retained or with a person near the dock (laceration) | Docked, maintenance | IF-PX4-009 | SYS-003 | PX4 arming plus dock interlock |
| Stale feedback causes runaway or fall (crush, tip-over) | Walking | Controller ↔ actuators | SYS-004 | Feedback monitor |
| False "retained" state, so UAV is released under motion (strike) | Transit | IF-PX4-003 | SYS-005 | Dock state fusion |
| Launch or recovery outside the envelope (strike on pilot or walker) | Launch, recovery | IF-PX4-004/005 | SYS-006 | Integration manager launch permit |
| Residual hydraulic pressure during service (crush, injection injury) | Maintenance | Maintenance ↔ walker | (new) | — |
| Tip-over with pilot aboard | Walking, manipulation | Walker ↔ ground | (new) | Balance controller |

The launch-permit function (row 6) is a useful early SSCM test case. If it can command the aircraft with no independent interlock, it is SCC 1 or 2, so with a Catastrophic severity it is **SwCI 1**. SwCI 1 requires analysis of code and in-depth safety testing, including the PX4 and adapter code. This result should feed the PX4 architecture trade now, while the design is still open.

## 5. Order of work
1. **Housekeeping:** decide the edition and correct the citations, fix the step numbering, choose one source for framework vs wiki, add markdown and link checks to CI.
2. **`model.yaml` and `tailoring/882e.yaml`** (sections 3.1–3.2). Review these with the safety lead before writing code.
3. **Schemas and validator** (3.3), plus a CI job that fails on rule violations.
4. **Seed the HTS and SSF records** (section 4). Turn `SYS-001..006` into typed Requirement objects.
5. **Generated reports** (3.4) published to the wiki.
6. **Second standard on the same pattern:** ARP4761A (FHA, PSSA, SSA, DAL) for SUS-A1, with a separate risk namespace, then ISO 12100 and ISO 13849 (PLr). Tests whether the engine generalizes.
7. **Later:** a SysML v2 textual model as the source for Function, Interface and Component; change-impact diffs on PRs; a hash-pinned evidence manifest per release.

## 6. Decisions needed
- Baseline edition: the 2012 base edition we hold, or Change 1.
- Tailored severity definitions and probability bands, including the exposure basis.
- The acceptance-authority and user-representative mapping, and who holds each simulated role.
- Tooling (Python + JSON Schema is proposed) and whether CI should block merges.
