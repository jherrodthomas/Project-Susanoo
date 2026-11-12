# Plant results: fault catalogue

| Label | Value |
|---|---|
| data_kind | synthetic |
| evidence credit | none (no approved fidelity case) |
| simulator | sim/plant/walker.py (reduced-order, stdlib) |
| plant spec | sim/spec/walker.yaml digest `48e1754c83f1` |
| scenario | Fault catalogue sim/faults.yaml on flat ground and an 8 degree slope |

Outcome per fault and configuration. `rho` is the robustness margin (negative = margin exhausted). A mishap ends the run (contact not modelled).

## No-fault capability

| Slope (deg) | Outcome | rho |
|---|---|---|
| 0 | safe | 0.7556 |
| 4 | safe | 0.6658 |
| 8 | safe | 0.5702 |
| 10 | safe | 0.52 |
| 12 | safe | 0.4681 |
| 15 | safe | 0.3866 |
| 20 | safe | 0.2404 |
| 25 | safe | 0.0712 |
| 30 | tip | -1.5959 |

## Faults

### FLT-01 · Hydraulic supply pressure loss

Causes: HAZ-SAF-001:CF2, HAZ-WLK-002:CF4, HAZ-PIL-002:CF1. Injection: supply fraction decays exponentially to zero from onset with time constant tau_leak_s.

| Slope | Configuration | Outcome | rho | Alarm (s) | Stop (s, by) | Hold (s) | Mishap (s) | Impact (m/s) |
|---|---|---|---|---|---|---|---|---|
| 0 | mitigated | **safe** | 0.1337 | 1.11 | 2.615 (pilot) | 1.38 | — | 0.0 |
| 0 | no load holding | **hard-drop** | -3.339 | 1.11 | — | — | 1.92 | 4.339 |
| 0 | no monitor | **safe** | 0.1337 | 1.11 | 2.615 (pilot) | 1.38 | — | 0.0 |
| 0 | no hold, slow pilot | **hard-drop** | -3.339 | 1.11 | — | — | 1.92 | 4.339 |
| 8 | mitigated | **safe** | -0.0446 | 1.11 | 2.615 (pilot) | 1.38 | — | 0.0 |
| 8 | no load holding | **hard-drop** | -3.339 | 1.11 | — | — | 1.92 | 4.339 |
| 8 | no monitor | **safe** | -0.0446 | 1.11 | 2.615 (pilot) | 1.38 | — | 0.0 |
| 8 | no hold, slow pilot | **hard-drop** | -3.339 | 1.11 | — | — | 1.92 | 4.339 |

### FLT-02 · Posture feedback frozen (stale)

Causes: HAZ-WLK-001:CF1, HAZ-WLK-001:CF3. Injection: controller reads the CoM state frozen at onset.

| Slope | Configuration | Outcome | rho | Alarm (s) | Stop (s, by) | Hold (s) | Mishap (s) | Impact (m/s) |
|---|---|---|---|---|---|---|---|---|
| 0 | mitigated | **safe** | 0.7556 | — | 1.155 (monitor) | 1.155 | — | 0.0 |
| 0 | no load holding | **tip** | -1.2193 | — | 1.155 (monitor) | — | 2.865 | 0.0 |
| 0 | no monitor | **tip** | -2.3889 | — | — | — | 2.875 | 0.0 |
| 0 | no hold, slow pilot | **tip** | -1.2193 | — | 1.155 (monitor) | — | 2.865 | 0.0 |
| 8 | mitigated | **safe** | 0.5702 | — | 1.155 (monitor) | 1.155 | — | 0.0 |
| 8 | no load holding | **tip** | -1.6383 | — | 1.155 (monitor) | — | 2.465 | 0.0 |
| 8 | no monitor | **tip** | -2.2073 | — | — | — | 2.815 | 0.0 |
| 8 | no hold, slow pilot | **tip** | -1.6383 | — | 1.155 (monitor) | — | 2.465 | 0.0 |

### FLT-03 · Protective stop commands zero torque

Causes: HAZ-SAF-001:CF1. Injection: a protective stop requested at onset removes leg force and ankle torque instead of the mode-specific stop.

| Slope | Configuration | Outcome | rho | Alarm (s) | Stop (s, by) | Hold (s) | Mishap (s) | Impact (m/s) |
|---|---|---|---|---|---|---|---|---|
| 0 | mitigated | **hard-drop** | -3.856 | — | 1.0 (faulty) | — | 1.49 | 4.856 |
| 0 | no load holding | **hard-drop** | -3.856 | — | 1.0 (faulty) | — | 1.49 | 4.856 |
| 0 | no monitor | **hard-drop** | -3.856 | — | 1.0 (faulty) | — | 1.49 | 4.856 |
| 0 | no hold, slow pilot | **hard-drop** | -3.856 | — | 1.0 (faulty) | — | 1.49 | 4.856 |
| 8 | mitigated | **hard-drop** | -3.856 | — | 1.0 (faulty) | — | 1.49 | 4.856 |
| 8 | no load holding | **hard-drop** | -3.856 | — | 1.0 (faulty) | — | 1.49 | 4.856 |
| 8 | no monitor | **hard-drop** | -3.856 | — | 1.0 (faulty) | — | 1.49 | 4.856 |
| 8 | no hold, slow pilot | **hard-drop** | -3.856 | — | 1.0 (faulty) | — | 1.49 | 4.856 |

### FLT-04 · Electric bus undervoltage

Causes: HAZ-SAF-001:CF2, HAZ-WLK-002:CF4, HAZ-PIL-002:CF1. Injection: torque capacity decays to electric_sag_floor from onset with time constant tau_leak_s.

| Slope | Configuration | Outcome | rho | Alarm (s) | Stop (s, by) | Hold (s) | Mishap (s) | Impact (m/s) |
|---|---|---|---|---|---|---|---|---|
| 0 | mitigated | **safe** | 0.1597 | 1.19 | 2.695 (pilot) | 1.875 | — | 0.0 |
| 0 | no load holding | **hard-drop** | -1.528 | 1.19 | — | — | 2.59 | 2.528 |
| 0 | no monitor | **safe** | 0.1597 | 1.19 | 2.695 (pilot) | 1.875 | — | 0.0 |
| 0 | no hold, slow pilot | **hard-drop** | -1.528 | 1.19 | — | — | 2.59 | 2.528 |
| 8 | mitigated | **safe** | -0.045 | 1.19 | 2.695 (pilot) | 1.875 | — | 0.0 |
| 8 | no load holding | **hard-drop** | -1.528 | 1.19 | — | — | 2.59 | 2.528 |
| 8 | no monitor | **safe** | -0.045 | 1.19 | 2.695 (pilot) | 1.875 | — | 0.0 |
| 8 | no hold, slow pilot | **hard-drop** | -1.528 | 1.19 | — | — | 2.59 | 2.528 |

