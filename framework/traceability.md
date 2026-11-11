# PDaC as Product Development as Code

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
