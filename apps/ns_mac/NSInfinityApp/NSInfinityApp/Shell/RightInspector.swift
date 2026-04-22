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

                // Ring 5 gates
                InspectorSection(title: "RING 5 GATES") {
                    VStack(alignment: .leading, spacing: 4) {
                        Ring5Gate(label: "Stripe live keys",  blocked: true,  actionLabel: "stripe.com/dashboard")
                        Ring5Gate(label: "Production domain", blocked: true,  actionLabel: "GoDaddy / Cloudflare")
                        Ring5Gate(label: "Legal entity",      blocked: true,  actionLabel: "Stripe Atlas / Clerky")
                    }
                }

                // Alexandria summary
                InspectorSection(title: "ALEXANDRIA") {
                    AlexandriaSummaryWidget()
                }

                // Founder proofs
                InspectorSection(title: "FOUNDER PROOFS") {
                    VStack(alignment: .leading, spacing: 3) {
                        ProofRow(label: "Boot proof", present: true)
                        ProofRow(label: "Receipt chain", present: true)
                        ProofRow(label: "Merkle proof", present: true)
                        ProofRow(label: "YubiKey quorum", present: true)
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

    var chambers: [(String, Int)] {
        let nodes = capGraph["nodes"] as? [[String: Any]] ?? []
        return nodes.compactMap { n -> (String, Int)? in
            guard let id = n["id"] as? String,
                  let sv = n["strategic_value"] as? Int else { return nil }
            return (id, sv)
        }.prefix(6).map { $0 }
    }

    var body: some View {
        VStack(spacing: 4) {
            ForEach(chambers, id: \.0) { id, sv in
                HStack(spacing: 6) {
                    Text(id).font(.system(size: 9, design: .monospaced)).foregroundColor(DSColors.textSecondary).lineLimit(1)
                    Spacer()
                    GeometryReader { geo in
                        ZStack(alignment: .leading) {
                            RoundedRectangle(cornerRadius: 2).fill(DSColors.surfaceBorder).frame(height: 3)
                            RoundedRectangle(cornerRadius: 2)
                                .fill(sv >= 8 ? DSColors.violet : DSColors.accentCyan)
                                .frame(width: geo.size.width * CGFloat(sv) / 10.0, height: 3)
                        }
                    }.frame(width: 60, height: 3)
                    Text("\(sv)").font(.system(size: 8, design: .monospaced)).foregroundColor(DSColors.textTertiary).frame(width: 12)
                }
            }
            if chambers.isEmpty {
                Text("offline").font(.system(size: 9)).foregroundColor(DSColors.textTertiary)
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
    @State private var status: String = "checking…"
    var body: some View {
        HStack(spacing: 6) {
            Image(systemName: "archivebox").font(.system(size: 10)).foregroundColor(DSColors.accentCyan)
            Text(status).font(.system(size: 10)).foregroundColor(DSColors.textSecondary)
        }
        .task {
            let result = await RuntimeAPIClient.shared.fetchAlexandriaStatus()
            if let snapshots = result["snapshot_count"] as? Int,
               let ledger    = result["ledger_count"] as? Int {
                status = "\(snapshots) snapshots · \(ledger) ledger"
            } else {
                status = "offline"
            }
        }
    }
}
