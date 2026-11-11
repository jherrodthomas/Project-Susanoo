# PDaC — Configuration, Change and Release

**Product Development as Code** expresses product objects, lifecycle relationships, rules, evidence and approvals in version-controlled, machine-readable form.

## Product identity
Product → Variant → Configuration → Release. SUS-M1 walker, SUS-A1 UAV and SUS-I1 integrated demonstrator have distinct applicability.

## Workflow
1. Create typed objects with stable IDs, provenance, owner, status and configuration applicability.
2. Link needs → requirements → architecture → hazards/controls → tests → evidence.
3. Propose a change request with rationale, affected baseline and impact review.
4. Validate schemas, references, completeness and evidence integrity in CI where available.
5. Obtain accountable human technical/safety/configuration reviews.
6. Generate an immutable release manifest with versions, unresolved findings and explicit approvals.
7. Reopen impacted analyses and tests after relevant changes.

**Implementation:** records, schema and checks P1–P9 are described in [`pdac/README.md`](../../pdac/README.md); CI runs them on every pull request.

**Important:** CI cannot certify safety or accept residual risk. A passing check means the records are consistent, not that anything is reviewed or approved.
