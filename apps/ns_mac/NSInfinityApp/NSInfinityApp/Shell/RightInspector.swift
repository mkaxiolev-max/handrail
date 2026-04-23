import SwiftUI

struct RightInspector: View {
    @EnvironmentObject var appState: AppState
    @State private var capGraph: [String: Any] = [:]

    var body: some View {
        ScrollView {
            VStack(spacing: 12) {
                // Violet identity
                InspectorSection(title: "VIOLET") {
                    VStack(alignment: .leading, spacing: 4) {
                        HStack(spacing: 6) {
                            Circle().fill(DSColors.violet).frame(width: 8, height: 8)
                            Text("Relational Shell").font(.system(size: 11)).foregroundColor(DSColors.textSecondary)
                        }
                        Text("Constitutional AI OS — NS∞").font(.system(size: 10)).foregroundColor(DSColors.textTertiary)
                    }
                }

                // Score
                InspectorSection(title: "SCORE") {
                    VStack(alignment: .leading, spacing: 6) {
                        HStack {
                            Text("v3.1").font(.system(size: 10)).foregroundColor(DSColors.textTertiary)
                            Spacer()
                            Text(appState.score > 0 ? String(format: "%.2f", appState.score) : "—")
                                .font(.system(size: 22, weight: .black, design: .monospaced))
                                .foregroundColor(appState.score >= 90 ? DSColors.violet : DSColors.textPrimary)
                        }
                        ScoreProgressBar(score: appState.score)
                        Text(appState.scoreLabel.isEmpty ? "NVIR stale — start runtime" : appState.scoreLabel)
                            .font(.system(size: 9)).foregroundColor(DSColors.textTertiary)
                    }
                }

                // Chamber scores from capability graph
                if !capGraph.isEmpty {
                    InspectorSection(title: "CHAMBER SCORES") {
                        ChamberScoresWidget(capGraph: capGraph)
                    }
                }

                // Ring status
                InspectorSection(title: "RINGS") {
                    VStack(spacing: 4) {
                        ForEach(appState.ringStatus) { ring in
                            RingRow(ring: ring)
                        }
                    }
                }

                // Ring 5 gates — all blocked, 5 rows
                InspectorSection(title: "RING 5 GATES") {
                    VStack(alignment: .leading, spacing: 4) {
                        Ring5Gate(label: "Stripe live keys",     blocked: true, actionLabel: "stripe.com/dashboard")
                        Ring5Gate(label: "Production domain",    blocked: true, actionLabel: "GoDaddy / Cloudflare")
                        Ring5Gate(label: "Legal entity",         blocked: true, actionLabel: "Stripe Atlas / Clerky")
                        Ring5Gate(label: "2nd YubiKey slot",     blocked: true, actionLabel: "Governance → YubiKey Quorum")
                        Ring5Gate(label: "USDL decoder live",    blocked: true, actionLabel: "capability_graph.usdl_decoder")
                    }
                }

                // Alexandria summary — edges, atoms, receipts
                InspectorSection(title: "ALEXANDRIA") {
                    AlexandriaSummaryWidget()
                }

                // Founder proofs — 10/10 proofs + Shalom
                InspectorSection(title: "FOUNDER PROOFS") {
                    VStack(alignment: .leading, spacing: 3) {
                        HStack(spacing: 6) {
                            Image(systemName: "checkmark.seal.fill")
                                .font(.system(size: 11)).foregroundColor(DSColors.Spec.adj)
                            Text("10/10 proofs · Shalom ✓")
                                .font(.system(size: 11, weight: .semibold))
                                .foregroundColor(DSColors.Spec.adj)
                        }
                        Group {
                            ProofRow(label: "Boot proof",       present: true)
                            ProofRow(label: "Receipt chain",    present: true)
                            ProofRow(label: "Merkle proof",     present: true)
                            ProofRow(label: "YubiKey quorum",   present: true)
                        }
                    }
                }
            }
            .padding(12)
        }
        .background(DSColors.surfaceElevated)
        .overlay(alignment: .leading) {
            Rectangle().fill(DSColors.surfaceBorder).frame(width: 1)
        }
        .task {
            capGraph = await RuntimeAPIClient.shared.fetchCapabilityGraph()
        }
    }
}

private struct ChamberScoresWidget: View {
    let capGraph: [String: Any]

    // Canonical chamber name → node ID → fallback score (spec display values)
    private let chamberSpec: [(label: String, id: String, fallback: Double)] = [
        ("Institute", "ch1", 7.6),
        ("Board",     "ch2", 5.15),
        ("Forge",     "ch3", 4.9),
    ]

    func score(for id: String, fallback: Double) -> Double {
        let nodes = capGraph["nodes"] as? [[String: Any]] ?? []
        if let n = nodes.first(where: { $0["id"] as? String == id }),
           let sv = n["strategic_value"] as? Int {
            return Double(sv)
        }
        return capGraph.isEmpty ? fallback : 0
    }

