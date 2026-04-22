import Foundation

actor RuntimeAPIClient {
    static let shared = RuntimeAPIClient()

    private let nsBase  = "http://localhost:9000"
    private let hrBase  = "http://localhost:8011"
    private let ctBase  = "http://localhost:8788"

    private let session: URLSession = {
        let cfg = URLSessionConfiguration.default
        cfg.timeoutIntervalForRequest = 5
        cfg.timeoutIntervalForResource = 10
        return URLSession(configuration: cfg)
    }()

    // MARK: — Health

    func health(port: Int, path: String = "/healthz") async throws -> [String: Any] {
        let url = URL(string: "http://localhost:\(port)\(path)")!
        let (data, _) = try await session.data(from: url)
        return try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]
    }

    // MARK: — Score

    func fetchScore() async -> Double? {
        guard let url = URL(string: "\(nsBase)/score/current") else { return nil }
        do {
            let (data, _) = try await session.data(from: url)
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
            return json?["score"] as? Double ?? json?["v3_1"] as? Double
        } catch { return nil }
    }

    // MARK: — Voice

    func fetchVoiceSessions() async -> [String: Any] {
        guard let url = URL(string: "\(nsBase)/voice/sessions") else { return [:] }
        do {
            let (data, _) = try await session.data(from: url)
            return try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]
        } catch { return [:] }
    }

    func sendChat(_ text: String) async -> String {
        guard let url = URL(string: "\(nsBase)/chat/quick") else { return "" }
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try? JSONSerialization.data(withJSONObject: ["text": text])
        do {
            let (data, _) = try await session.data(for: req)
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
            return json?["response"] as? String ?? ""
        } catch { return "" }
    }

    // MARK: — Receipts / Timeline

    func fetchRecentReceipts(n: Int = 20) async -> [[String: Any]] {
        guard let url = URL(string: "\(nsBase)/memory/recent?n=\(n)") else { return [] }
        do {
            let (data, _) = try await session.data(from: url)
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
            return json?["entries"] as? [[String: Any]] ?? []
        } catch { return [] }
    }

    // MARK: — Alexandria

    func fetchAlexandriaStatus() async -> [String: Any] {
        guard let url = URL(string: "\(nsBase)/alexandria/status") else { return [:] }
        do {
            let (data, _) = try await session.data(from: url)
            return try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]
        } catch { return [:] }
    }

    // MARK: — Capability Graph

    func fetchCapabilityGraph() async -> [String: Any] {
        guard let url = URL(string: "\(nsBase)/capability/graph") else { return [:] }
        do {
            let (data, _) = try await session.data(from: url)
            return try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]
        } catch { return [:] }
    }

    // MARK: — Intel

    func fetchProactiveIntel() async -> [[String: Any]] {
        guard let url = URL(string: "\(nsBase)/intel/proactive") else { return [] }
        do {
            let (data, _) = try await session.data(from: url)
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
            return json?["suggestions"] as? [[String: Any]] ?? []
        } catch { return [] }
    }

    // MARK: — Continuum

    func fetchContinuumState() async -> [String: Any] {
        guard let url = URL(string: "\(ctBase)/continuum/status") else { return [:] }
        do {
            let (data, _) = try await session.data(from: url)
            return try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]
        } catch { return [:] }
    }

    // MARK: — CPS Execution

    func executeCPS(plan: [String: Any]) async throws -> [String: Any] {
        let url = URL(string: "\(hrBase)/ops/cps")!
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try JSONSerialization.data(withJSONObject: plan)
        let (data, resp) = try await session.data(for: req)
        guard let http = resp as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            throw RuntimeError.httpError((resp as? HTTPURLResponse)?.statusCode ?? 0)
        }
        return try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]
    }

    // MARK: — Semantic

    func fetchSemanticCandidates() async -> [[String: Any]] {
        guard let url = URL(string: "\(nsBase)/semantic/candidates") else { return [] }
        do {
            let (data, _) = try await session.data(from: url)
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
            return json?["candidates"] as? [[String: Any]] ?? []
        } catch { return [] }
    }

    // MARK: — Model registry

    func fetchModelStatus() async -> [String: Any] {
        guard let url = URL(string: "\(nsBase)/models/status") else { return [:] }
        do {
            let (data, _) = try await session.data(from: url)
            return try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]
        } catch { return [:] }
    }

    // MARK: — Ops recent (Jarvis)

    func fetchRecentOps() async -> [[String: Any]] {
        guard let url = URL(string: "\(nsBase)/ops/recent") else { return [] }
        do {
            let (data, _) = try await session.data(from: url)
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
            return json?["ops"] as? [[String: Any]] ?? []
        } catch { return [] }
    }

    enum RuntimeError: Error {
        case httpError(Int)
        case parseError
    }
}
