import Foundation

final class ServiceHealth: Identifiable, ObservableObject {
    let id: String
    let name: String
    let port: Int
    let endpoint: String
    @Published var status: Status = .unknown
    @Published var lastChecked: Date? = nil

    enum Status: String {
        case online  = "online"
        case offline = "offline"
        case unknown = "unknown"
        case degraded = "degraded"

        var label: String { rawValue.capitalized }
    }

    init(id: String, name: String, port: Int, endpoint: String) {
        self.id = id; self.name = name; self.port = port; self.endpoint = endpoint
    }

    var healthURL: URL? {
        URL(string: "http://localhost:\(port)\(endpoint)")
    }

    static let allServices: [ServiceHealth] = [
        ServiceHealth(id: "handrail",  name: "Handrail",  port: 8011, endpoint: "/healthz"),
        ServiceHealth(id: "ns",        name: "NorthStar", port: 9000, endpoint: "/healthz"),
        ServiceHealth(id: "continuum", name: "Continuum", port: 8788, endpoint: "/continuum/status"),
        ServiceHealth(id: "svc-9001",  name: "Svc-9001",  port: 9001, endpoint: "/healthz"),
        ServiceHealth(id: "svc-9010",  name: "Svc-9010",  port: 9010, endpoint: "/healthz"),
        ServiceHealth(id: "svc-9011",  name: "Svc-9011",  port: 9011, endpoint: "/healthz"),
    ]
}
