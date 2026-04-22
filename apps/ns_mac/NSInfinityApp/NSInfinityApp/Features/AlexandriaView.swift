import SwiftUI

struct AlexandriaView: View {
    @State private var status: [String: Any] = [:]
    @State private var receipts: [[String: Any]] = []
    @State private var ledgerPage = 0
    @State private var isLoading = false
    private let pageSize = 20

    var body: some View {
        HStack(spacing: 0) {
            // Left: status + controls
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    Text("Alexandria")
                        .font(.habitatTitle())
                        .foregroundColor(DSColors.textPrimary)

                    // Status grid
                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                        AlexCard(title: "Snapshots",    icon: "camera.fill",             color: DSColors.accentCyan,
                                 value: "\(status["snapshot_count"] as? Int ?? 0)")
                        AlexCard(title: "Ledger Entries", icon: "list.bullet.rectangle", color: DSColors.violet,
                                 value: "\(status["ledger_count"] as? Int ?? 0)")
                        AlexCard(title: "SSD Mount",    icon: "externaldrive.fill",      color: DSColors.online,
                                 value: status["ssd_mounted"] as? Bool == true ? "MOUNTED" : "FALLBACK")
                        AlexCard(title: "Root",         icon: "folder.fill",             color: DSColors.accentAmber,
                                 value: shortPath(status["root"] as? String ?? "—"))
                    }

                    // Alexandria architecture
                    VStack(alignment: .leading, spacing: 8) {
                        SectionHeader(title: "THREE-REALITY SPINE")
                        ForEach(realityLayers, id: \.0) { name, desc, color in
                            RealityLayerRow(name: name, desc: desc, color: color)
                        }
                    }
                }
                .padding(24)
            }
            .frame(maxWidth: .infinity)

            Rectangle().fill(DSColors.surfaceBorder).frame(width: 1)

            // Right: paginated receipt chain viewer
            VStack(alignment: .leading, spacing: 0) {
                HStack {
                    SectionHeader(title: "RECEIPT CHAIN")
                    Spacer()
                    if isLoading { ProgressView().scaleEffect(0.6) }
                    Button("← Prev") { if ledgerPage > 0 { ledgerPage -= 1; Task { await loadReceipts() } } }
                        .buttonStyle(.plain).font(.system(size: 10)).foregroundColor(DSColors.textTertiary)
                        .disabled(ledgerPage == 0)
                    Text("p\(ledgerPage + 1)").font(.system(size: 9, design: .monospaced)).foregroundColor(DSColors.textTertiary)
                    Button("Next →") { ledgerPage += 1; Task { await loadReceipts() } }
                        .buttonStyle(.plain).font(.system(size: 10)).foregroundColor(DSColors.textTertiary)
                        .disabled(receipts.count < pageSize)
                }
                .padding(.horizontal, 14).padding(.top, 16).padding(.bottom, 8)

                Divider().overlay(DSColors.surfaceBorder)

                ScrollView {
                    LazyVStack(spacing: 3) {
                        if receipts.isEmpty {
                            Text(status.isEmpty ? "Loading…" : "No receipts — services offline")
                                .font(.system(size: 10)).foregroundColor(DSColors.textTertiary).padding(12)
                        } else {
                            ForEach(Array(receipts.enumerated()), id: \.offset) { _, r in
                                ReceiptRow(entry: r)
                            }
                        }
                    }
                    .padding(.horizontal, 10).padding(.vertical, 6)
                }
            }
            .frame(width: 340)
            .background(DSColors.surfaceElevated)
        }
        .task {
            async let statusFetch   = RuntimeAPIClient.shared.fetchAlexandriaStatus()
            async let receiptsFetch = RuntimeAPIClient.shared.fetchRecentReceipts(n: pageSize)
            let (s, r) = await (statusFetch, receiptsFetch)
            status = s; receipts = r
        }
    }

    func loadReceipts() async {
        isLoading = true
        receipts = await RuntimeAPIClient.shared.fetchRecentReceipts(n: pageSize)
        isLoading = false
    }

    func shortPath(_ p: String) -> String {
        p.replacingOccurrences(of: "/Users/axiolevns/", with: "~/")
         .replacingOccurrences(of: "/Volumes/", with: "⎇/")
    }

    let realityLayers: [(String, String, Color)] = [
        ("Lexicon",    "Semantic reality — canonical meanings, USDL gate library", DSColors.violet),
        ("Alexandria", "Knowledge reality — receipts, sessions, canon, MaRS",       DSColors.accentCyan),
        ("SAN",        "Legal/territorial reality — claims, filings, licensing",     DSColors.accentAmber),
    ]
}

private struct AlexCard: View {
    let title: String; let icon: String; let color: Color; let value: String
    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: icon).font(.system(size: 16)).foregroundColor(color)
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(.system(size: 9)).foregroundColor(DSColors.textTertiary)
                Text(value).font(.system(size: 12, weight: .bold, design: .monospaced))
                    .foregroundColor(DSColors.textPrimary).lineLimit(1)
            }
        }
        .padding(12).background(DSColors.surfaceCard).cornerRadius(8)
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(color.opacity(0.2), lineWidth: 1))
    }
}

private struct RealityLayerRow: View {
    let name: String; let desc: String; let color: Color
    var body: some View {
        HStack(spacing: 8) {
            RoundedRectangle(cornerRadius: 2).fill(color).frame(width: 3, height: 36)
            VStack(alignment: .leading, spacing: 2) {
                Text(name).font(.system(size: 11, weight: .semibold)).foregroundColor(DSColors.textPrimary)
                Text(desc).font(.system(size: 9)).foregroundColor(DSColors.textTertiary).lineLimit(2)
            }
        }
        .padding(8).background(DSColors.surfaceCard).cornerRadius(6)
    }
}

private struct ReceiptRow: View {
    let entry: [String: Any]
    var body: some View {
        HStack(spacing: 6) {
            let ok = (entry["status"] as? String ?? "ok") == "ok"
            RoundedRectangle(cornerRadius: 1)
                .fill(ok ? DSColors.online : DSColors.accentAmber)
                .frame(width: 2, height: 28)
            VStack(alignment: .leading, spacing: 1) {
                Text(entry["op"] as? String ?? entry["event"] as? String ?? "—")
                    .font(.system(size: 9, design: .monospaced)).foregroundColor(DSColors.textSecondary).lineLimit(1)
                Text(entry["ts"] as? String ?? entry["timestamp"] as? String ?? "")
                    .font(.system(size: 8)).foregroundColor(DSColors.textTertiary)
            }
            Spacer()
            if let id = entry["id"] as? String {
                Text(String(id.suffix(6)))
                    .font(.system(size: 7, design: .monospaced)).foregroundColor(DSColors.textTertiary)
            }
        }
        .padding(.horizontal, 6).padding(.vertical, 4)
        .background(DSColors.surfaceCard).cornerRadius(4)
    }
}

#Preview {
    AlexandriaView()
        .frame(width: 1100, height: 700)
        .preferredColorScheme(.dark)
}
