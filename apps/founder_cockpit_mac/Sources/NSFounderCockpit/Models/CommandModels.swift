import Foundation

struct QueryRequest: Encodable {
    let prompt: String
}

struct QueryResponse: Decodable {
    let answer: String
    let confidence: Double
    let verb: String
    let branch_id: String?
    let proposal_id: String?
    let score_100: Double
    let invariants_passed: [String]?
    let imo_receipt: String?
    let trace: QueryTrace?
}

struct QueryTrace: Decodable {
    let router: RouterInfo?
    let canon_alignment: String?
    let next_actions: [String]?
}

struct RouterInfo: Decodable {
    let engine: String
    let verb: String
}

struct RouterDecisionResponse: Decodable {
    let engine: String
    let version: String
    let available_verbs: [String]
}
