# PDaC as Product Development as Code

**ID:** SUS-FW-005 · **Revision:** 0.3-draft · **Status:** Draft, not reviewed

PDaC is a machine-readable product lifecycle model with typed objects, schemas, executable validation, versioned configurations, workflows and releases. **A digital thread is an emergent capability, not the definition.**

## Canonical identity
Product → Variant → Configuration → Release. A release references immutable baselines and evidence manifests.

## Object types
Requirement, Function, Interface, Component, Hazard, FailureCondition, SafetyControl, Analysis, TestCase, TestResult, Finding, ChangeRequest, ComplianceClaim, Approval, Release.

Required common fields: id, type, revision, status, owner, source, timestamps, configuration applicability and provenance.

## Typed links
- requirement **allocated_to** component
- requirement **verified_by** test case
- hazard **mitigated_by** safety control
- failure condition **analyzed_by** aircraft safety analysis
- control **implemented_by** design element
- test result **evidences** verification claim
- change **impacts** controlled object
- release **contains** immutable baseline
- compliance claim **supported_by** evidence

## Validation rules
1. All IDs unique and all references resolvable.
2. Released requirements require a verification disposition.
3. Open high-risk findings cannot be silently omitted from release.
4. Every approval names an authority and identifies whether real or simulated.
5. A change affecting safety controls flags linked analyses and verification as requiring review.
6. Every evidence reference includes provenance, version and integrity hash where available.
7. Risk scales for MIL-STD-882E and ARP4761A are separate schema namespaces.

CI checks syntax, links and completeness; human reviewers decide technical adequacy and risk acceptance.

## Implementation status
Implemented in [`pdac/`](../pdac/README.md) and [`tools/pdac/`](../tools/pdac/): object types Product, Variant, Configuration, Release, Document, Actor, Mode, Scenario, Component, Interface, TradeStudy, Requirement, Hazard, and (schema only) FailureCondition and Approval.

| Rule | Check | State |
|---|---|---|
| 1 IDs unique, references resolvable | P2, P3 | Implemented |
| 2 Released requirements need a verification disposition | P6 | Implemented for `baselined` requirements (method and approval) |
| 3 Open high-risk findings not silently omitted from release | — | Planned, with Finding records |
| 4 Approvals name an authority, real or simulated | P1 (schema), P6 | Implemented |
| 5 Safety-control change flags linked analyses and verification | — | Planned, with ChangeRequest records |
| 6 Evidence references carry provenance, version, hash | — | Planned, with Evidence records |
| 7 MIL-STD-882E and ARP4761A scales in separate namespaces | P1 (schema), P5 | Implemented |
