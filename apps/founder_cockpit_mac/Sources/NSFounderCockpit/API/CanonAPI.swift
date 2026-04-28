import Foundation

struct CanonAPI {
    static func list() async throws -> CanonListResponse {
        try await APIClient.shared.get(RuntimeConfig.nsCoreBase + "/canon")
    }

    static func promote(proposalId: String, reason: String = "founder_promote",
                        yubikeyReceipt: String? = nil) async throws -> CanonPromoteResponse {
        try await APIClient.shared.post(
            RuntimeConfig.nsCoreBase + "/canon/promote",
            body: CanonPromoteRequest(proposal_id: proposalId, reason: reason,
                                      yubikey_receipt: yubikeyReceipt)
        )
    }
}
