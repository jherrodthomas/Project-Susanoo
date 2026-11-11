# Project Susanoo

**SUS-M1 — Human-Piloted Mechanized Platform with Integrated Observation UAV**

Project Susanoo is an open-source, simulation-first product-development demonstrator centered on a **human-piloted mechanized walker** and a **dockable, unarmed observation UAV (SUS-A1)**. The platform explores material handling, logistics, inspection, and field support—not weapon systems.

The design reference is an industrial, open-frame, hydraulically actuated mechanized walker with a protected operator station. Hydraulic actuation is an **initial hypothesis**, subject to an electrohydraulic/electromechanical trade study. The UAV provides aerial observation and can dock with the platform, with deployment and recovery envelopes to be defined and verified.

## Product Development as Code (PDaC)
PDaC is **Product Development as Code**, not a synonym for digital thread: typed product objects, versioned configurations, executable rules, controlled changes, evidence, approvals, and releases. A traceable digital thread is one outcome.

## Start here
- [Concept and CONOPS](concept/CONOPS.md)
- [System architecture](concept/architecture.md)
- [Actuation and UAV integration trade studies](concept/trade-studies.md)
- [Integrated standards framework](framework/README.md)
- [Standards applicability](framework/standards-applicability.md)
- [Lifecycle and review gates](framework/lifecycle.md)
- [Process contracts](framework/process-contracts.md)
- [PDaC traceability](framework/traceability.md)
- [Execution plan](framework/execution-plan.md)
- [Product manifest](pdac/product.yaml)
- [MIL-STD-882E work-product tree](safety/mil-std-882e/README.md) — folders follow the eight-element 882E flow
- [Documentation standard](framework/documentation-standard.md) — required block, boundary and SysML diagrams in every folder README

## Assurance approach
MIL-STD-882E is the integrated system safety method. ISO 12100, ISO 13849 and IEC 61508 methods are evaluated for machinery and control-system risks; MIL-STD-1472 informs operator human factors. SAE ARP4754B and ARP4761A are voluntarily adopted for the UAV development and aircraft safety assessment; DO-178C/DO-254 require separate applicability decisions.

**Status: concept v0.2.** No built prototype, certification, qualification, airworthiness approval or formal government risk acceptance is claimed.
