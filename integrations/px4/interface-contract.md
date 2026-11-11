# SUS-I1 / PX4 interface contract — preliminary

**Status:** draft, not implemented. Interface direction, authority and fail behavior must be reviewed before implementation.

The IF-PX4 interfaces are also recorded, with endpoints and hazard links, in [`architecture/item-definition.yaml`](../../architecture/item-definition.yaml). Keep the two in step until this table is generated from the record.

| ID | Interface | Producer → Consumer | Control/safety concern |
|---|---|---|---|
| IF-PX4-001 | Flight state, position, status | PX4 → SUS-I1 | Freshness and source validity |
| IF-PX4-002 | UAV health and arming state | PX4 → SUS-I1 | Disagreement handling |
| IF-PX4-003 | Dock occupied/retained | Dock → SUS-I1 / SUS-A1 | Independent sensor plausibility |
| IF-PX4-004 | Ground platform posture/stationary | SUS-M1 → integration manager | Launch/recovery envelope |
| IF-PX4-005 | Launch permit/revoke | Integration manager → UAV control adapter | Explicit authorization and fail-closed logic |
| IF-PX4-006 | Recovery/abort intent | Integration manager → UAV control adapter | Airborne contingency on lost link |
| IF-PX4-007 | UAV video and mission cues | SUS-A1 → pilot HMI | Latency, distraction and trust |
| IF-PX4-008 | Fault and contingency notification | Both directions | Time stamping and priority |
| IF-PX4-009 | Power/charging handshake | Dock ↔ UAV power subsystem | Rotor inhibit, energy isolation |

## Authority principles
- PX4 remains responsible for onboard flight control and configured aircraft failsafes.
- The SUS-I1 supervisor may request mission operations only through a validated command adapter.
- Ground walker emergency stop does not imply automatic aircraft motor cutoff while airborne.
- Loss of system integration link must invoke defined, analyzed contingencies on *both* aircraft and walker.
- Docking requires independently defined mechanical retention and rotor safety; software status alone is not physical evidence of retention.
- All numeric thresholds, timing, control ownership and safe states are TBD.

## Acceptance tests to derive
- Transition to launch permitted only in correct walker posture/dock state.
- Stale or inconsistent dock state prevents launch command authorization.
- Flight/ground controller authority collision is prevented.
- Offboard-loss contingency behavior is verified in SITL.
- Lost link during docking aborts appropriately and does not command walker movement.
- Rotor startup inhibited when physically retained, with fault-tolerant hardware design to be studied.
