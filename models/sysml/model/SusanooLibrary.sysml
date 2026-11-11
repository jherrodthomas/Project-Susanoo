// Susanoo SysML v2 library: the vocabulary the model uses. Hand-written.
// Types follow MIL-STD-882E (11 May 2012) and the item-definition record (architecture/item-definition.yaml).
// Checked by tools/sysml/check.py and by the OMG pilot implementation (tools/sysml/pilot/validate.sh).
package SusanooLibrary {
    private import ScalarValues::*;

    doc /* Shared definitions for the SUS-I1 model: element metadata, interfaces, and the
         * MIL-STD-882E risk and software-criticality vocabulary. */

    // ------------------------------------------------------------ item definition
    enum def ElementKind {
        enum system;
        enum mechanical;
        enum electrical;
        enum computing;
        enum humanInterface;
        enum mixed;
    }
    enum def SafetyRole {
        doc /* protective: the element implements a protective function (safety monitor, interlock, retention). */
        enum protective;
        enum none;
    }
    enum def ElementStatus {
        doc /* candidate: depends on an open decision in decisions/register.yaml. */
        enum concept;
        enum candidate;
        enum baselined;
    }
    metadata def ItemElement {
        doc /* An element inside the SUS-I1 boundary (item-definition elements). */
        attribute kind : ElementKind;
        attribute safetyRole : SafetyRole;
        attribute status : ElementStatus;
        attribute decision : String[0..1];
    }
    metadata def ExternalElement {
        doc /* An element outside the SUS-I1 boundary; its doc states the assumption made about it. */
    }

    enum def Direction {
        doc /* uni: from the first connection end to the second; bi: both ways. */
        enum uni;
        enum bi;
    }
    metadata def InterfaceSpec {
        doc /* Item-definition interface: direction, exchange kinds (data, energy, mechanical, human,
             * environment), the exchange and the hazards it carries. */
        attribute direction : Direction;
        attribute kinds : String[1..*];
        attribute exchange : String;
        attribute hazards : String[0..*];
        attribute status : ElementStatus[0..1];
        attribute decision : String[0..1];
    }
    connection def Exchange {
        doc /* Any exchange across an interface between two parts. */
        end part a;
        end part b;
    }

    // ------------------------------------------------------------ requirements and traceability
    metadata def Source {
        doc /* The record a generated model element was copied from. */
        attribute record : String;
    }
    metadata def HazardRef {
        doc /* MIL-STD-882E hazards (safety/hazards/HAZ-*.yaml) a requirement mitigates. */
        attribute ids : String[1..*];
    }
    requirement def SystemRequirement {
        doc /* A system requirement from requirements/SYS-*.yaml. */
    }

    // ------------------------------------------------------------ MIL-STD-882E vocabulary
    enum def RiskLevel {
        doc /* Table III risk levels. */
        enum High;
        enum Serious;
        enum Medium;
        enum Low;
        enum Eliminated;
    }
    enum def SoftwareControlCategory {
        doc /* Table IV software control categories. */
        enum autonomous;
        enum semiAutonomous;
        enum redundantFaultTolerant;
        enum influential;
        enum noSafetyImpact;
    }
}
