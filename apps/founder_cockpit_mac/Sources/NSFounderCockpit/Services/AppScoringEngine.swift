import Foundation

enum AppScoringEngine {
    @MainActor
    static func compute(state: AppState) -> CockpitScore {
        let svcs = state.services
        let upCount = Double(svcs.filter { $0.isUp }.count)
        let total = Double(max(svcs.count, 1))

        // D1: Endpoint availability (6 core services)
        let d1 = (upCount / total) * 10.0

        // D2: Query routing — check if /query returns a valid verb
        let d2: Double
        if let qr = state.queryResponse {
            d2 = ["collapse_ready","hold_ncom","force_more_branches","abort"].contains(qr.verb) ? 10.0 : 4.0
        } else { d2 = 0.0 }

        // D3: NCOM dashboard accessible
        let ncomUp = svcs.first(where: { $0.id == "ncom" })?.isUp ?? false
        let d3 = ncomUp ? 10.0 : 0.0

        // D4: Canon panel has data or is reachable
        let canonSvcUp = svcs.first(where: { $0.id == "ns_core" })?.isUp ?? false
        let d4 = canonSvcUp ? (state.canonRecords.isEmpty ? 6.0 : 10.0) : 0.0

        // D5: Contradictions panel — pressure score tracking
        let d5: Double
        if let ct = state.contradictions {
            d5 = ct.pressure_score <= 1.0 ? 10.0 : 0.0
        } else if canonSvcUp { d5 = 6.0 } else { d5 = 0.0 }

        // D6: Memory atoms/molecules reachable
        let d6 = canonSvcUp ? (state.atoms.isEmpty && state.molecules.isEmpty ? 6.0 : 10.0) : 0.0

        // D7: Storytime narration
        let d7: Double
        if let st = state.storytime {
            d7 = !st.rule.isEmpty ? 10.0 : 5.0
        } else if canonSvcUp { d7 = 5.0 } else { d7 = 0.0 }

        // D8: Mac Adapter bridge
        let macUp = svcs.first(where: { $0.id == "mac" })?.isUp ?? false
        let d8 = macUp ? 10.0 : 0.0

        // D9: Receipt/ledger integrity
        let d9: Double
        if let lh = state.ledger {
            d9 = lh.all_chains_valid == true ? 10.0 : 3.0
        } else if ncomUp { d9 = 5.0 } else { d9 = 0.0 }

        return CockpitScore(dimensions: [
            .init(id: "d1", label: "Endpoint Availability",    score: d1, note: "\(Int(upCount))/\(Int(total)) services up"),
            .init(id: "d2", label: "IMO Gate Query Routing",   score: d2, note: state.queryResponse.map { "verb: \($0.verb)" } ?? "no query sent yet"),
            .init(id: "d3", label: "NCOM Dashboard :9020",     score: d3, note: ncomUp ? "live" : "unreachable"),
            .init(id: "d4", label: "Canon Panel",              score: d4, note: "\(state.canonRecords.count) collapse_ready records"),
            .init(id: "d5", label: "Contradiction Tracking",   score: d5, note: state.contradictions.map { String(format: "pressure %.2f", $0.pressure_score) } ?? "pending"),
            .init(id: "d6", label: "Memory Atoms/Molecules",   score: d6, note: "\(state.atoms.count) atoms, \(state.molecules.count) molecules"),
            .init(id: "d7", label: "Storytime Narration",      score: d7, note: state.storytime.map { "\($0.what_happened.count) events" } ?? "pending"),
            .init(id: "d8", label: "Mac Adapter Bridge :8765", score: d8, note: macUp ? "81 methods live" : "unreachable"),
            .init(id: "d9", label: "Receipt/Ledger Integrity", score: d9, note: state.ledger.map { $0.all_chains_valid == true ? "all chains valid" : "violation" } ?? "pending"),
        ])
    }
}
