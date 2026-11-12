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

400 uniform samples: safe 173 (43.2%), tip 50 (12.5%), hard-drop 177 (44.2%).

| Subset | Samples | Failures |
|---|---|---|
| load_holding=works | 199 | 26 (13.1%) |
| load_holding=fails | 201 | 201 (100.0%) |

Cross-entropy falsification: 480 evaluations, worst rho -3.849.

Parameter space: `slope_deg` {'uniform': [0, 20]}; `tau_leak_s` {'loguniform': [0.05, 5.0]}; `pilot_reaction_s` {'uniform': [0.5, 3.0]}; `stride_offset_m` {'uniform': [0.0, 0.3]}; `load_holding` {'choice': ['works', 'fails']}.

## Edge cases

| ID | Parameters (rounded) | Outcome | rho | No fault | Hazard | Probes that change the outcome |
|---|---|---|---|---|---|---|
| EC-01 | slope_deg=15.5, tau_leak_s=0.05, pilot_reaction_s=2.1, stride_offset_m=0.19, load_holding=fails | **hard-drop** | -3.835 | safe | HAZ-PIL-002 | load holding works → safe; slow leak (tau 3 s) → tip |
| EC-02 | slope_deg=16, tau_leak_s=0.06, pilot_reaction_s=0.6, stride_offset_m=0.03, load_holding=fails | **hard-drop** | -3.816 | safe | HAZ-PIL-002 | load holding works → safe |
| EC-03 | slope_deg=8.5, tau_leak_s=0.05, pilot_reaction_s=0.9, stride_offset_m=0.25, load_holding=fails | **hard-drop** | -3.835 | safe | HAZ-PIL-002 | load holding works → safe; slow leak (tau 3 s) → tip |
| EC-04 | slope_deg=20, tau_leak_s=0.07, pilot_reaction_s=2, stride_offset_m=0.25, load_holding=fails | **hard-drop** | -3.797 | tip | finding | load holding works → tip; slow leak (tau 3 s) → tip |
| EC-05 | slope_deg=19, tau_leak_s=0.18, pilot_reaction_s=1.6, stride_offset_m=0.26, load_holding=fails | **hard-drop** | -3.589 | tip | finding | load holding works → tip; slow leak (tau 3 s) → tip |
| EC-06 | slope_deg=17, tau_leak_s=0.45, pilot_reaction_s=2.1, stride_offset_m=0.27, load_holding=fails | **tip** | -2.7495 | safe | HAZ-WLK-002 | flat ground → hard-drop |
| EC-07 | slope_deg=16, tau_leak_s=2.56, pilot_reaction_s=2.4, stride_offset_m=0.16, load_holding=works | **tip** | -2.3252 | safe | HAZ-WLK-002 | pilot reacts in 0.5 s → safe; flat ground → safe |
| EC-08 | slope_deg=19.5, tau_leak_s=1.94, pilot_reaction_s=2.4, stride_offset_m=0.24, load_holding=works | **tip** | -2.3188 | tip | finding | flat ground → safe |

## Findings for review

- **FND-SF-01-01** (EC-04, EC-05, EC-08): Walker tips with no fault: case lies outside the nominal gait capability (terrain limit for CONOPS section 4)

Findings are drafts for the safety lead: a new hazard or causal factor is added to the hazard records only through review (CLAUDE.md).
