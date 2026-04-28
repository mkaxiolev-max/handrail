import Foundation

struct RISAPI {
    static func sources() async throws -> RISSourcesResponse {
        try await APIClient.shared.get(RuntimeConfig.risBase + "/ris/sources")
    }
}
