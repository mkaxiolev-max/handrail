import Foundation
import Combine

enum HabitatMode: String, CaseIterable, Identifiable {
    case livingArch     = "Living Architecture"
    case engineRoom     = "Engine Room"
    case founderHome    = "Programs Runtime"
    case alexandria     = "Memory"
    case governance     = "Governance"
    case buildSpace     = "Build Space"

    var id: String { rawValue }

    var icon: String {
        switch self {
        case .livingArch:   return "circle.hexagongrid.fill"
        case .engineRoom:   return "gearshape.2.fill"
        case .founderHome:  return "square.stack.3d.up.fill"
        case .alexandria:   return "memorychip"
        case .governance:   return "building.columns.fill"
        case .buildSpace:   return "hammer.fill"
        }
    }
}

final class AppState: ObservableObject {
    static let shared = AppState()

    @Published var currentMode: HabitatMode = .livingArch
    @Published var services: [ServiceHealth] = ServiceHealth.allServices
    @Published var score: Double = 0
    @Published var scoreLabel: String = "—"
    @Published var recentReceipts: [ReceiptEntry] = []
    @Published var voiceState: VoiceState = .dormant
    @Published var ringStatus: [RingStatus] = RingStatus.canonical
    @Published var founderIdentity = FounderIdentity.canonical
    @Published var isServicesOnline: Bool = false

    private var poller: HealthPoller?
    private var cancellables = Set<AnyCancellable>()

    private init() {
        poller = HealthPoller(appState: self)
        poller?.start()
    }
}

enum VoiceState: String {
    case dormant    = "dormant"
    case ready      = "ready"
    case listening  = "listening"
    case processing = "processing"
    case responding = "responding"
    case muted      = "muted"

    var label: String { rawValue.capitalized }

    var color: DSColors.Semantic {
        switch self {
        case .dormant:    return .inactive
        case .ready:      return .active
        case .listening:  return .alert
        case .processing: return .processing
        case .responding: return .responding
        case .muted:      return .inactive
        }
    }
}

struct FounderIdentity {
    let name: String
    let role: String
    let entity: String

    static let canonical = FounderIdentity(
        name: "Mike Kenworthy",
        role: "Founder",
        entity: "AXIOLEV Holdings"
    )
}

struct RingStatus: Identifiable {
    let id: Int
    let name: String
    let status: RingState
    let milestone: String

    enum RingState { case complete, blocked, inProgress }

    static let canonical: [RingStatus] = [
        RingStatus(id: 1, name: "Foundations",   status: .complete,    milestone: "M1 Founder MVP"),
        RingStatus(id: 2, name: "Intelligence",  status: .complete,    milestone: "M2 Jarvis"),
        RingStatus(id: 3, name: "Sovereign",     status: .complete,    milestone: "BLACK KNIGHT"),
        RingStatus(id: 4, name: "Capability",    status: .complete,    milestone: "Adapter + SAN"),
        RingStatus(id: 5, name: "Production",    status: .blocked,     milestone: "Stripe / Domain / Legal"),
    ]
}

struct ReceiptEntry: Identifiable, Codable {
    let id: String
    let op: String
    let status: String
    let ts: String
}
