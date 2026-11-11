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

**Important:** CI cannot certify safety or accept residual risk. The current `pdac/product.yaml` is a **draft manifest**, not a validated executable PDaC implementation.
