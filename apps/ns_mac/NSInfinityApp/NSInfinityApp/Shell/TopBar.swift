import SwiftUI

struct TopBar: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        HStack(spacing: 16) {
            // Brand
            HStack(spacing: 6) {
                Text("NS∞")
                    .font(.system(size: 18, weight: .black, design: .monospaced))
                    .foregroundColor(DSColors.violet)
                Text("AXIOLEV")
                    .font(.system(size: 11, weight: .bold))
                    .foregroundColor(DSColors.textSecondary)
                    .tracking(2)
            }
            .padding(.leading, 16)

            Divider().frame(height: 20).overlay(DSColors.surfaceBorder)

            // Mode label
            Text(appState.currentMode.rawValue.uppercased())
                .font(.system(size: 11, weight: .semibold))
                .foregroundColor(DSColors.textSecondary)
                .tracking(1.5)

            Spacer()

            // HUD indicators
            HUDPill(label: "DOCKER", value: appState.isServicesOnline ? "UP" : "DOWN",
                    color: appState.isServicesOnline ? DSColors.online : DSColors.offline)

            HUDPill(label: "INVARIANTS", value: "HELD", color: DSColors.online)

            HUDPill(label: "RINGS", value: "4/5", color: DSColors.accentAmber)

            HUDPill(label: "YUBIKEY",
                    value: "SLOT-1",
                    color: DSColors.online)

            HUDPill(label: "SHALOM", value: "✓", color: DSColors.violet)

            // Score badge
            ScoreBadge(score: appState.score)
                .padding(.trailing, 16)
        }
        .frame(maxHeight: .infinity)
        .background(DSColors.surfaceElevated)
        .overlay(alignment: .bottom) {
            Rectangle().fill(DSColors.surfaceBorder).frame(height: 1)
        }
    }
}

private struct HUDPill: View {
    let label: String
    let value: String
    let color: Color

    var body: some View {
        HStack(spacing: 4) {
            Circle().fill(color).frame(width: 5, height: 5)
            Text(label).font(.system(size: 9, weight: .medium)).foregroundColor(DSColors.textTertiary).tracking(1)
            Text(value).font(.system(size: 9, weight: .bold, design: .monospaced)).foregroundColor(color)
        }
        .padding(.horizontal, 7)
        .padding(.vertical, 3)
        .background(color.opacity(0.08))
        .cornerRadius(4)
    }
}

private struct ScoreBadge: View {
    let score: Double

    var body: some View {
        HStack(spacing: 4) {
            Text("v3.1")
                .font(.system(size: 9, weight: .medium)).foregroundColor(DSColors.textTertiary)
            Text(score > 0 ? String(format: "%.2f", score) : "—")
                .font(.system(size: 12, weight: .black, design: .monospaced))
                .foregroundColor(scoreColor)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(scoreColor.opacity(0.12))
        .cornerRadius(5)
    }

    var scoreColor: Color {
        if score >= 96 { return DSColors.violet }
        if score >= 93 { return DSColors.online }
        if score >= 90 { return DSColors.accentAmber }
        return DSColors.textSecondary
    }
}
