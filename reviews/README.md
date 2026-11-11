# Review records

One `REV-YYYY-NNN.yaml` per review (schema [`pdac/schemas/review.schema.json`](../pdac/schemas/review.schema.json)). A review record is the **only** way anything in Susanoo is accepted (rule R13):

| To do this | You need an accepting review that lists the item in `scope` and has a named human reviewer |
|---|---|
| Accept a hazard's risk (`acceptances[].review_id`) | in the acceptance authority's role; plus the user representative for High and Serious |
| Approve a task record (`status: approved`, `review_id`) | any tailoring role |
| Baseline a requirement (`status: baselined`, `review_id`) | any tailoring role |
| Approve the tailoring or the risk definitions (`approval.record`) | in the approval's `authority_role` |
| Approve the item definition (`status: approved`, `review_id`) | any tailoring role |

An AI reviewer is recorded with `human: false` and independence `I0`. A review with no named human reviewer can never have an accepting outcome. CI passing, tests passing or a file existing never accept anything.

Template:

```yaml
schema: susanoo/review/v0.1
id: REV-2026-001
title: Risk acceptance for EVT-BENCH-001 event risks
date: 2026-12-01
type: risk-acceptance            # technical-review | risk-acceptance | approval | independent-assessment
scope: [HAZ-PWR-001]
baseline: <git commit reviewed>
reviewers:
  - {role: ROLE-CE, person: <name>, human: true, independence: I1}
outcome: in-progress             # in-progress | accepted | accepted-with-actions | returned
findings: []
record: <link to minutes or signed record, if separate>
```
