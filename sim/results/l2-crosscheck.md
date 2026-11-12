# Level-1 vs level-2 cross-check

| Label | Value |
|---|---|
| data_kind | synthetic |
| evidence credit | none (no approved fidelity case) |
| simulator | sim/plant/walker.py (level 1) and sim/mujoco/l2.py (level 2, MuJoCo 3.3.5) |
| plant spec | sim/spec/walker.yaml digest `48e1754c83f1` |
| scenario | Fault catalogue, no-fault slopes and every failure-search edge case |
| purpose | fidelity cross-check between two models; not validation against hardware |

## Agreement by family

| Family | Cases | Same outcome |
|---|---|---|
| CAT · Fault catalogue (sim/faults.yaml) | 9 | 8 (89%) |
| NOM · No fault (capability by slope) | 6 | 5 (83%) |
| SF-01 · Failure search SF-01: Hydraulic supply loss in mid-stride on a slope (edge cases) | 8 | 8 (100%) |

## Cases

| ID | Level 1 | Level 2 | Mishap time L1 / L2 (s) | Impact L1 / L2 (m/s) | Agree |
|---|---|---|---|---|---|
| NOM-00 | safe | safe | — / — | 0.0 / 0.0 | yes |
| NOM-08 | safe | safe | — / — | 0.0 / 0.0 | yes |
| NOM-12 | safe | safe | — / — | 0.0 / 0.0 | yes |
| NOM-15 | safe | safe | — / — | 0.0 / 0.0 | yes |
| NOM-20 | safe | safe | — / — | 0.0 / 0.0 | yes |
| NOM-25 | safe | tip | — / 3.236 | 0.0 / 0.0 | **no** |
| CAT-STOP | safe | safe | — / — | 0.0 / 0.0 | yes |
| CAT-01-HOLD | safe | safe | — / — | 0.0 / 0.0 | yes |
| CAT-01-NOHOLD | hard-drop | hard-drop | 1.575 / 1.786 | 4.835 / 4.11 | yes |
| CAT-01-SLOW-8 | safe | safe | — / — | 0.0 / 0.0 | yes |
| CAT-02-MON | safe | safe | — / — | 0.0 / 0.0 | yes |
| CAT-02-NOMON | tip | tip | 2.875 / 4.284 | 0.0 / 0.0 | yes |
| CAT-03 | hard-drop | hard-drop | 1.49 / 1.616 | 4.856 / 4.101 | yes |
| CAT-04-BRAKE | safe | safe | — / — | 0.0 / 0.0 | yes |
| CAT-04-NOBRAKE | hard-drop | safe | 2.59 / — | 2.528 / 0.0 | **no** |
| SF-01/EC-01 | hard-drop | hard-drop | 1.575 / 1.72 | 4.835 / 4.134 | yes |
| SF-01/EC-02 | hard-drop | hard-drop | 1.59 / 1.808 | 4.816 / 4.129 | yes |
| SF-01/EC-03 | hard-drop | hard-drop | 1.575 / 1.722 | 4.835 / 4.129 | yes |
| SF-01/EC-04 | hard-drop | hard-drop | 1.59 / 1.814 | 4.816 / 4.121 | yes |
| SF-01/EC-05 | hard-drop | hard-drop | 1.575 / 1.786 | 4.835 / 4.112 | yes |
| SF-01/EC-06 | hard-drop | hard-drop | 1.59 / 1.818 | 4.816 / 4.116 | yes |
| SF-01/EC-07 | tip | tip | 2.695 / 2.92 | 0.0 / 0.0 | yes |
| SF-01/EC-08 | tip | tip | 2.92 / 3.468 | 0.0 / 0.0 | yes |

## Disagreements

- **NOM-25** (L1 safe, L2 tip): Level 2 tips the no-fault gait from about 24 degrees, level 1 from about 27 (both hold at 20). The level-2 controller keeps the commanded centre of pressure within 90% of the foot, a margin the level-1 limit (A3) does not have: with the full foot, level 2 holds 25 and tips at 26. The ankle stays below its torque limit (15.5 of 20 kN m at 25 degrees). Level 2 is the more pessimistic; the slope limit should rest on it.
- **CAT-04-NOBRAKE** (L1 hard-drop, L2 safe): Level 1 scales leg support force linearly with capacity (assumption A4), so 35% capacity cannot hold the body. In level 2 nearly straight legs need little knee torque, so 35% of the knee torque still holds. A4 is pessimistic for straight-legged stance and optimistic for a deep crouch.

Notes are AI drafts (I0). A disagreement is a finding about the models: the level that is closer to the real machine is unknown until hardware data exists.
