// ConceptOperations — SysML v2 view of the SUS-I1 CONOPS (SUS-CONOPS-001 rev 0.3-draft).
// Hand-authored; keep in step with concept/CONOPS.md sections 5-7.
// Status: unapproved concept. Mode transitions are proposed and have not been
// analysed; Task 206 (O&SHA) is responsible for assessing them.

package ConceptOperations {
    private import ScalarValues::*;
    private import SusanooSystem::*;

    // ------------------------------------------------------ mode triggers
    attribute def PowerUp;
    attribute def ReadinessConfirmed;
    attribute def SelfTestFailed;
    attribute def WalkEnable;
    attribute def ManipulateEnable;
    attribute def HoldRequested;
    attribute def UAVPrepareRequested;
    attribute def LaunchPermitted;
    attribute def RecoveryRequested;
    attribute def RetentionConfirmed;
    attribute def FaultDetected;
    attribute def FaultCleared;
    attribute def ShutdownRequested;
    attribute def ServiceRequested;
    attribute def ServiceComplete;

    // ------------------------------------------- CONOPS section 5 modes
    state def OperatingModes {
        doc /* MOD-01..MOD-10 from CONOPS section 5. */
        entry; then offSecured;

        state <'MOD-01'> offSecured   { doc /* Energy isolated, supported */ }
        state <'MOD-02'> startup      { doc /* Pilot readiness and self-test */ }
        state <'MOD-03'> standby      { doc /* Stable pose, motion inhibited */ }
        state <'MOD-04'> pilotedWalk  { doc /* Bounded operator locomotion */ }
        state <'MOD-05'> manipulation { doc /* Controlled payload handling */ }
        state <'MOD-06'> uavPrepare   { doc /* Dock, clearance and preflight */ }
        state <'MOD-07'> uavFlight    { doc /* Observation and return; walker stationary */ }
        state <'MOD-08'> uavRecovery  { doc /* Approach, capture, retention */ }
        state <'MOD-09'> degradedEmergency { doc /* Mode-specific fault response; not instant zero torque */ }
        state <'MOD-10'> maintenance  { doc /* Supported, isolated service */ }

        transition t01 first offSecured accept PowerUp then startup;
        transition t02 first startup accept ReadinessConfirmed then standby;
        transition t03 first startup accept SelfTestFailed then offSecured;
        transition t04 first standby accept WalkEnable then pilotedWalk;
        transition t05 first pilotedWalk accept HoldRequested then standby;
        transition t06 first standby accept ManipulateEnable then manipulation;
        transition t07 first manipulation accept HoldRequested then standby;
        transition t08 first standby accept UAVPrepareRequested then uavPrepare;
        transition t09 first uavPrepare accept LaunchPermitted then uavFlight;
        transition t10 first uavFlight accept RecoveryRequested then uavRecovery;
        transition t11 first uavRecovery accept RetentionConfirmed then standby;
        transition t12 first pilotedWalk accept FaultDetected then degradedEmergency;
        transition t13 first manipulation accept FaultDetected then degradedEmergency;
        transition t14 first uavRecovery accept FaultDetected then degradedEmergency;
        transition t15 first degradedEmergency accept FaultCleared then standby;
        transition t16 first standby accept ShutdownRequested then offSecured;
        transition t17 first offSecured accept ServiceRequested then maintenance;
        transition t18 first maintenance accept ServiceComplete then offSecured;
    }

    // ------------------------------------- CONOPS section 6 scenarios
    use case def <'SCN-001'> IngressStartup {
        subject sys : IntegratedSystem;
        actor pilot : Pilot;
        actor crew : GroundCrew;
        objective { doc /* Confirm supports, exclusion zone and pilot readiness; failed checks inhibit motion. */ }
    }
    use case def <'SCN-002'> Travel {
        subject sys : IntegratedSystem;
        actor pilot : Pilot;
        objective { doc /* Walk inside a defined stability envelope under state supervision. */ }
    }
    use case def <'SCN-003'> Handling {
        subject sys : IntegratedSystem;
        actor pilot : Pilot;
        objective { doc /* Manipulate a bounded nonhazardous payload with load and exclusion-zone checks. */ }
    }
    use case def <'SCN-004'> Observation {
        subject sys : IntegratedSystem;
        actor pilot : Pilot;
        actor airspace : AirspaceGnssRf;
        objective { doc /* Launch UAV from a permitted stationary state, collect imagery, return. */ }
    }
    use case def <'SCN-005'> Recovery {
        subject sys : IntegratedSystem;
        actor pilot : Pilot;
        objective { doc /* Approach only with dock ready; positive retention precedes charging or rotor-inhibit change. */ }
    }
    use case def <'SCN-006'> Shutdown {
        subject sys : IntegratedSystem;
        actor pilot : Pilot;
        actor crew : GroundCrew;
        objective { doc /* UAV accounted for, supported posture, energy isolated, pilot egress. */ }
    }
}
