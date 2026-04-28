import Foundation

struct CommandAPI {
    static func query(prompt: String) async throws -> QueryResponse {
        try await APIClient.shared.post(
            RuntimeConfig.nsCoreBase + "/query",
            body: QueryRequest(prompt: prompt)
        )
    }

    static func routerDecision() async throws -> RouterDecisionResponse {
        try await APIClient.shared.get(RuntimeConfig.nsCoreBase + "/router/decision")
    }

    static func systemState() async throws -> SystemStateResponse {
        try await APIClient.shared.get(RuntimeConfig.nsCoreBase + "/system/state")
    }
}
