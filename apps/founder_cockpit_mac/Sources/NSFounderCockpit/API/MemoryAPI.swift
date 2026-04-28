import Foundation

struct MemoryAPI {
    static func atoms() async throws -> MemoryAtomsResponse {
        try await APIClient.shared.get(RuntimeConfig.nsCoreBase + "/memory/atoms")
    }

    static func molecules() async throws -> MemoryMoleculesResponse {
        try await APIClient.shared.get(RuntimeConfig.nsCoreBase + "/memory/molecules")
    }

    static func etherTrace() async throws -> EtherTrace {
        try await APIClient.shared.get(RuntimeConfig.nsCoreBase + "/ether/retrieval_trace")
    }
}
