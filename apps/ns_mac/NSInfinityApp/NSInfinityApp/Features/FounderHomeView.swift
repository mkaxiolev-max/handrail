import SwiftUI

struct FounderHomeView: View {
    @EnvironmentObject var appState: AppState
    @State private var intel: [[String: Any]] = []
    @State private var recentOps: [[String: Any]] = []

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // Header
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Programs Runtime")
                            .font(.system(size: 28, weight: .black))
                            .foregroundColor(DSColors.textPrimary)
                        Text("\(appState.founderIdentity.name) · \(appState.founderIdentity.entity)")
                            .font(.system(size: 12)).foregroundColor(DSColors.textSecondary)
                    }
                    Spacer()
                    ScoreGlobe(score: appState.score, label: appState.scoreLabel)
                }

                // KPI grid
                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                    HomeCard(title: "Score Band", icon: "chart.bar.fill", color: DSColors.violet) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(appState.score > 0 ? String(format: "%.2f", appState.score) : "—")
                                .font(.system(size: 26, weight: .black, design: .monospaced))
                                .foregroundColor(DSColors.violet)
                            Text(appState.scoreLabel.isEmpty ? "NVIR stale" : appState.scoreLabel)
                                .font(.system(size: 10)).foregroundColor(DSColors.textTertiary)
                        }
                    }

                    HomeCard(title: "Ring Status", icon: "circle.hexagongrid", color: DSColors.accentCyan) {
                        VStack(alignment: .leading, spacing: 3) {
                            ForEach(appState.ringStatus) { ring in
                                HStack(spacing: 5) {
                                    Circle()
                                        .fill(ring.status == .complete ? DSColors.online :
                                              ring.status == .blocked  ? DSColors.offline : DSColors.accentAmber)
                                        .frame(width: 5, height: 5)
                                    Text("R\(ring.id)").font(.system(size: 9, design: .monospaced)).foregroundColor(DSColors.textTertiary)
                                    Text(ring.status == .blocked ? "BLOCKED" : "DONE")
                                        .font(.system(size: 9, weight: .semibold))
                                        .foregroundColor(ring.status == .complete ? DSColors.online : DSColors.offline)
                                }
                            }
                        }
                    }

                    HomeCard(title: "Services", icon: "server.rack", color: DSColors.accentAmber) {
                        VStack(alignment: .leading, spacing: 3) {
                            let onlineCount = appState.services.filter { $0.status == .online }.count
                            Text("\(onlineCount)/\(appState.services.count)")
                                .font(.system(size: 22, weight: .black, design: .monospaced))
                                .foregroundColor(onlineCount > 0 ? DSColors.online : DSColors.offline)
                            Text("services online").font(.system(size: 9)).foregroundColor(DSColors.textTertiary)
                        }
                    }
                }

                // Proactive Intel
                if !intel.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        SectionHeader(title: "PROACTIVE INTEL")
                        ForEach(Array(intel.prefix(3).enumerated()), id: \.offset) { _, item in
                            IntelRow(item: item)
                        }
                    }
                }

                // Recent ops
                if !recentOps.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        SectionHeader(title: "RECENT OPS")
                        ForEach(Array(recentOps.prefix(4).enumerated()), id: \.offset) { _, op in
                            RecentOpRow(op: op)
                        }
                    }
                }

                // Open loops
                VStack(alignment: .leading, spacing: 8) {
                    SectionHeader(title: "OPEN LOOPS")
                    OpenLoopRow(label: "Ring 5 — Stripe live keys needed", severity: .high,
                                actionLabel: "stripe.com/dashboard", actionURL: "https://stripe.com/dashboard")
                    OpenLoopRow(label: "Ring 5 — Production domain not configured", severity: .high,
                                actionLabel: "GoDaddy / Cloudflare DNS", actionURL: nil)
                    OpenLoopRow(label: "Ring 5 — Legal entity not formed", severity: .high,
                                actionLabel: "Stripe Atlas or Clerky", actionURL: "https://stripe.com/atlas")
                    OpenLoopRow(label: "2nd YubiKey slot unprovisioned", severity: .medium,
                                actionLabel: "Governance → YubiKey Quorum", actionURL: nil)
                    OpenLoopRow(label: "Branch not merged to main", severity: .medium,
                                actionLabel: "git push + PR", actionURL: nil)
                }
            }
            .padding(24)
        }
        .task {
            async let intelFetch  = RuntimeAPIClient.shared.fetchProactiveIntel()
            async let opsFetch    = RuntimeAPIClient.shared.fetchRecentOps()
            let (i, o) = await (intelFetch, opsFetch)
            intel = i; recentOps = o
        }
    }
}

