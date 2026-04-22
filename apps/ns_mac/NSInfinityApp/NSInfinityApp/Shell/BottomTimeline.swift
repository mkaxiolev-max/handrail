import SwiftUI

struct BottomTimeline: View {
    @EnvironmentObject var appState: AppState
    @State private var selectedTab: TimelineTab = .receipts

    enum TimelineTab: String, CaseIterable { case receipts, events, commits }

    var body: some View {
        VStack(spacing: 0) {
            Rectangle().fill(DSColors.surfaceBorder).frame(height: 1)

            HStack(spacing: 0) {
                // Tab bar
                HStack(spacing: 0) {
                    ForEach(TimelineTab.allCases, id: \.self) { tab in
                        Button(tab.rawValue.uppercased()) {
                            selectedTab = tab
                        }
                        .buttonStyle(.plain)
                        .font(.system(size: 9, weight: .semibold))
                        .foregroundColor(selectedTab == tab ? DSColors.violet : DSColors.textTertiary)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .background(selectedTab == tab ? DSColors.violetFaint : Color.clear)
                    }
                }
                .padding(.leading, 8)

                Divider().frame(height: 20).overlay(DSColors.surfaceBorder)

                // Timeline content
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        if appState.recentReceipts.isEmpty {
                            TimelineEmptyCard()
                        } else {
                            ForEach(appState.recentReceipts.prefix(12)) { receipt in
                                TimelineEventCard(receipt: receipt)
                            }
                        }
                    }
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                }

                Spacer()
            }
            .frame(maxHeight: .infinity)
            .background(DSColors.surfaceElevated)
        }
    }
}

private struct TimelineEmptyCard: View {
    var body: some View {
        RoundedRectangle(cornerRadius: 6)
            .fill(DSColors.surfaceCard)
            .frame(width: 180, height: 76)
            .overlay(
                Text("No receipts — services offline")
                    .font(.system(size: 10))
                    .foregroundColor(DSColors.textTertiary)
            )
    }
}

private struct TimelineEventCard: View {
    let receipt: ReceiptEntry

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(receipt.op)
                    .font(.system(size: 10, weight: .semibold, design: .monospaced))
                    .foregroundColor(DSColors.accentCyan)
                    .lineLimit(1)
                Spacer()
                statusDot
            }
            Text(receipt.ts)
                .font(.system(size: 8))
                .foregroundColor(DSColors.textTertiary)
        }
        .padding(8)
        .frame(width: 160)
        .background(DSColors.surfaceCard)
        .cornerRadius(6)
        .overlay(RoundedRectangle(cornerRadius: 6).stroke(DSColors.surfaceBorder, lineWidth: 1))
    }

    var statusDot: some View {
        Circle()
            .fill(receipt.status == "ok" || receipt.status == "success" ? DSColors.online : DSColors.offline)
            .frame(width: 5, height: 5)
    }
}
