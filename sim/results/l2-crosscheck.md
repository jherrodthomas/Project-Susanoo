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
| NOM · No fault (capability by slope) | 4 | 3 (75%) |
| SF-01 · Failure search SF-01: Hydraulic supply loss in mid-stride on a slope (edge cases) | 8 | 5 (62%) |

## Cases

| ID | Level 1 | Level 2 | Mishap time L1 / L2 (s) | Impact L1 / L2 (m/s) | Agree |
|---|---|---|---|---|---|
| NOM-00 | safe | safe | — / — | 0.0 / 0.0 | yes |
| NOM-08 | safe | safe | — / — | 0.0 / 0.0 | yes |
| NOM-12 | safe | safe | — / — | 0.0 / 0.0 | yes |
| NOM-15 | tip | safe | 2.47 / — | 0.0 / 0.0 | **no** |
| CAT-STOP | safe | safe | — / — | 0.0 / 0.0 | yes |
| CAT-01-HOLD | safe | safe | — / — | 0.0 / 0.0 | yes |
| CAT-01-NOHOLD | hard-drop | hard-drop | 1.575 / 1.784 | 4.835 / 4.105 | yes |
| CAT-01-SLOW-8 | safe | safe | — / — | 0.0 / 0.0 | yes |
| CAT-02-MON | safe | safe | — / — | 0.0 / 0.0 | yes |
| CAT-02-NOMON | tip | tip | 3.22 / 4.492 | 0.0 / 0.0 | yes |
| CAT-03 | hard-drop | hard-drop | 1.49 / 1.616 | 4.856 / 4.099 | yes |
| CAT-04-BRAKE | safe | safe | — / — | 0.0 / 0.0 | yes |
| CAT-04-NOBRAKE | hard-drop | safe | 2.59 / — | 2.528 / 0.0 | **no** |
| SF-01/EC-01 | hard-drop | hard-drop | 1.575 / 1.778 | 4.835 / 4.113 | yes |
| SF-01/EC-02 | hard-drop | hard-drop | 1.575 / 1.784 | 4.835 / 4.114 | yes |
| SF-01/EC-03 | hard-drop | hard-drop | 1.59 / 1.816 | 4.816 / 4.106 | yes |
| SF-01/EC-04 | hard-drop | hard-drop | 1.575 / 1.732 | 4.835 / 4.126 | yes |
| SF-01/EC-05 | tip | hard-drop | 1.61 / 1.808 | 0.0 / 4.092 | **no** |
| SF-01/EC-06 | hard-drop | hard-drop | 2.04 / 2.422 | 4.162 / 3.435 | yes |
| SF-01/EC-07 | tip | safe | 1.205 / — | 0.0 / 0.0 | **no** |
| SF-01/EC-08 | tip | safe | 2.445 / — | 0.0 / 0.0 | **no** |

## Disagreements

- **NOM-15** (L1 tip, L2 safe): Level 1 limits the centre of pressure to an assumed +/- L cos(slope); in level 2 the same limit comes from foot contact, and the sway is tracked with less centre-of-pressure demand, so the 15 degree gait holds. The level-1 terrain limit (12-15 degrees) is pessimistic by this measure.
- **CAT-04-NOBRAKE** (L1 hard-drop, L2 safe): Level 1 scales leg support force linearly with capacity (assumption A4), so 35% capacity cannot hold the body. In level 2 nearly straight legs need little knee torque, so 35% of the knee torque still holds. A4 is pessimistic for straight-legged stance and optimistic for a deep crouch.
- **SF-01/EC-05** (L1 tip, L2 hard-drop): Level 1 tips this case even with no fault (the terrain-limit finding); level 2 holds it with no fault. With the burst and failed load holding, level 2 does not tip but drops vertically, the HAZ-PIL-002 mechanism. The level-1 terrain limit and its no-fault tips come from assumption A3 and are not reproduced at level 2 (also EC-07).
- **SF-01/EC-07** (L1 tip, L2 safe): Level 1 tips at 1.2 s as its capacity-scaled centre-of-pressure limit (A3) shrinks below the capture point; level 2 locks at 1.23 s with the CoM over the stance foot and holds. Same mechanism as EC-08. Before load holding was modelled as a joint constraint, explicit lock springs made the locked walker rock and tip at about 5 s, depending on rounding; that tip was a numerical artefact.
- **SF-01/EC-08** (L1 tip, L2 safe): Level 1 loses balance before load holding engages because its centre-of-pressure limit shrinks with capacity (A3). In level 2 the ankle torque limit shrinks, but the foot still supports the body and the hold engages with the CoM over the foot. The tip found by the level-1 search is not reproduced at level 2; HAZ-WLK-002 CF4 rests on it.

Notes are AI drafts (I0). A disagreement is a finding about the models: the level that is closer to the real machine is unknown until hardware data exists.
