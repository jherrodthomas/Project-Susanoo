// SusanooSafety — SysML v2 vocabulary for MIL-STD-882E work products.
// Category names follow MIL-STD-882E terminology; definitions, thresholds and
// the risk matrix must be confirmed against the controlled standard and the
// approved SSPP before formal use. This is not a compliance claim.
// The ARP4761A failure-condition scale is deliberately NOT modelled here
// (separate schema namespace — see framework/traceability.md rule 7).

package SusanooSafety {
    private import ScalarValues::*;
    private import SusanooSystem::*;

    // ------------------------------------------------- risk classification
    enum def SeverityCategory {
        enum Catastrophic;   // 1
        enum Critical;       // 2
        enum Marginal;       // 3
        enum Negligible;     // 4
    }
    enum def ProbabilityLevel {
        enum Frequent;       // A
        enum Probable;       // B
        enum Occasional;     // C
        enum Remote;         // D
        enum Improbable;     // E
        enum Eliminated;     // F
    }
    enum def RiskLevel {
        enum High;
        enum Serious;
        enum Medium;
        enum Low;
        enum Eliminated;
    }
    enum def SoftwareControlCategory {
        enum Autonomous;            // SwCI 1 (AT)
        enum SemiAutonomous;        // SwCI 2 (SAT)
        enum RedundantFaultTolerant;// SwCI 3 (RFT)
        enum Influential;           // SwCI 4 (IN)
        enum NoSafetyImpact;        // SwCI 5 (NSI)
    }
    enum def MitigationPrecedence {
        enum EliminateByDesign;
        enum ReduceByDesignAlteration;
        enum EngineeredFeatures;
        enum WarningDevices;
        enum SignageProceduresTrainingPPE;
    }
    enum def HazardStatus {
        enum Open;
        enum Monitor;
        enum Mitigated;
        enum Verified;
        enum PendingAcceptance;
        enum Accepted;
        enum Closed;
    }

    attribute def RiskAssessment {
        attribute severity : SeverityCategory;
        attribute probability : ProbabilityLevel;
        attribute level : RiskLevel;
        attribute rationale : String;
    }

    // ------------------------------------------------------ core items
    item def SafetyRequirement {
        attribute id : String;
        attribute text : String;
        attribute verificationMethod : String;
    }
    item def Mitigation {
        attribute id : String;
        attribute description : String;
        attribute precedence : MitigationPrecedence;
        ref item requirement : SafetyRequirement[0..*];
    }
    item def VerificationEvidence {
        attribute id : String;
        attribute provenance : String;
        attribute integrityHash : String;
        attribute simulated : Boolean;
    }
    item def RiskAcceptanceDecision {
        attribute decisionRecord : String;
        attribute authority : String;
        attribute acceptedLevel : RiskLevel;
        attribute realApproval : Boolean;
    }
    item def Hazard {
        doc /* Mirrors safety/mil-std-882e/templates/hazard-record.yaml. */
        attribute id : String;
        attribute status : HazardStatus;
        attribute configurationId : String;
        attribute hazardousCondition : String;
        attribute causes : String[0..*];
        attribute consequences : String[0..*];
        attribute initialRisk : RiskAssessment;
        attribute residualRisk : RiskAssessment;
        ref item mitigations : Mitigation[0..*];
        ref item evidence : VerificationEvidence[0..*];
        ref item acceptance : RiskAcceptanceDecision[0..1];
        attribute subsystemIds : String[0..*];   // short names from SusanooSystem
    }
}
