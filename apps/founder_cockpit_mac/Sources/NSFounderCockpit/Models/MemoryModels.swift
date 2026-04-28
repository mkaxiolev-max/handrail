import Foundation

struct MemoryAtom: Identifiable, Decodable {
    let id: String
    let claim: String
    let amp: Double
    let ts: String?
}

struct MemoryAtomsResponse: Decodable {
    let count: Int
    let atoms: [MemoryAtom]
}

struct MemoryMolecule: Identifiable, Decodable {
    let members: [String]
    let claims: [String]
    var id: String { members.joined(separator: "|") }
}

struct MemoryMoleculesResponse: Decodable {
    let count: Int
    let molecules: [MemoryMolecule]
}
