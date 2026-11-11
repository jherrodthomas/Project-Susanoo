// Susanoo architecture: the SUS-I1 context, its elements, the external elements and every interface.
// Hand-written. Checked against architecture/item-definition.yaml by tools/sysml/check.py (rules M1, M2, M4, M9)
// and validated by the OMG pilot implementation (tools/sysml/pilot/validate.sh).
package SusanooArchitecture {
    private import SusanooLibrary::*;
    private import SusanooFunctions::*;

    // ------------------------------------------------------------ definitions
    part def IntegratedSystem { doc /* SUS-I1 integrated mechanized walker and observation UAV */ }
    part def Walker { doc /* Piloted walker */ }
    part def PilotStation { doc /* Pilot station, restraints, displays and controls */ }
    part def MotionControl { doc /* Mission, motion and balance control */ }
    part def LegsAndChassis { doc /* Chassis, legs, joint actuators and stability sensing */ }
    part def Manipulators { doc /* Manipulation arms and end effectors */ }
    part def SafetyMonitor { doc /* Independent safety monitor, protective stop and isolation */ }
    part def UavDock { doc /* UAV dock, retention, charging and release */ }
    part def PowerSystem { doc /* Power generation, storage, distribution and thermal control */ }
    part def EngineGenerator { doc /* Engine-generator and governor */ }
    part def BatteryPack { doc /* Battery pack, BMS and contactors */ }
    part def PowerDistribution { doc /* Protected power distribution */ }
    part def ObservationUav { doc /* Dockable observation UAV */ }
    part def FlightController { doc /* PX4-based flight controller */ }
    part def NavigationAndTelemetry { doc /* Navigation sensors, camera and telemetry */ }
    part def UavPower { doc /* UAV battery and power management */ }
    part def Propulsion { doc /* Motors, ESCs and propellers */ }
    part def IntegrationManager { doc /* Integration manager and PX4 command adapter */ }
    part def GroundSupport { doc /* Ground support, maintenance supports, charging and test equipment */ }
    part def Pilot { doc /* Pilot */ }
    part def SafetyObserver { doc /* Safety observer */ }
    part def GroundCrew { doc /* Ground crew and maintainers */ }
    part def Bystanders { doc /* Bystanders */ }
    part def Terrain { doc /* Terrain and obstacles */ }
    part def Airspace { doc /* Airspace, people and property under the UAV */ }
    part def GnssRfEnvironment { doc /* GNSS and RF environment */ }
    part def Weather { doc /* Weather */ }

    // ------------------------------------------------------------ context
    part context {
        part <'EXT-PILOT'> pilot : Pilot {
            doc /* Trained, restrained pilot; may become incapacitated (SCN-104) */
            @ExternalElement;
        }
        part <'EXT-OBSERVER'> safetyObserver : SafetyObserver {
            doc /* Holds an independent stop and enforces the exclusion zone */
            @ExternalElement;
        }
        part <'EXT-CREW'> groundCrew : GroundCrew {
            doc /* Follow isolation procedures; may not */
            @ExternalElement;
        }
        part <'EXT-BYSTANDER'> bystanders : Bystanders {
            doc /* Kept outside the exclusion zone by procedure only */
            @ExternalElement;
        }
        part <'EXT-TERRAIN'> terrain : Terrain {
            doc /* Slope, payload and ground limits TBD (CONOPS 4) */
            @ExternalElement;
        }
        part <'EXT-AIRSPACE'> airspace : Airspace {
            doc /* Operations inside a defined, unpopulated volume */
            @ExternalElement;
        }
        part <'EXT-GNSS-RF'> gnssRf : GnssRfEnvironment {
            doc /* Signals may be degraded, lost or spoofed */
            @ExternalElement;
        }
        part <'EXT-WEATHER'> weather : Weather {
            doc /* Wind and precipitation limits TBD */
            @ExternalElement;
        }
        part <'SUS-I1'> system : IntegratedSystem {
            part <'SUS-M1'> walker : Walker {
                @ItemElement { kind = ElementKind::system; safetyRole = SafetyRole::none; status = ElementStatus::concept; }
                part <'SUS-M1-PIL'> pilotStation : PilotStation {
                    @ItemElement { kind = ElementKind::humanInterface; safetyRole = SafetyRole::none; status = ElementStatus::concept; }
                    perform pilotedLocomotion;
                    perform pilotReadinessIngressAndEgress;
                }
                part <'SUS-M1-CTL'> motionControl : MotionControl {
                    @ItemElement { kind = ElementKind::computing; safetyRole = SafetyRole::none; status = ElementStatus::concept; }
                    perform pilotedLocomotion;
                    perform payloadManipulation;
                    perform protectiveStopAndFaultResponse;
                }
                part <'SUS-M1-WLK'> legs : LegsAndChassis {
                    @ItemElement { kind = ElementKind::mechanical; safetyRole = SafetyRole::none; status = ElementStatus::concept; }
                    perform pilotedLocomotion;
                }
                part <'SUS-M1-MAN'> manipulators : Manipulators {
                    @ItemElement { kind = ElementKind::mechanical; safetyRole = SafetyRole::none; status = ElementStatus::concept; }
                    perform payloadManipulation;
                }
                part <'SUS-M1-SAF'> safetyMonitor : SafetyMonitor {
                    @ItemElement { kind = ElementKind::computing; safetyRole = SafetyRole::protective; status = ElementStatus::concept; }
                    perform pilotReadinessIngressAndEgress;
                    perform protectiveStopAndFaultResponse;
                    perform powerGenerationStorageDistributionAndIsolation;
                }
                part <'SUS-M1-DCK'> dock : UavDock {
                    @ItemElement { kind = ElementKind::mixed; safetyRole = SafetyRole::protective; status = ElementStatus::concept; }
                    perform uavLaunchRecoveryAndRetention;
                    perform uavCharging;
                }
                part <'SUS-M1-PWR'> power : PowerSystem {
                    @ItemElement { kind = ElementKind::electrical; safetyRole = SafetyRole::none; status = ElementStatus::concept; }
                    perform powerGenerationStorageDistributionAndIsolation;
                    perform maintenanceSupportAndEnergyIsolation;
                    part <'SUS-M1-PWR-GEN'> engineGenerator : EngineGenerator {
                        @ItemElement { kind = ElementKind::mechanical; safetyRole = SafetyRole::none; status = ElementStatus::candidate; decision = "DQ-006"; }
                    }
                    part <'SUS-M1-PWR-BAT'> battery : BatteryPack {
                        @ItemElement { kind = ElementKind::electrical; safetyRole = SafetyRole::none; status = ElementStatus::candidate; decision = "DQ-006"; }
                    }
                    part <'SUS-M1-PWR-DIST'> distribution : PowerDistribution {
                        @ItemElement { kind = ElementKind::electrical; safetyRole = SafetyRole::none; status = ElementStatus::candidate; decision = "DQ-006"; }
                    }
                }
            }
            part <'SUS-A1'> uav : ObservationUav {
                @ItemElement { kind = ElementKind::system; safetyRole = SafetyRole::none; status = ElementStatus::concept; }
                part <'SUS-A1-FC'> flightController : FlightController {
                    @ItemElement { kind = ElementKind::computing; safetyRole = SafetyRole::none; status = ElementStatus::concept; }
                    perform aerialObservation;
                    perform uavLaunchRecoveryAndRetention;
                }
                part <'SUS-A1-NAV'> navigation : NavigationAndTelemetry {
                    @ItemElement { kind = ElementKind::electrical; safetyRole = SafetyRole::none; status = ElementStatus::concept; }
                    perform aerialObservation;
                }
                part <'SUS-A1-PWR'> uavPower : UavPower {
                    @ItemElement { kind = ElementKind::electrical; safetyRole = SafetyRole::none; status = ElementStatus::concept; }
                    perform uavCharging;
                }
                part <'SUS-A1-PROP'> propulsion : Propulsion {
                    @ItemElement { kind = ElementKind::mechanical; safetyRole = SafetyRole::none; status = ElementStatus::concept; }
                    perform aerialObservation;
                }
            }
            part <'SUS-I1-INT'> integrationManager : IntegrationManager {
                @ItemElement { kind = ElementKind::computing; safetyRole = SafetyRole::none; status = ElementStatus::concept; }
                perform uavLaunchRecoveryAndRetention;
            }
            part <'SUS-GSE'> groundSupport : GroundSupport {
                @ItemElement { kind = ElementKind::mixed; safetyRole = SafetyRole::none; status = ElementStatus::concept; }
                perform maintenanceSupportAndEnergyIsolation;
            }
        }

        connection <'IF-001'> pilotControlsAndDisplays : Exchange connect pilot to system.walker.pilotStation {
            doc /* Pilot controls and displays */
            @InterfaceSpec { direction = Direction::bi; kinds = ("human", "data"); exchange = "commands, state, warnings"; hazards = ("HAZ-PIL-001"); }
        }
        connection <'IF-002'> engineGeneratorToDistribution : Exchange connect system.walker.power.engineGenerator to system.walker.power.distribution {
            doc /* Engine-generator to distribution */
            @InterfaceSpec { direction = Direction::uni; kinds = ("energy"); exchange = "electric power, voltage, thermal state"; status = ElementStatus::candidate; decision = "DQ-006"; }
        }
        connection <'IF-003'> batteryToDistribution : Exchange connect system.walker.power.battery to system.walker.power.distribution {
            doc /* Battery to distribution */
            @InterfaceSpec { direction = Direction::bi; kinds = ("energy", "data"); exchange = "bidirectional power, BMS state"; status = ElementStatus::candidate; decision = "DQ-006"; }
        }
        connection <'IF-004'> controlToJointActuators : Exchange connect system.walker.motionControl to system.walker.legs {
            doc /* Control to joint actuators */
            @InterfaceSpec { direction = Direction::bi; kinds = ("data", "energy"); exchange = "torque or pressure commands, joint feedback"; hazards = ("HAZ-WLK-001", "HAZ-WLK-002", "HAZ-PIL-002"); }
        }
        connection <'IF-005'> safetyMonitorToPower : Exchange connect system.walker.safetyMonitor to system.walker.power {
            doc /* Safety monitor to power */
            @InterfaceSpec { direction = Direction::uni; kinds = ("data", "energy"); exchange = "inhibit, isolation"; hazards = ("HAZ-SAF-001", "HAZ-PIL-002"); }
        }
        connection <'IF-006'> walkerDockToUav : Exchange connect system.walker.dock to system.uav {
            doc /* Walker dock to UAV */
            @InterfaceSpec { direction = Direction::bi; kinds = ("mechanical", "energy", "data"); exchange = "retention, charging, data, release"; hazards = ("HAZ-DCK-001", "HAZ-DCK-002"); }
        }
        connection <'IF-007'> uavInAirspace : Exchange connect system.uav to airspace {
            doc /* UAV in airspace */
            @InterfaceSpec { direction = Direction::bi; kinds = ("environment"); exchange = "flight, exposure of people and property"; hazards = ("HAZ-INT-001"); }
        }
        connection <'IF-008'> maintainerToEnergySources : Exchange connect groundCrew to system.walker.power {
            doc /* Maintainer to energy sources */
            @InterfaceSpec { direction = Direction::bi; kinds = ("human", "energy"); exchange = "lockout, isolation, inspection, service"; hazards = ("HAZ-PWR-001"); }
        }
        connection <'IF-PX4-001'> flightStatePositionAndStatus : Exchange connect system.uav.flightController to system.integrationManager {
            doc /* Flight state, position and status */
            @InterfaceSpec { direction = Direction::uni; kinds = ("data"); exchange = "flight state, position, status; freshness and source validity"; hazards = ("HAZ-INT-001"); }
        }
        connection <'IF-PX4-002'> uavHealthAndArmingState : Exchange connect system.uav.flightController to system.integrationManager {
            doc /* UAV health and arming state */
            @InterfaceSpec { direction = Direction::uni; kinds = ("data"); exchange = "health, arming state; disagreement handling"; hazards = ("HAZ-DCK-001"); }
        }
        connection <'IF-PX4-003'> dockOccupiedAndRetained : Exchange connect system.walker.dock to system.integrationManager {
            doc /* Dock occupied and retained */
            @InterfaceSpec { direction = Direction::uni; kinds = ("data"); exchange = "occupied/retained state with independent plausibility"; hazards = ("HAZ-DCK-002"); }
        }
        connection <'IF-PX4-004'> walkerPostureAndStationaryState : Exchange connect system.walker.motionControl to system.integrationManager {
            doc /* Walker posture and stationary state */
            @InterfaceSpec { direction = Direction::uni; kinds = ("data"); exchange = "posture, stationary flag for the launch/recovery envelope"; hazards = ("HAZ-INT-001"); }
        }
        connection <'IF-PX4-005'> launchPermitAndRevoke : Exchange connect system.integrationManager to system.uav.flightController {
            doc /* Launch permit and revoke */
            @InterfaceSpec { direction = Direction::uni; kinds = ("data"); exchange = "explicit, fail-closed launch authorization"; hazards = ("HAZ-INT-001"); }
        }
        connection <'IF-PX4-006'> recoveryAndAbortIntent : Exchange connect system.integrationManager to system.uav.flightController {
            doc /* Recovery and abort intent */
            @InterfaceSpec { direction = Direction::uni; kinds = ("data"); exchange = "recovery request, abort; contingency on lost link"; hazards = ("HAZ-INT-001"); }
        }
        connection <'IF-PX4-007'> uavVideoAndMissionCues : Exchange connect system.uav.navigation to system.walker.pilotStation {
            doc /* UAV video and mission cues */
            @InterfaceSpec { direction = Direction::uni; kinds = ("data"); exchange = "video, mission cues; latency, distraction"; }
        }
        connection <'IF-PX4-008'> faultAndContingencyNotification : Exchange connect system.integrationManager to system.uav.flightController {
            doc /* Fault and contingency notification */
            @InterfaceSpec { direction = Direction::bi; kinds = ("data"); exchange = "time-stamped, prioritised fault notifications"; hazards = ("HAZ-INT-001"); }
        }
        connection <'IF-PX4-009'> powerAndChargingHandshake : Exchange connect system.walker.dock to system.uav.uavPower {
            doc /* Power and charging handshake */
            @InterfaceSpec { direction = Direction::bi; kinds = ("energy", "data"); exchange = "charging handshake, rotor inhibit, energy isolation"; hazards = ("HAZ-DCK-001"); }
        }
        connection <'IF-010'> walkerOnTerrain : Exchange connect system.walker.legs to terrain {
            doc /* Walker on terrain */
            @InterfaceSpec { direction = Direction::bi; kinds = ("mechanical", "environment"); exchange = "contact loads, terrain sensing"; hazards = ("HAZ-WLK-002"); }
        }
        connection <'IF-011'> observerStop : Exchange connect safetyObserver to system.walker.safetyMonitor {
            doc /* Observer stop */
            @InterfaceSpec { direction = Direction::uni; kinds = ("human", "data"); exchange = "independent stop request"; hazards = ("HAZ-SAF-001"); }
        }
        connection <'IF-012'> walkerMotionNearPeople : Exchange connect system.walker.legs to bystanders {
            doc /* Walker motion near people */
            @InterfaceSpec { direction = Direction::uni; kinds = ("mechanical", "environment"); exchange = "moving structure, exclusion zone"; hazards = ("HAZ-WLK-002", "HAZ-SAF-001"); }
        }
        connection <'IF-013'> navigationAndTelemetryLink : Exchange connect system.uav.navigation to gnssRf {
            doc /* Navigation and telemetry link */
            @InterfaceSpec { direction = Direction::bi; kinds = ("data", "environment"); exchange = "GNSS, telemetry, RF link"; hazards = ("HAZ-INT-001"); }
        }
        connection <'IF-014'> weatherOnTheUav : Exchange connect weather to system.uav {
            doc /* Weather on the UAV */
            @InterfaceSpec { direction = Direction::uni; kinds = ("environment"); exchange = "wind, precipitation, temperature"; hazards = ("HAZ-INT-001"); }
        }
        connection <'IF-015'> pilotStopRequest : Exchange connect pilot to system.walker.safetyMonitor {
            doc /* Pilot stop request */
            @InterfaceSpec { direction = Direction::uni; kinds = ("human", "data"); exchange = "protective stop request"; hazards = ("HAZ-SAF-001"); }
        }
        connection <'IF-016'> torqueInhibitAndBrakes : Exchange connect system.walker.safetyMonitor to system.walker.legs {
            doc /* Torque inhibit and brakes */
            @InterfaceSpec { direction = Direction::uni; kinds = ("data", "energy"); exchange = "torque inhibit, brakes, load holding"; hazards = ("HAZ-SAF-001", "HAZ-WLK-001"); }
        }
        connection <'IF-017'> pilotMotionRequest : Exchange connect system.walker.pilotStation to system.walker.motionControl {
            doc /* Pilot motion request */
            @InterfaceSpec { direction = Direction::uni; kinds = ("data"); exchange = "requested motion, mode"; hazards = ("HAZ-PIL-001"); }
        }
        connection <'IF-018'> armCommands : Exchange connect system.walker.motionControl to system.walker.manipulators {
            doc /* Arm commands */
            @InterfaceSpec { direction = Direction::bi; kinds = ("data", "energy"); exchange = "arm commands, load feedback"; }
        }
        connection <'IF-019'> groundSupportToWalker : Exchange connect system.groundSupport to system.walker {
            doc /* Ground support to walker */
            @InterfaceSpec { direction = Direction::bi; kinds = ("mechanical", "energy"); exchange = "maintenance supports, external charging, test connections"; hazards = ("HAZ-PWR-001"); }
        }
        connection <'IF-020'> launchAndRecoveryAuthorization : Exchange connect system.walker.pilotStation to system.integrationManager {
            doc /* Launch and recovery authorization */
            @InterfaceSpec { direction = Direction::bi; kinds = ("human", "data"); exchange = "operator launch/recovery request and authorization, status"; hazards = ("HAZ-INT-001"); }
        }
        connection <'IF-021'> motorCommands : Exchange connect system.uav.flightController to system.uav.propulsion {
            doc /* Motor commands */
            @InterfaceSpec { direction = Direction::uni; kinds = ("data", "energy"); exchange = "motor commands"; hazards = ("HAZ-DCK-001"); }
        }
        connection <'IF-022'> safetySensing : Exchange connect system.walker.legs to system.walker.safetyMonitor {
            doc /* Safety sensing */
            @InterfaceSpec { direction = Direction::uni; kinds = ("data"); exchange = "posture, joint and pressure sensing for the monitor"; hazards = ("HAZ-WLK-001"); }
        }
    }
}
