import Foundation

struct CanonRecord: Identifiable, Decodable {
    let branch_id: String
    let claim: String
    let verb: String
    let imo_receipt: String?
    let invariants_passed: [String]?
    var id: String { branch_id }
}

struct CanonListResponse: Decodable {
    let count: Int
    let records: [CanonRecord]
}

struct CanonPromoteRequest: Encodable {
    let proposal_id: String
    let reason: String
    let yubikey_receipt: String?
}

struct CanonPromoteResponse: Decodable {
    let ok: Bool
    let proposal_id: String?
    let reason: String?
    let note: String?
    let error: String?
}
