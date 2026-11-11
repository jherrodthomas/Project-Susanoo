// Susanoo functions (item-definition functions F-nn). Hand-written; checked against
// architecture/item-definition.yaml by tools/sysml/check.py (rule M9).
package SusanooFunctions {
    private import SusanooLibrary::*;

    action def PilotedLocomotion { doc /* Piloted locomotion */ }
    action def PayloadManipulation { doc /* Payload manipulation */ }
    action def PilotReadinessIngressAndEgress { doc /* Pilot readiness, ingress and egress */ }
    action def ProtectiveStopAndFaultResponse { doc /* Protective stop and fault response */ }
    action def PowerGenerationStorageDistributionAndIsolation { doc /* Power generation, storage, distribution and isolation */ }
    action def AerialObservation { doc /* Aerial observation */ }
    action def UavLaunchRecoveryAndRetention { doc /* UAV launch, recovery and retention */ }
    action def UavCharging { doc /* UAV charging */ }
    action def MaintenanceSupportAndEnergyIsolation { doc /* Maintenance support and energy isolation */ }

    action <'F-01'> pilotedLocomotion : PilotedLocomotion;
    action <'F-02'> payloadManipulation : PayloadManipulation;
    action <'F-03'> pilotReadinessIngressAndEgress : PilotReadinessIngressAndEgress;
    action <'F-04'> protectiveStopAndFaultResponse : ProtectiveStopAndFaultResponse;
    action <'F-05'> powerGenerationStorageDistributionAndIsolation : PowerGenerationStorageDistributionAndIsolation;
    action <'F-06'> aerialObservation : AerialObservation;
    action <'F-07'> uavLaunchRecoveryAndRetention : UavLaunchRecoveryAndRetention;
    action <'F-08'> uavCharging : UavCharging;
    action <'F-09'> maintenanceSupportAndEnergyIsolation : MaintenanceSupportAndEnergyIsolation;
}
