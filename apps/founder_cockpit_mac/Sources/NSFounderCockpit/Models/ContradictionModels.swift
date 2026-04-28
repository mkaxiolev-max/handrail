import Foundation

struct ContradictionItem: Identifiable, Decodable {
    let branch_id: String
    let claim: String
    let contradicts: [String]
    var id: String { branch_id }
}

struct ContradictionsResponse: Decodable {
    let count: Int
    let items: [ContradictionItem]
    let pressure_score: Double
}

struct GraphNode: Identifiable, Decodable {
    let id: String
    let label: String
}

struct GraphEdge: Decodable {
    let from: String
    let to: String
}

struct ContradictionGraph: Decodable {
    let nodes: [GraphNode]
    let edges: [GraphEdge]
}
