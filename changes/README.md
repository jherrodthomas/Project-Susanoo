# Change requests (MIL-STD-882E 4.3.8, Task 304)

One `CR-NNN.yaml` per change (schema `pdac/schemas/change-request.schema.json`). When a change is `approved` or `implemented`, the validator (rule R10) requires every hazard it affects to carry a `reassessments` entry for it. Affected items are found through linked requirements, SSFs, mitigations (`HAZ-x:M1`) or configurations. If the reassessment outcome is `risk-increased` on a previously accepted hazard, a new acceptance dated on or after the reassessment is required.
