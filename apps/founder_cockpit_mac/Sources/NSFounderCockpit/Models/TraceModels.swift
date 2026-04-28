import Foundation

struct EtherTrace: Decodable {
    let recent_branch_count: Int
    let branch_ids: [String]
    let substrate: String
    let note: String
}

struct NCOMPanel: Decodable {
    let panel: String?
    let count: Int?
    let ts: String?
}

struct LedgerHealth: Decodable {
    let all_chains_valid: Bool?
    let tables: [String: TableHealth]?
}

struct TableHealth: Decodable {
    let count: Int?
    let chain_valid: Bool?
}

struct ReadinessPanel: Decodable {
    let panel: String?
    let latest: ReadinessLatest?
    let ts: String?
}

struct ReadinessLatest: Decodable {
    let branch_id: String?
    let score_100: Double?
    let sub_metrics: [String: Double]?
    let ts: String?
}

struct ReceiptModels {}
