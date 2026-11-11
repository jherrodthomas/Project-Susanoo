# Verification records (MIL-STD-882E 4.3.6, Task 401)

One `VER-NNN.yaml` per verification activity (schema `pdac/schemas/verification.schema.json`). Mitigations cite these by `evidence_ids`. A hazard can only move to `verified` when every selected mitigation is implemented and has passed evidence (rule R04). Set `simulated: true` for simulation-only results; they never stand in for hardware verification.
