# Failure search SF-01 · Hydraulic supply loss in mid-stride on a slope

| Label | Value |
|---|---|
| data_kind | synthetic |
| evidence credit | none (no approved fidelity case) |
| simulator | sim/search/search.py over sim/plant/walker.py |
| plant spec | sim/spec/walker.yaml digest `48e1754c83f1` |
| scenario | SF-01 (FLT-01) |
| method | seeded Monte Carlo + cross-entropy falsification |

## Monte Carlo

400 uniform samples: safe 187 (46.8%), tip 24 (6.0%), hard-drop 189 (47.2%).

| Subset | Samples | Failures |
|---|---|---|
| load_holding=works | 199 | 12 (6.0%) |
| load_holding=fails | 201 | 201 (100.0%) |

Cross-entropy falsification: 480 evaluations, worst rho -3.849.

Parameter space: `slope_deg` {'uniform': [0, 15]}; `tau_leak_s` {'loguniform': [0.05, 5.0]}; `pilot_reaction_s` {'uniform': [0.5, 3.0]}; `stride_offset_m` {'uniform': [0.0, 0.3]}; `load_holding` {'choice': ['works', 'fails']}.

## Edge cases

| ID | Parameters (rounded) | Outcome | rho | No fault | Hazard | Probes that change the outcome |
|---|---|---|---|---|---|---|
| EC-01 | slope_deg=11.5, tau_leak_s=0.05, pilot_reaction_s=2.1, stride_offset_m=0.19, load_holding=fails | **hard-drop** | -3.835 | safe | HAZ-PIL-002 | load holding works → safe; slow leak (tau 3 s) → tip |
| EC-02 | slope_deg=12, tau_leak_s=0.06, pilot_reaction_s=0.6, stride_offset_m=0.03, load_holding=fails | **hard-drop** | -3.816 | safe | HAZ-PIL-002 | load holding works → safe |
| EC-03 | slope_deg=6, tau_leak_s=0.05, pilot_reaction_s=0.9, stride_offset_m=0.25, load_holding=fails | **hard-drop** | -3.835 | safe | HAZ-PIL-002 | load holding works → safe |
| EC-04 | slope_deg=9, tau_leak_s=0.06, pilot_reaction_s=1.8, stride_offset_m=0.04, load_holding=fails | **hard-drop** | -3.816 | safe | HAZ-PIL-002 | load holding works → safe |
| EC-05 | slope_deg=0, tau_leak_s=0.05, pilot_reaction_s=3, stride_offset_m=0.11, load_holding=fails | **hard-drop** | -3.835 | safe | HAZ-PIL-002 | load holding works → safe |
| EC-06 | slope_deg=1, tau_leak_s=0.06, pilot_reaction_s=1.3, stride_offset_m=0.11, load_holding=fails | **hard-drop** | -3.816 | safe | HAZ-PIL-002 | load holding works → safe |
| EC-07 | slope_deg=9, tau_leak_s=1.13, pilot_reaction_s=1.7, stride_offset_m=0.3, load_holding=fails | **tip** | -2.6285 | safe | HAZ-WLK-002 | flat ground → hard-drop |
| EC-08 | slope_deg=13, tau_leak_s=2.05, pilot_reaction_s=2.6, stride_offset_m=0.27, load_holding=works | **tip** | -2.4308 | safe | HAZ-WLK-002 | flat ground → safe |

## Findings for review

None.

Findings are drafts for the safety lead: a new hazard or causal factor is added to the hazard records only through review (CLAUDE.md).
