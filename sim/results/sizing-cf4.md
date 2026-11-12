# SZ-01 · Ankle and knee torque against supply loss on a slope

| Label | Value |
|---|---|
| data_kind | synthetic |
| evidence credit | none (no approved fidelity case) |
| simulator | sim/mujoco/l2.py (level 2, MuJoCo 3.3.5); sim/spec/walker_l2.yaml |
| plant spec | sim/spec/walker.yaml digest `48e1754c83f1` |
| scenario | HAZ-WLK-002 CF4: FLT-01 supply loss with load holding working |
| purpose | draft sizing input to the actuation trade (TS-001, DQ-006); not a design value |

Envelope grid: 378 cases (`pilot_reaction_s` [0.5, 1.5, 3.0], `slope_deg` [0, 10, 14, 16, 18, 20], `stride_offset_m` [0.0, 0.06, 0.12], `tau_leak_s` [0.05, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0]). Corner grid: 504 cases. A failure is any outcome other than safe. m g L_foot = 17658 N m. Assumed in `sim/spec/walker_l2.yaml`: ankle 20000, knee 60000, hip 40000 N m.

## Sweep: ankle_torque_max_nm (other joints as assumed)

| Value (N m) | Ratio to m g L_foot | Failures | Failing cases (first 3) |
|---|---|---|---|
| 15000 | 0.85 | 53 | 14°, offset 0.12 m, leak τ 3.0 s, pilot 3.0 s → tip; 14°, offset 0.12 m, leak τ 5.0 s, pilot 0.5 s → tip; 14°, offset 0.12 m, leak τ 5.0 s, pilot 3.0 s → tip |
| 20000 | 1.13 | 4 | 20°, offset 0.12 m, leak τ 3.0 s, pilot 1.5 s → tip; 20°, offset 0.12 m, leak τ 3.0 s, pilot 3.0 s → tip; 20°, offset 0.12 m, leak τ 5.0 s, pilot 1.5 s → tip |
| 22000 | 1.25 | 2 | 20°, offset 0.12 m, leak τ 3.0 s, pilot 1.5 s → tip; 20°, offset 0.12 m, leak τ 3.0 s, pilot 3.0 s → tip |
| 24000 | 1.36 | 0 | — |
| 26500 | 1.50 | 0 | — |

Lowest value that clears the grid: 24000.

## Sweep: knee_torque_max_nm (ankle_torque_max_nm 26500)

| Value (N m) | Failures | Failing cases (first 3) |
|---|---|---|
| 10000 | 30 | 0°, offset 0.0 m, leak τ 2.0 s, pilot 0.5 s → hard-drop; 0°, offset 0.0 m, leak τ 3.0 s, pilot 0.5 s → tip; 0°, offset 0.0 m, leak τ 3.0 s, pilot 1.5 s → hard-drop |
| 15000 | 0 | — |
| 20000 | 0 | — |
| 30000 | 0 | — |

Lowest value that clears the grid: 15000.

## Proposal (draft, I0)

Ankle 26500 N m (1.501 m g L_foot), knee 22500 N m. Preliminary. Ankle 1.5 m g L_foot at full supply (0.6 m g L_foot at the 0.4 load-holding threshold), about 10% above the lowest value that clears the grid; knee 1.5 times the lowest value that clears it with that ankle. Joint torque is taken to fall in proportion to supply (level-2 assumption, as A4 at level 1).

Failures with the proposal on the envelope and corner grids: 0.
Failures on the corner grid at the lowest clear ankle value: 0.

Level 2 only: level 1 has no joint torques. Supply loss with failed load holding drops the cockpit at any torque (HAZ-PIL-002); sizing does not address it.
