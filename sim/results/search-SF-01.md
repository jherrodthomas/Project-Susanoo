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

400 uniform samples: safe 128 (32.0%), tip 146 (36.5%), hard-drop 126 (31.5%).

| Subset | Samples | Failures |
|---|---|---|
| load_holding=works | 199 | 71 (35.7%) |
| load_holding=fails | 201 | 201 (100.0%) |

Cross-entropy falsification: 480 evaluations, worst rho -3.847.

Parameter space: `slope_deg` {'uniform': [0, 15]}; `tau_leak_s` {'loguniform': [0.05, 5.0]}; `pilot_reaction_s` {'uniform': [0.5, 3.0]}; `stride_offset_m` {'uniform': [0.0, 0.3]}; `load_holding` {'choice': ['works', 'fails']}.

## Edge cases

| ID | Parameters (rounded) | Outcome | rho | No fault | Hazard | Probes that change the outcome |
|---|---|---|---|---|---|---|
| EC-01 | slope_deg=8.5, tau_leak_s=0.05, pilot_reaction_s=2.5, stride_offset_m=0.03, load_holding=fails | **hard-drop** | -3.835 | safe | finding | load holding works → safe |
| EC-02 | slope_deg=0, tau_leak_s=0.05, pilot_reaction_s=3, stride_offset_m=0.11, load_holding=fails | **hard-drop** | -3.835 | safe | finding | load holding works → safe |
| EC-03 | slope_deg=1, tau_leak_s=0.06, pilot_reaction_s=1.3, stride_offset_m=0.11, load_holding=fails | **hard-drop** | -3.816 | safe | finding | load holding works → safe |
| EC-04 | slope_deg=8, tau_leak_s=0.05, pilot_reaction_s=1.5, stride_offset_m=0.2, load_holding=fails | **hard-drop** | -3.835 | safe | finding | load holding works → tip; slow leak (tau 3 s) → tip |
| EC-05 | slope_deg=8, tau_leak_s=0.08, pilot_reaction_s=2.1, stride_offset_m=0.21, load_holding=fails | **tip** | -2.828 | tip | finding | flat ground → hard-drop |
| EC-06 | slope_deg=2, tau_leak_s=0.4, pilot_reaction_s=2.1, stride_offset_m=0.27, load_holding=fails | **hard-drop** | -3.162 | safe | finding | load holding works → tip; slow leak (tau 3 s) → tip |
| EC-07 | slope_deg=9, tau_leak_s=0.14, pilot_reaction_s=1.3, stride_offset_m=0.28, load_holding=works | **tip** | -2.3485 | tip | finding | flat ground → safe |
| EC-08 | slope_deg=9, tau_leak_s=1.8, pilot_reaction_s=1.3, stride_offset_m=0.18, load_holding=works | **tip** | -2.2784 | safe | HAZ-WLK-002 | flat ground → safe |

## Findings for review

- **FND-SF-01-01** (EC-01, EC-02, EC-03, EC-04, EC-06): Uncontrolled vertical drop of the cockpit on loss of actuator supply with no protective stop under way; no hazard record covers occupant vertical impact
- **FND-SF-01-02** (EC-05, EC-07): Walker tips with no fault: case lies outside the nominal gait capability (terrain limit for CONOPS section 4)
- **FND-SF-01-03** (EC-08): HAZ-WLK-002 lists no causal factor for FLT-01 (fault causes: HAZ-SAF-001:CF2)

Findings are drafts for the safety lead: a new hazard or causal factor is added to the hazard records only through review (CLAUDE.md).
