import Foundation

struct RISLane: Identifiable, Decodable {
    let id: String
    let status: String?
    let last_run: String?
    let rows: Int?
}

struct RISSourcesResponse: Decodable {
    let lanes: [String: RISSingleLane]?
}

struct RISSingleLane: Decodable {
    let status: String?
    let last_ingest: String?
    let record_count: Int?
}
