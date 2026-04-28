import Foundation

struct StorytimeResponse: Decodable {
    let what_happened: [String]
    let what_is_uncertain: [String]
    let what_changed: [String]
    let rule: String
}
