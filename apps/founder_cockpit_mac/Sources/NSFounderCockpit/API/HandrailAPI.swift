import Foundation

struct HandrailAPI {
    static func contradictions() async throws -> ContradictionsResponse {
        try await APIClient.shared.get(RuntimeConfig.nsCoreBase + "/contradictions")
    }

    static func contradictionGraph() async throws -> ContradictionGraph {
        try await APIClient.shared.get(RuntimeConfig.nsCoreBase + "/contradictions/graph")
    }

    static func ledgerHealth() async throws -> LedgerHealth {
        try await APIClient.shared.get(RuntimeConfig.ncomBase + "/ncom/panels/ledger_health")
    }

    static func readinessScore() async throws -> ReadinessPanel {
        try await APIClient.shared.get(RuntimeConfig.ncomBase + "/ncom/panels/readiness_score")
    }
}
