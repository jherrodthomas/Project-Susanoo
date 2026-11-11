# Susanoo Integrated Standards & Lifecycle Framework v0.1

**Status:** proposed framework, not evidence of certification or compliance.

Project Susanoo is a fictional, unarmed integrated UGV/UAV logistics and observation demonstrator. The governing concept is **Product Development as Code (PDaC)**: typed, versioned product objects, executable validation rules, controlled changes, evidence and releases. A digital thread is an outcome, not the definition of PDaC.

## Framework architecture
1. Program and mission: CONOPS, operating environment, stakeholders, roles, acquisition assumptions.
2. Systems engineering: requirements, architecture, interfaces, validation, verification and configuration baselines.
3. Integrated system safety: MIL-STD-882E program planning, hazard identification, risk assessment, mitigations, tracking and risk acceptance.
4. Air-system assurance: ARP4754B development and ARP4761A FHA/PSSA/SSA, FMEA/FTA/CCA, with DO-178C/DO-254 applicability decisions.
5. Ground-system assurance: MIL-STD-882E with tailored machinery and functional safety methods where justified.
6. Cybersecurity, human factors, quality, manufacturing and sustainment.
7. PDaC product/variant/configuration/release and controlled evidence graph.

## Rules
- Applicability is determined by mission, system boundary, contract and authority; never inferred solely from being a military project.
- Maintain separate MIL-STD-882E risk and ARP4761A failure-condition classifications. Cross-reference rather than equate them.
- An analysis is not complete until inputs, assumptions, results, reviewer and supporting evidence are recorded.
- CI may validate schemas and detect impacts, but may not approve safety risk.
- Simulated approvals must be marked simulated; no claim of military qualification, airworthiness or certification.
- Record standard edition, licensed source, tailoring rationale and clause-level applicability before claiming coverage.
- Do not reproduce copyrighted standards text in this repository.

See [applicability](standards-applicability.md), [lifecycle](lifecycle.md), [processes](process-contracts.md), [traceability](traceability.md) and [execution plan](execution-plan.md).
