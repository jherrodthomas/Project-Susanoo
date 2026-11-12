// PX4Integration — SysML v2 view of the SUS-A1 / PX4 integration boundary.
// Hand-authored; keep in step with integrations/px4/README.md, interface-contract.md and the IF-PX4-nnn
// interfaces in architecture/item-definition.yaml (SUS-I1-INT is the integration manager / adapter).
// Status: proposed, not implemented or verified. Thresholds, timing and safe
// states are TBD. PX4 is an external, version-pinned dependency.

package PX4Integration {
    private import ScalarValues::*;
    private import SusanooArchitecture::*;

    // --------------------------------------------------------- structure
    part def PX4Autopilot :> FlightController {
        doc /* Upstream PX4 (BSD-3-Clause), pinned by tag + commit SHA. Owns flight
             * stabilisation, navigation, flight modes and configured failsafes. */
        attribute version : String;
        attribute commitSha : String;
        attribute parameterSetHash : String;
        port mavlink : MissionPort;
        port dds : TelemetryPort;
    }
    part def UAVControlAdapter {
        doc /* Validated command adapter: the only path for SUS-I1 mission requests. Fail-closed. */
        port toPx4 : ~MissionPort;
        port fromSupervisor : ~PermitPort;
    }
    part def IntegrationSupervisor {
        doc /* SUS-I1 supervisory layer: readiness, launch/recovery, interlocks, alerting. */
        port permit : PermitPort;
        port telemetryIn : ~TelemetryPort;
        port dockState : ~DockStatePort;
    }
    part def GroundControlStation {
        doc /* QGroundControl: development monitoring and parameters only. */
    }

    port def MissionPort    { doc /* MAVLink / MAVSDK mission operations */ }
    port def TelemetryPort  { doc /* ROS 2 via uXRCE-DDS: state, health, arming (IF-PX4-001/002) */ }
    port def PermitPort     { doc /* Launch permit/revoke, recovery/abort intent (IF-PX4-005/006) */ }
    port def DockStatePort  { doc /* Dock occupied/retained, walker posture (IF-PX4-003/004) */ }

    part def PX4IntegrationContext {
        part px4 : PX4Autopilot;
        part adapter : UAVControlAdapter;
        part supervisor : IntegrationSupervisor;
        part dock : UavDock;
        part walker : Walker;
        part gcs : GroundControlStation;

        connection if001 connect px4.dds to supervisor.telemetryIn { doc /* IF-PX4-001/002 state, health, arming */ }
        connection if005 connect supervisor.permit to adapter.fromSupervisor { doc /* IF-PX4-005/006 permit, recovery, abort */ }
        connection ifMav connect adapter.toPx4 to px4.mavlink { doc /* validated mission commands */ }
        connection if003 connect dock to supervisor { doc /* IF-PX4-003 dock occupied/retained */ }
        connection if004 connect walker to supervisor { doc /* IF-PX4-004 posture / stationary */ }
        connection if009 connect dock to px4 { doc /* IF-PX4-009 power/charging handshake, rotor inhibit */ }
        connection gcsLink connect gcs to px4 { doc /* development telemetry and parameters */ }
    }

    // ------------------------------------------- launch permit behaviour
    attribute def DockRetainedFresh;
    attribute def PostureStationary;
    attribute def PilotRequestsLaunch;
    attribute def StaleOrInconsistentState;
    attribute def UAVClearOfDock;
    attribute def PermitRevoked;
    attribute def LinkLost;
    attribute def Recovered;

    state def LaunchPermit {
        doc /* Fail-closed launch authorisation held by the integration supervisor. */
        entry; then denied;
        state denied     { doc /* default; any stale or inconsistent input returns here */ }
        state armable    { doc /* dock state fresh and walker stationary */ }
        state permitted  { doc /* explicit pilot request accepted */ }
        state airborne   { doc /* PX4 owns flight; walker E-stop does not cut motors */ }
        state contingency { doc /* analysed lost-link behaviour on BOTH aircraft and walker */ }

        transition t1 first denied accept PostureStationary then armable;
        transition t2 first armable accept PilotRequestsLaunch then permitted;
        transition t3 first armable accept StaleOrInconsistentState then denied;
        transition t4 first permitted accept StaleOrInconsistentState then denied;
        transition t5 first permitted accept UAVClearOfDock then airborne;
        transition t6 first permitted accept PermitRevoked then denied;
        transition t7 first airborne accept LinkLost then contingency;
        transition t8 first airborne accept Recovered then denied;
        transition t9 first contingency accept Recovered then denied;
    }

    // -------------------------------------------- integration requirements
    requirement def <'PX4-R-001'> LaunchOnlyWhenPermitted {
        doc /* Launch shall be authorised only in correct walker posture and dock state. */
    }
    requirement def <'PX4-R-002'> StaleStateBlocksLaunch {
        doc /* Stale or inconsistent dock state shall prevent launch authorisation. */
    }
    requirement def <'PX4-R-003'> NoAuthorityCollision {
        doc /* Flight and ground controller authority collision shall be prevented. */
    }
    requirement def <'PX4-R-004'> LinkLossDoesNotMoveWalker {
        doc /* Lost link during docking shall abort appropriately and not command walker movement. */
    }
    requirement px4r001 : LaunchOnlyWhenPermitted;
    requirement px4r002 : StaleStateBlocksLaunch;
    requirement px4r003 : NoAuthorityCollision;
    requirement px4r004 : LinkLossDoesNotMoveWalker;
}
