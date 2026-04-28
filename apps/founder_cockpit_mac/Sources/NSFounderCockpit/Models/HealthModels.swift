import Foundation

struct ServiceHealth: Identifiable, Decodable {
    let id: String
    let label: String
    var isUp: Bool
    var latencyMs: Double
    var raw: String
}

struct SystemStateResponse: Decodable {
    let ns_core: String
    let coherence_kernel: String
    let imo_gate: String
    let ts: String
}

struct ContinuumStatus: Decodable {
    let tier: Int?
    let status: String?
    let event_count: Int?
}
