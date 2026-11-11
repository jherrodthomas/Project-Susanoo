# PX4 Integration & Assurance Procedure

**Scope:** SUS-A1 observation UAV and SUS-I1 docking interfaces. **Status:** draft.

## Purpose
Use upstream PX4 Autopilot as a *candidate* externally maintained software component, with configuration/version control, interface validation and independent SUS-A1 safety assessment.

## Procedure
1. Select upstream tag and commit. Record license, external dependencies, build toolchain and hardware profile.
2. Reproduce a clean PX4 SITL simulation and capture logs.
3. Record ROS 2/DDS, MAVLink/MAVSDK and ground-station interface versions.
4. Define command authority, UAV/ground platform mode interactions and explicit failure behavior.
5. Perform FHA/PSSA on UAV functions and MIL-STD-882E interface hazards for docking and personnel exposure.
6. Derive safety-related requirements, verify simulations including fault injection and maintain discrepancy records.
7. Control changes to PX4 commit, parameters, airframe, interface contracts and simulator under PDaC.
8. Review any move to HIL or physical test separately; no approval inferred from SITL completion.

**Inputs:** CONOPS, flight/dock scenarios, PX4 baseline, architecture and hazard log.  
**Outputs:** software/dependency baseline, interface contract, simulation evidence, FHA/PSSA, integration test results and issue records.  
**Exit:** reproducible pinned simulated configuration, hazard-to-test traceability, open findings recorded, accountable engineering review.

[Integration plan](https://github.com/jherrodthomas/Project-Susanoo/blob/main/integrations/px4/README.md) · [Interface contract](https://github.com/jherrodthomas/Project-Susanoo/blob/main/integrations/px4/interface-contract.md) · [PX4 upstream](https://github.com/PX4/PX4-Autopilot)
