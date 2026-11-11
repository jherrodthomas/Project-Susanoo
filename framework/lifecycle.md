# Integrated lifecycle and review gates

| Gate | Stage | Required entry | Exit evidence |
|---|---|---|---|
| G0 | Mission and concept | Defined unarmed mission | CONOPS, boundaries, operating assumptions, initial PHL |
| G1 | Requirements baseline | Approved concept | Stakeholder/system requirements, interfaces, traceability |
| G2 | Preliminary safety and architecture | Requirements baseline | PHA, UAV FHA, preliminary architecture, initial safety requirements |
| G3 | Detailed design | Preliminary safety findings | SSHA, PSSA, design, FMEA/FTA/CCA plans, updated risk controls |
| G4 | Integration readiness | Controlled design | Builds, interface verification, simulation procedures |
| G5 | Verification and safety assessment | Testable configuration | Executed tests, fault injection, SHA, O&SHA, SSA, findings |
| G6 | Release review | Evidence and unresolved issues visible | Configuration audit, safety case, risk disposition, approval record |
| G7 | Sustainment and change | Released baseline | Change impact, regression, updated evidence and new release |

These gates are project-defined; they do not purport to reproduce the formal tasks of any standard. Every gate has an accountable owner and an explicit open-items disposition.

## Cross-domain handoffs
CONOPS → system requirements → functional architecture → allocated requirements → design → implementation → verification → safety assessment → risk disposition → release.

MIL-STD-882E governs the integrated system safety program. ARP4761A supports the UAV aircraft safety assessment; ARP4754B supports aircraft development. Their risk taxonomies remain separate. PDaC links their outputs without substituting one process for another.
