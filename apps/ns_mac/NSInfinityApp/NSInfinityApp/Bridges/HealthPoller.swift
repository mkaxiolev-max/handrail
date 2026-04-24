import Foundation
import Combine

final class HealthPoller {
    private weak var appState: AppState?
    private var timer: Timer?
    private let interval: TimeInterval = 8.0

    init(appState: AppState) {
        self.appState = appState
    }

    func start() {
        poll()
        timer = Timer.scheduledTimer(withTimeInterval: interval, repeats: true) { [weak self] _ in
            self?.poll()
        }
    }

    func stop() {
        timer?.invalidate()
        timer = nil
    }

    private func poll() {
        Task { [weak self] in
            guard let self, let state = self.appState else { return }

            // Service health
            let ports: [(String, Int, String)] = [
                ("handrail",  8011, "/healthz"),
                ("ns",        9000, "/healthz"),
                ("continuum", 8788, "/continuum/status"),
                ("svc-9001",  9001, "/healthz"),
                ("svc-9002",  9002, "/healthz"),
                ("svc-9003",  9003, "/healthz"),
                ("svc-9004",  9004, "/healthz"),
                ("svc-9005",  9005, "/healthz"),
                ("svc-9006",  9006, "/healthz"),
                ("svc-9010",  9010, "/healthz"),
                ("svc-9011",  9011, "/healthz"),
            ]
            var anyOnline = false
            for (id, port, path) in ports {
                let isOnline: Bool
                do {
                    _ = try await RuntimeAPIClient.shared.health(port: port, path: path)
                    isOnline = true
                    anyOnline = true
                } catch {
                    isOnline = false
                }
                await MainActor.run {
                    if let svc = state.services.first(where: { $0.id == id }) {
                        svc.status = isOnline ? .online : .offline
                        svc.lastChecked = Date()
                    }
                }
            }
            await MainActor.run { state.isServicesOnline = anyOnline }

            guard anyOnline else { return }

            // Score
            async let scoreFetch     = RuntimeAPIClient.shared.fetchScore()
            // Voice sessions
            async let voiceFetch     = RuntimeAPIClient.shared.fetchVoiceSessions()
            // Recent receipts
            async let receiptsFetch  = RuntimeAPIClient.shared.fetchRecentReceipts(n: 20)

            let (scoreVal, voiceData, receiptsRaw) = await (scoreFetch, voiceFetch, receiptsFetch)

            await MainActor.run {
                if let s = scoreVal {
                    state.score = s
                    state.scoreLabel = scoreBand(s)
                }

                // Voice state from sessions
                let activeSessions = voiceData["active_sessions"] as? [[String: Any]] ?? []
                if activeSessions.isEmpty {
                    if state.voiceState == .listening || state.voiceState == .processing {
                        state.voiceState = .ready
                    } else if state.voiceState == .dormant {
                        state.voiceState = .ready
                    }
                } else {
                    state.voiceState = .listening
                }

                // Receipts
                state.recentReceipts = receiptsRaw.compactMap { dict -> ReceiptEntry? in
                    guard let id  = dict["id"] as? String ?? dict["receipt_id"] as? String,
                          let op  = dict["op"] as? String ?? dict["event"] as? String,
                          let ts  = dict["ts"] as? String ?? dict["timestamp"] as? String
                    else { return nil }
                    let status = dict["status"] as? String ?? "ok"
                    return ReceiptEntry(id: id, op: op, status: status, ts: ts)
                }
            }
        }
    }

    private func scoreBand(_ s: Double) -> String {
        if s >= 96 { return "Omega-Full" }
        if s >= 93 { return "Omega-Certified" }
        if s >= 90 { return "Omega-Approaching" }
        return "Pre-Omega"
    }
}
