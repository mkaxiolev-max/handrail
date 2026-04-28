import Foundation

struct StorytimeAPI {
    static func fetch() async throws -> StorytimeResponse {
        try await APIClient.shared.get(RuntimeConfig.nsCoreBase + "/storytime")
    }
}
