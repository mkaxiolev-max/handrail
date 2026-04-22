import Foundation
import Combine

// Score delta tracking — keeps a rolling window of score samples + computes trend
final class ScoreHistory: ObservableObject {
    static let shared = ScoreHistory()

    struct Sample: Identifiable {
        let id = UUID()
        let score: Double
        let ts: Date
    }

    @Published var samples: [Sample] = []
    @Published var trend: Trend = .stable

    enum Trend: String {
        case rising  = "↑"
        case falling = "↓"
        case stable  = "→"

        var color: String {   // used in SwiftUI via DSColors lookup
            switch self {
            case .rising:  return "online"
            case .falling: return "offline"
            case .stable:  return "textSecondary"
            }
        }
    }

    private let windowSize = 20
    private init() {}

    func record(_ score: Double) {
        guard score > 0 else { return }
        let sample = Sample(score: score, ts: Date())
        samples.append(sample)
        if samples.count > windowSize { samples.removeFirst(samples.count - windowSize) }
        recomputeTrend()
    }

    private func recomputeTrend() {
        guard samples.count >= 3 else { return }
        let recent  = samples.suffix(3).map(\.score)
        let earlier = samples.prefix(3).map(\.score)
        let recentAvg  = recent.reduce(0, +) / Double(recent.count)
        let earlierAvg = earlier.reduce(0, +) / Double(earlier.count)
        let delta = recentAvg - earlierAvg
        if delta > 0.05 {
            trend = .rising
        } else if delta < -0.05 {
            trend = .falling
        } else {
            trend = .stable
        }
    }

    var sparklinePoints: [Double] {
        samples.map(\.score)
    }

    var latestDelta: Double {
        guard samples.count >= 2 else { return 0 }
        return samples[samples.count - 1].score - samples[samples.count - 2].score
    }
}