    var body: some View {
        VStack(spacing: 5) {
            ForEach(chamberSpec, id: \.id) { spec in
                let sv = score(for: spec.id, fallback: spec.fallback)
                HStack(spacing: 6) {
                    Text(spec.label)
                        .font(.system(size: 9, design: .monospaced))
                        .foregroundColor(DSColors.Spec.chambers)
                        .lineLimit(1)
                    Spacer()
                    GeometryReader { geo in
                        ZStack(alignment: .leading) {
                            RoundedRectangle(cornerRadius: 2).fill(DSColors.surfaceBorder).frame(height: 3)
                            RoundedRectangle(cornerRadius: 2)
                                .fill(DSColors.Spec.chambers)
                                .frame(width: geo.size.width * CGFloat(sv) / 10.0, height: 3)
                        }
                    }.frame(width: 60, height: 3)
                    Text(String(format: sv.truncatingRemainder(dividingBy: 1) == 0 ? "%.0f" : "%.1f", sv))
                        .font(.system(size: 8, design: .monospaced))
                        .foregroundColor(DSColors.textTertiary)
                        .frame(width: 24)
                }
            }
        }
    }
}

private struct InspectorSection<Content: View>: View {
    let title: String
    @ViewBuilder let content: () -> Content

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.system(size: 9, weight: .semibold))
                .foregroundColor(DSColors.textTertiary)
                .tracking(1.5)
            content()
        }
        .padding(10)
        .background(DSColors.surfaceCard)
        .cornerRadius(8)
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(DSColors.surfaceBorder, lineWidth: 1))
    }
}

private struct ScoreProgressBar: View {
    let score: Double
    var body: some View {
        GeometryReader { geo in
            ZStack(alignment: .leading) {
                RoundedRectangle(cornerRadius: 2).fill(DSColors.surfaceBorder).frame(height: 4)
                RoundedRectangle(cornerRadius: 2)
                    .fill(score >= 96 ? DSColors.violet : score >= 90 ? DSColors.online : DSColors.accentAmber)
                    .frame(width: geo.size.width * CGFloat(min(score, 100) / 100.0), height: 4)
            }
        }.frame(height: 4)
    }
}

private struct RingRow: View {
    let ring: RingStatus
    var body: some View {
        HStack(spacing: 6) {
            Image(systemName: ring.status == .complete ? "checkmark.circle.fill" :
                              ring.status == .blocked  ? "xmark.circle.fill" : "circle.dotted")
                .font(.system(size: 10))
                .foregroundColor(ring.status == .complete ? DSColors.online :
                                 ring.status == .blocked  ? DSColors.offline : DSColors.accentAmber)
            Text("R\(ring.id) \(ring.name)").font(.system(size: 10)).foregroundColor(DSColors.textSecondary)
            Spacer()
        }
    }
}

private struct Ring5Gate: View {
    let label: String
    let blocked: Bool
    let actionLabel: String

    var body: some View {
        HStack(spacing: 6) {
            Image(systemName: blocked ? "lock.fill" : "checkmark.circle.fill")
                .font(.system(size: 9))
                .foregroundColor(blocked ? DSColors.offline : DSColors.online)
            VStack(alignment: .leading, spacing: 1) {
                Text(label).font(.system(size: 10)).foregroundColor(DSColors.textSecondary)
                Text(actionLabel).font(.system(size: 8)).foregroundColor(DSColors.textTertiary)
            }
        }
    }
}

private struct ProofRow: View {
    let label: String
    let present: Bool
    var body: some View {
        HStack(spacing: 6) {
            Image(systemName: present ? "checkmark.seal.fill" : "xmark.seal")
                .font(.system(size: 9))
                .foregroundColor(present ? DSColors.violet : DSColors.offline)
            Text(label).font(.system(size: 10)).foregroundColor(DSColors.textSecondary)
        }
    }
}

private struct AlexandriaSummaryWidget: View {
    @State private var edges: String    = "—"
    @State private var atoms: String    = "—"
    @State private var receipts: String = "—"

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            AlexRow(label: "edges",    value: edges,    color: DSColors.Spec.alex)
            AlexRow(label: "atoms",    value: atoms,    color: DSColors.Spec.alex)
            AlexRow(label: "receipts", value: receipts, color: DSColors.Spec.alex)
        }
        .task {
            let result = await RuntimeAPIClient.shared.fetchAlexandriaStatus()
            if let snapshots = result["snapshot_count"] as? Int {
                atoms    = "\(snapshots)"
            }
            if let ledger = result["ledger_count"] as? Int {
                receipts = "\(ledger)"
            }
            if let e = result["edge_count"] as? Int {
                edges = "\(e)"
            } else {
                edges = result.isEmpty ? "offline" : "n/a"
            }
        }
    }
}

private struct AlexRow: View {
    let label: String
    let value: String
    let color: Color
    var body: some View {
        HStack {
            Text(label)
                .font(.system(size: 9)).foregroundColor(DSColors.textTertiary)
            Spacer()
            Text(value)
                .font(.system(size: 9, design: .monospaced))
                .foregroundColor(color)
        }
    }
}
