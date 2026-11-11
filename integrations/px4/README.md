# PX4 integration — SUS-A1 candidate baseline

**Status:** proposed, not integrated or verified. This is an engineering integration plan, not a claim that PX4 or SUS-A1 is certified or airworthy.

## Decision
Adopt [PX4 Autopilot](https://github.com/PX4/PX4-Autopilot) as the **candidate** SUS-A1 flight-control software baseline. Keep PX4 upstream and version-pinned as an external dependency; do not vendor or fork PX4 in Susanoo until an actual divergence is justified.

**License:** BSD 3-Clause. Preserve original source/license notices when redistributing. External dependency review shall capture licenses and third-party notices.

## Functional split
- PX4: flight stabilization, navigation, flight modes, configured onboard failsafes and vehicle telemetry.
- SUS-A1 companion/integration: payload observation, mission interface and UAV dock handshake, avoiding unsafe simultaneous control authorities.
- SUS-M1: piloted walking/manipulation and pilot station. SUS-M1 does **not** use PX4 to control walker joints.
- SUS-I1 supervisory layer: coordinate readiness, UAV launch/recovery, operator alerting, docking interlocks, and system safety.
- QGroundControl: development/flight monitoring and parameter configuration, not a substitute for an approved operations procedure.

## Proposed interfaces
1. ROS 2 and uXRCE-DDS for telemetry and high-level integration where supported.
2. MAVLink/MAVSDK for mission-management operations under explicit state/authority constraints.
3. Defined application interface for dock readiness, retained state, mechanical release, rotor inhibit, launch clearance, approach permit and abort.
4. PDaC trace links from PX4 version/configuration through scenarios, safety analyses, requirements and tests.

## Dependency baseline register
| Item | Required baseline information |
|---|---|
| PX4 version | Tagged release and exact commit SHA (TBD) |
| Airframe | Model/geometry and airframe ID (TBD) |
| Firmware target | Board and OS (TBD) |
| Parameters | Exported configured parameter set (TBD) |
| ROS 2 | Distribution, px4_msgs branch/version and DDS bridge (TBD) |
| Gazebo | Tested simulator version and world model (TBD) |
| MAVLink/MAVSDK | Version and messages/API contract (TBD) |
| QGroundControl | Version and configuration (TBD) |
| Licenses/SBOM | Recorded and verified (TBD) |

## Incremental integration
**P0:** Run unmodified PX4 multicopter SITL; record build and simulator versions.  
**P1:** Connect QGroundControl and collect telemetry/logs.  
**P2:** Connect ROS 2 telemetry only; record message compatibility and time sync.  
**P3:** Implement simulation-only launch/recover mission state machine with explicit authority and mode checks.  
**P4:** Add simulated docking sensors, rotor inhibit and abort; inject faults.  
**P5:** Conduct UAV FHA, PSSA and system interface hazard analyses, close design gaps.  
**P6:** Evaluate HIL and physical test readiness through formal safety reviews; no automatic flight authorization.

## Offboard control warning
Do not publish setpoints indiscriminately. PX4's own documentation warns that ROS 2 setpoints can collide with onboard controller publishers. Use documented control modes and verify loss-of-offboard behavior. Prefer the PX4 ROS 2 Interface Library for custom modes if justified; experimental interfaces must be pinned and assessed.

## Review references
- https://github.com/PX4/PX4-Autopilot
- https://docs.px4.io/main/en/ros2/
- https://docs.px4.io/main/en/simulation/
- https://docs.px4.io/main/en/flight_modes/offboard.html
- https://github.com/PX4/px4_msgs

**Non-goals:** weapons, autonomous targeting, using PX4 as a pilot-safety controller for SUS-M1, or asserting DO-178C/ARP4761A qualification without evidence.
