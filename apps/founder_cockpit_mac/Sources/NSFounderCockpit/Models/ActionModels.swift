import Foundation

struct CPSPlan: Encodable {
    let ops: [CPSOp]
}

struct CPSOp: Encodable {
    let id: String
    let domain: String
    let op: String
    let args: [String: String]
}

struct CPSResult: Decodable {
    let plan_id: String?
    let results: [CPSOpResult]?
    let status: String?
    let error: String?
}

struct CPSOpResult: Decodable {
    let op_id: String?
    let status: String?
    let output: AnyCodable?
    let error: String?
}

struct AnyCodable: Decodable {
    let value: Any
    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let s = try? container.decode(String.self) { value = s }
        else if let i = try? container.decode(Int.self) { value = i }
        else if let d = try? container.decode(Double.self) { value = d }
        else if let b = try? container.decode(Bool.self) { value = b }
        else { value = "?" }
    }
}

struct ReceiptEntry: Identifiable, Decodable {
    let id: String
    let op: String
    let ts: String
    let ref_id: String?
}
