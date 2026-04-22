import SwiftUI

struct AlexandriaView: View {
    @State private var status: [String: Any] = [:]
    @State private var receipts: [[String: Any]] = []

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Text("Alexandria")
                    .font(.system(size: 28, weight: .black))
                    .foregroundColor(DSColors.textPrimary)

                // Status cards
                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                    AlexCard(title: "Snapshots", icon: "camera.fill", color: DSColors.accentCyan,
                             value: "\(status["snapshot_count"] as? Int ?? 0)")
                    AlexCard(title: "Ledger Entries", icon: "list.bullet.rectangle", color: DSColors.violet,
                             value: "\(status["ledger_count"] as? Int ?? 0)")
                    AlexCard(title: "SSD Mount", icon: "externaldrive.fill", color: DSColors.online,
                             value: status["ssd_mounted"] as? Bool == true ? "MOUNTED" : "FALLBACK")
                    AlexCard(title: "Root", icon: "folder.fill", color: DSColors.accentAmber,
                             value: status["root"] as? String ?? "—")
                }

                // Receipt chain
                VStack(alignment: .leading, spacing: 8) {
                    SectionHeader(title: "RECEIPT CHAIN")
                    if receipts.isEmpty {
                        Text("No receipts fetched — services offline")
                            .font(.system(size: 11))
                            .foregroundColor(DSColors.textTertiary)
                            .padding(12)
                            .background(DSColors.surfaceCard)
                            .cornerRadius(6)
                    } else {
                        ForEach(Array(receipts.prefix(10).enumerated()), id: \.offset) { _, r in
                            ReceiptRow(entry: r)
                        }
                    }
                }
            }
            .padding(24)
        }
        .task {
            status = await RuntimeAPIClient.shared.fetchAlexandriaStatus()
            receipts = await RuntimeAPIClient.shared.fetchRecentReceipts(n: 10)
        }
    }
}

private struct AlexCard: View {
    let title: String
    let icon: String
    let color: Color
    let value: String

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon).font(.system(size: 18)).foregroundColor(color)
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(.system(size: 10)).foregroundColor(DSColors.textTertiary)
                Text(value).font(.system(size: 13, weight: .bold, design: .monospaced)).foregroundColor(DSColors.textPrimary)
                    .lineLimit(1)
            }
        }
        .padding(12)
        .background(DSColors.surfaceCard)
        .cornerRadius(8)
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(color.opacity(0.2), lineWidth: 1))
    }
}

private struct ReceiptRow: View {
    let entry: [String: Any]
    var body: some View {
        HStack(spacing: 8) {
            Circle()
                .fill((entry["status"] as? String ?? "") == "ok" ? DSColors.online : DSColors.accentAmber)
                .frame(width: 5, height: 5)
            Text(entry["op"] as? String ?? entry["event"] as? String ?? "—")
                .font(.system(size: 10, design: .monospaced))
                .foregroundColor(DSColors.textSecondary)
            Spacer()
            Text(entry["ts"] as? String ?? "")
                .font(.system(size: 9))
                .foregroundColor(DSColors.textTertiary)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(DSColors.surfaceCard)
        .cornerRadius(5)
    }
}
