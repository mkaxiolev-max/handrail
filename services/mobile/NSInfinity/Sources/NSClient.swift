import Foundation
import Combine

class NSClient: ObservableObject {
    static let shared = NSClient()
    @Published var isConnected = false
    @Published var lastResponse = ""
    @Published var memoryEntries: [[String: Any]] = []
    @Published var healthStatus: [String: Any] = [:]

    var baseURL: String {
        ProcessInfo.processInfo.environment["NS_BASE_URL"]
            ?? "https://monica-problockade-caylee.ngrok-free.dev"
    }

    func checkHealth() async {
        guard let url = URL(string: "\(baseURL)/healthz") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                await MainActor.run {
                    self.healthStatus = json
                    self.isConnected = json["status"] as? String == "ok"
                }
            }
        } catch { await MainActor.run { self.isConnected = false } }
    }

    func sendChat(_ text: String) async -> String {
        guard let url = URL(string: "\(baseURL)/chat/quick") else { return "" }
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try? JSONSerialization.data(withJSONObject: ["text": text])
        do {
            let (data, _) = try await URLSession.shared.data(for: req)
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
            return json?["response"] as? String ?? ""
        } catch { return "" }
    }

    func fetchMemory(n: Int = 10) async {
        guard let url = URL(string: "\(baseURL)/memory/recent?n=\(n)") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
               let entries = json["entries"] as? [[String: Any]] {
                await MainActor.run { self.memoryEntries = entries }
            }
        } catch {}
    }

    func fetchIntel() async -> [[String: Any]] {
        guard let url = URL(string: "\(baseURL)/intel/proactive") else { return [] }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
               let suggestions = json["suggestions"] as? [[String: Any]] {
                return suggestions
            }
        } catch {}
        return []
    }

    func fetchHIC(_ text: String) async -> [String: Any] {
        guard let url = URL(string: "\(baseURL)/hic/compile") else { return [:] }
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try? JSONSerialization.data(withJSONObject: ["text": text])
        do {
            let (data, _) = try await URLSession.shared.data(for: req)
            return try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]
        } catch { return [:] }
    }
}
