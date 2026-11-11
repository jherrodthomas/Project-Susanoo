// SusanooSystem — SysML v2 textual model of the SUS-I1 system breakdown.
// Status: concept baseline (SUS-I1-C001, planned). Proposed allocations only;
// no component, safety integrity or interface has been selected or verified.
// Short names <'...'> match the element IDs used in safety/mil-std-882e/catalog.yaml.

package SusanooSystem {
    private import ScalarValues::*;

    doc /* System breakdown used as the analysis baseline for every
         * MIL-STD-882E work-product folder under safety/mil-std-882e. */

    // ---------------------------------------------------------------- ports
    port def DockPort {
        doc /* Combined mechanical retention, protected power and data/command
             * interface between the SUS-M1 dock and SUS-A1. */
    }
    port def InhibitPort {
        doc /* Independent protective-stop / torque-inhibit signal path. */
    }
    port def PowerPort {
        doc /* Protected DC power branch. */
    }
    port def CommandPort {
        doc /* Pilot intent and motion command data. */
    }

    interface def DockInterface {
        doc /* SUS-M1 to SUS-A1 docking interface: retention, charging, data,
             * rotor inhibit while retained. */
        end walkerSide : DockPort;
        end uavSide : ~DockPort;
    }

    // ------------------------------------------------------- SUS-M1 walker
    part def <'SUS-M1-WLK'> WalkerStructure {
        doc /* Chassis, legs, feet, joint actuators and brakes, stability sensing. */
        port power : ~PowerPort;
    }
    part def <'SUS-M1-MAN'> Manipulators {
        doc /* Two manipulation arms, end effectors and payload sensing. */
        port power : ~PowerPort;
    }
    part def <'SUS-M1-PIL'> PilotStation {
        doc /* Protected operator station, restraints, displays, controls, ingress/egress. */
        port commands : CommandPort;
    }
    part def <'SUS-M1-PWR'> PowerSystem {
        doc /* Candidate series hybrid: engine-generator, battery + BMS, protected DC
             * distribution, energy isolation, thermal and fire protection. */
        port mainBus : PowerPort;
        port isolate : ~InhibitPort;
    }
    part def <'SUS-M1-CTL'> MotionControl {
        doc /* Mission/motion controller, balance control and joint drives (software intensive). */
        port commands : ~CommandPort;
        port inhibitIn : ~InhibitPort;
    }
    part def <'SUS-M1-SAF'> SafetyMonitor {
        doc /* Independent safety monitor and protective-stop function (proposed allocation). */
        port torqueInhibit : InhibitPort;
        port powerIsolate : InhibitPort;
    }
    part def <'SUS-M1-DCK'> UAVDock {
        doc /* UAV mechanical retention, latch sensing, protected charging and data gateway. */
        port dockPort : DockPort;
    }

    part def <'SUS-M1'> PilotedWalker {
        doc /* Human-piloted mechanized walker. */
        part wlk : WalkerStructure;
        part man : Manipulators;
        part pil : PilotStation;
        part pwr : PowerSystem;
        part ctl : MotionControl;
        part saf : SafetyMonitor;
        part dck : UAVDock;

        connect pil.commands to ctl.commands;
        connect saf.torqueInhibit to ctl.inhibitIn;
        connect saf.powerIsolate to pwr.isolate;
        connect pwr.mainBus to wlk.power;
        connect pwr.mainBus to man.power;
    }

    // --------------------------------------------------------- SUS-A1 UAV
    part def <'SUS-A1-FCS'> FlightControl {
        doc /* Flight controller; PX4 is a candidate, see integrations/px4. */
    }
    part def <'SUS-A1-PRP'> Propulsion {
        doc /* Motors, ESCs and propellers. */
    }
    part def <'SUS-A1-PWR'> UAVPower {
        doc /* UAV battery and power management. */
    }
    part def <'SUS-A1-NAV'> NavTelemetry {
        doc /* Navigation sensors, GNSS receiver and telemetry link. */
    }
    part def <'SUS-A1-PLD'> ObservationPayload {
        doc /* Unarmed observation sensors (camera / imaging). */
    }

    part def <'SUS-A1'> ObservationUAV {
        doc /* Dockable, unarmed observation UAV. */
        part fcs : FlightControl;
        part prp : Propulsion;
        part pwr : UAVPower;
        part nav : NavTelemetry;
        part pld : ObservationPayload;
        port dockPort : ~DockPort;
    }

    // ------------------------------------------------ ground support (GSE)
    part def <'SUS-GSE-SUP'> MaintenanceSupports {
        doc /* Mechanical supports, stands and lockout provisions. */
    }
    part def <'SUS-GSE-CHG'> ChargingEquipment {
        doc /* Shore charging and fuelling equipment. */
    }
    part def <'SUS-GSE-TST'> TestRigs {
        doc /* Supported joint rigs, HIL benches and simulation. */
    }
    part def <'SUS-GSE'> GroundSupport {
        part sup : MaintenanceSupports;
        part chg : ChargingEquipment;
        part tst : TestRigs;
    }

    // ---------------------------------------------------- integrated system
    part def <'SUS-I1'> IntegratedSystem {
        doc /* Integrated mech-and-UAV demonstrator; system of interest for 882E analyses. */
        part m1 : PilotedWalker;
        part a1 : ObservationUAV;
        part gse : GroundSupport;

        interface dock : DockInterface
            connect walkerSide ::> m1.dck.dockPort to uavSide ::> a1.dockPort;
    }

    // --------------------------------------------------- external context
    part def <'EXT-PILOT'> Pilot;
    part def <'EXT-CREW'> GroundCrew;
    part def <'EXT-BYST'> Bystanders;
    part def <'EXT-TERRAIN'> TerrainAndObstacles;
    part def <'EXT-AIR'> AirspaceGnssRf;
    part def <'EXT-SITE'> SiteInfrastructure;
    part def <'EXT-ENV'> NaturalEnvironment;
    part def <'EXT-AUTH'> RiskAcceptanceAuthority;

    // Configuration usage referenced by satisfy/verify relations in the
    // generated per-folder views (e.g. susanoo.m1.saf).
    part susanoo : IntegratedSystem;
}
