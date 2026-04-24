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

                // Rolling receipts ticker — right-to-left, newest enters from right edge
                if appState.recentReceipts.isEmpty {
                    TimelineEmptyCard()
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                    Spacer()
                } else {
                    ReceiptsTicker(receipts: Array(appState.recentReceipts.prefix(12).reversed()))
                        .frame(maxWidth: .infinity)
                }
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

private struct ReceiptsTicker: View {
    let receipts: [ReceiptEntry]

    private let speed: Double = 40          // pt/sec
    private let cardWidth: Double = 168     // 160 card + 8 gap

    private var loopWidth: CGFloat {
        CGFloat(cardWidth * Double(receipts.count) + 24)
    }

    var body: some View {
        TimelineView(.animation(minimumInterval: 1.0 / 30)) { timeline in
            let elapsed = CGFloat(timeline.date.timeIntervalSinceReferenceDate)
            let offset = loopWidth > 0
                ? -(elapsed * CGFloat(speed)).truncatingRemainder(dividingBy: loopWidth)
                : 0
            HStack(spacing: 8) {
                ForEach(receipts) { TimelineEventCard(receipt: $0) }
                ForEach(receipts) { TimelineEventCard(receipt: $0) }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .offset(x: offset)
        }
        .clipped()
    }
}

private struct TimelineEventCard: View {
    let receipt: ReceiptEntry

    // Color-coded by layer per Living Architecture spec tokens
    var layerColor: Color {
        let op = receipt.op.lowercased()
        if op.contains("adjudication") || op.contains("adjudicate") { return DSColors.Spec.adj }
        if op.contains("atom_write")   || op.contains("atom")       { return DSColors.Spec.alex }
        if op.contains("invariant")                                  { return DSColors.Spec.kernel }
        if op.contains("receipt")                                    { return DSColors.Spec.violet }
        if op.contains("cps")         || op.contains("handrail")    { return DSColors.Spec.handrail }
        if op.contains("chamber")     || op.contains("forge") ||
           op.contains("institute")   || op.contains("board")       { return DSColors.Spec.chambers }
        return DSColors.Spec.violet
    }

    var rowType: String {
        let op = receipt.op.lowercased()
        if op.contains("adjudication") || op.contains("adjudicate") { return "adjudication" }
        if op.contains("atom_write")   || op.contains("atom")       { return "atom_write" }
        if op.contains("invariant")                                  { return "invariant_check" }
        return "receipt"
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(receipt.op)
                    .font(.system(size: 10, weight: .semibold, design: .monospaced))
                    .foregroundColor(layerColor)
                    .lineLimit(1)
                Spacer()
                Circle()
                    .fill(receipt.status == "ok" || receipt.status == "success" ? DSColors.online : DSColors.offline)
                    .frame(width: 5, height: 5)
            }
            HStack {
                Text(rowType)
                    .font(.system(size: 7, weight: .medium))
                    .foregroundColor(layerColor.opacity(0.70))
                Spacer()
                Text(receipt.ts)
                    .font(.system(size: 8))
                    .foregroundColor(DSColors.textTertiary)
            }
        }
        .padding(8)
        .frame(width: 160)
        .background(layerColor.opacity(0.05))
        .cornerRadius(6)
        .overlay(RoundedRectangle(cornerRadius: 6).stroke(layerColor.opacity(0.25), lineWidth: 1))
    }
}
