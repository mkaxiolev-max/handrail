import Foundation

struct CockpitScore {
    struct Dimension: Identifiable {
        let id: String
        let label: String
        let score: Double    // 0–10
        let max: Double = 10.0
        let note: String
    }

    let dimensions: [Dimension]

    var total: Double {
        dimensions.reduce(0) { $0 + $1.score }
    }

    var outOf: Double {
        dimensions.reduce(0) { $0 + $1.max }
    }

    var score100: Double {
        guard outOf > 0 else { return 0 }
        return (total / outOf) * 100.0
    }

    var grade: String {
        switch score100 {
        case 95...:  return "S"
        case 85...:  return "A"
        case 70...:  return "B"
        case 55...:  return "C"
        default:     return "F"
        }
    }
}