private struct ScoreGlobe: View {
    let score: Double
    let label: String

    var body: some View {
        ZStack {
            Circle()
                .stroke(DSColors.violetDim, lineWidth: 2)
                .frame(width: 84, height: 84)
            Circle()
                .stroke(DSColors.violet.opacity(0.08), lineWidth: 8)
                .frame(width: 84, height: 84)
            VStack(spacing: 0) {
                Text(score > 0 ? String(format: "%.1f", score) : "—")
                    .font(.system(size: 22, weight: .black, design: .monospaced))
                    .foregroundColor(DSColors.violet)
                Text("v3.1").font(.system(size: 9)).foregroundColor(DSColors.textTertiary)
            }
        }
    }
}

private struct HomeCard<Content: View>: View {
    let title: String
    let icon: String
    let color: Color
    @ViewBuilder let content: () -> Content

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 6) {
                Image(systemName: icon).font(.system(size: 11)).foregroundColor(color)
                Text(title).font(.system(size: 10, weight: .semibold)).foregroundColor(DSColors.textSecondary)
            }
            content()
            Spacer()
        }
        .padding(12)
        .frame(minHeight: 110)
        .background(DSColors.surfaceCard)
        .cornerRadius(10)
        .overlay(RoundedRectangle(cornerRadius: 10).stroke(color.opacity(0.2), lineWidth: 1))
    }
}

private struct IntelRow: View {
    let item: [String: Any]
    var body: some View {
        HStack(alignment: .top, spacing: 10) {
            let pri = item["priority"] as? String ?? "low"
            Circle().fill(priColor(pri)).frame(width: 6, height: 6).padding(.top, 4)
            VStack(alignment: .leading, spacing: 2) {
                Text(item["suggestion"] as? String ?? "").font(.system(size: 11)).foregroundColor(DSColors.textSecondary)
                if let op = item["action_op"] as? String {
                    Text(op).font(.system(size: 9, design: .monospaced)).foregroundColor(DSColors.textTertiary)
                }
            }
        }
        .padding(10)
        .background(DSColors.surfaceCard)
        .cornerRadius(6)
    }
    func priColor(_ p: String) -> Color {
        switch p { case "critical": return DSColors.offline; case "high": return DSColors.accentAmber; default: return DSColors.textTertiary }
    }
}

private struct RecentOpRow: View {
    let op: [String: Any]
    var body: some View {
        HStack(spacing: 8) {
            let status = op["status"] as? String ?? "ok"
            Circle().fill(status == "ok" || status == "success" ? DSColors.online : DSColors.offline)
                .frame(width: 5, height: 5)
            Text(op["op"] as? String ?? op["operation"] as? String ?? "—")
                .font(.system(size: 10, design: .monospaced)).foregroundColor(DSColors.textSecondary)
            Spacer()
            Text(op["ts"] as? String ?? op["timestamp"] as? String ?? "")
                .font(.system(size: 9)).foregroundColor(DSColors.textTertiary)
        }
        .padding(8).background(DSColors.surfaceCard).cornerRadius(5)
    }
}

enum OpenLoopSeverity { case high, medium, low }

struct OpenLoopRow: View {
    let label: String
    let severity: OpenLoopSeverity
    var actionLabel: String? = nil
    var actionURL: String? = nil

    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: severity == .high ? "exclamationmark.triangle.fill" : "circle.fill")
                .font(.system(size: 10))
                .foregroundColor(severity == .high ? DSColors.offline : DSColors.accentAmber)
            VStack(alignment: .leading, spacing: 2) {
                Text(label).font(.system(size: 11)).foregroundColor(DSColors.textSecondary)
                if let al = actionLabel {
                    if let urlStr = actionURL, let url = URL(string: urlStr) {
                        Link(al, destination: url)
                            .font(.system(size: 9)).foregroundColor(DSColors.violet)
                    } else {
                        Text(al).font(.system(size: 9)).foregroundColor(DSColors.textTertiary)
                    }
                }
            }
            Spacer()
        }
        .padding(8).background(DSColors.surfaceCard).cornerRadius(6)
    }
}

#Preview {
    FounderHomeView()
        .environmentObject(AppState.shared)
        .frame(width: 900, height: 700)
        .preferredColorScheme(.dark)
}
