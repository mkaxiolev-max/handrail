import SwiftUI

struct TopBar: View {
    @EnvironmentObject var appState: AppState
    @StateObject private var scoreHistory = ScoreHistory.shared

    var body: some View {
        HStack(spacing: 14) {
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
                .animation(.easeInOut(duration: 0.15), value: appState.currentMode)

            Spacer()

            // HUD indicators
            HUDPill(label: "DOCKER",
                    value: appState.isServicesOnline ? "UP" : "DOWN",
                    color: appState.isServicesOnline ? DSColors.online : DSColors.offline)
            HUDPill(label: "INVARIANTS", value: "HELD",  color: DSColors.online)
            HUDPill(label: "RINGS",      value: "4/5",   color: DSColors.accentAmber)
            HUDPill(label: "YUBIKEY",    value: "SLOT-1", color: DSColors.online)
            HUDPill(label: "SHALOM",     value: "✓",     color: DSColors.violet)

            Divider().frame(height: 20).overlay(DSColors.surfaceBorder)

            // Score badge + sparkline + trend
            ScoreCluster(score: appState.score, history: scoreHistory)
                .padding(.trailing, 16)
        }
        .frame(maxHeight: .infinity)
        .background(DSColors.surfaceElevated)
        .overlay(alignment: .bottom) {
            Rectangle().fill(DSColors.surfaceBorder).frame(height: 1)
        }
        .onChange(of: appState.score) { _, newScore in
            scoreHistory.record(newScore)
        }
    }
}

// MARK: — HUD Pill

private struct HUDPill: View {
    let label: String
    let value: String
    let color: Color

    var body: some View {
        HStack(spacing: 4) {
            Circle().fill(color).frame(width: 5, height: 5)
            Text(label)
                .font(.system(size: 9, weight: .medium))
                .foregroundColor(DSColors.textTertiary)
                .tracking(1)
            Text(value)
                .font(.system(size: 9, weight: .bold, design: .monospaced))
                .foregroundColor(color)
        }
        .padding(.horizontal, 7).padding(.vertical, 3)
        .background(color.opacity(0.08))
        .cornerRadius(4)
    }
}

// MARK: — Score Cluster (badge + sparkline + trend arrow)

private struct ScoreCluster: View {
    let score: Double
    @ObservedObject var history: ScoreHistory

    var body: some View {
        HStack(spacing: 8) {
            // Sparkline
            if history.sparklinePoints.count >= 2 {
                SparklineView(points: history.sparklinePoints)
                    .frame(width: 48, height: 18)
            }

            // Trend arrow
            Text(history.trend.rawValue)
                .font(.system(size: 11, weight: .bold))
                .foregroundColor(trendColor)
                .animation(.easeInOut, value: history.trend)

            // Score
            VStack(spacing: 0) {
                Text(score > 0 ? String(format: "%.2f", score) : "—")
                    .font(.system(size: 13, weight: .black, design: .monospaced))
                    .foregroundColor(scoreColor)
                Text("v3.1")
                    .font(.system(size: 7))
                    .foregroundColor(DSColors.textTertiary)
            }
            .padding(.horizontal, 7).padding(.vertical, 4)
            .background(scoreColor.opacity(0.12))
            .cornerRadius(5)
        }
    }

    var scoreColor: Color {
        if score >= 96 { return DSColors.violet }
        if score >= 93 { return DSColors.online }
        if score >= 90 { return DSColors.accentAmber }
        return DSColors.textSecondary
    }

    var trendColor: Color {
        switch history.trend {
        case .rising:  return DSColors.online
        case .falling: return DSColors.offline
        case .stable:  return DSColors.textTertiary
        }
    }
}

// MARK: — Sparkline

struct SparklineView: View {
    let points: [Double]

    var body: some View {
        GeometryReader { geo in
            let w = geo.size.width
            let h = geo.size.height
            let minV = (points.min() ?? 0) - 0.5
            let maxV = (points.max() ?? 100) + 0.5
            let range = maxV - minV

            if points.count >= 2 {
                Path { path in
                    for (i, v) in points.enumerated() {
                        let x = CGFloat(i) / CGFloat(points.count - 1) * w
                        let y = h - CGFloat((v - minV) / range) * h
                        if i == 0 { path.move(to: CGPoint(x: x, y: y)) }
                        else       { path.addLine(to: CGPoint(x: x, y: y)) }
                    }
                }
                .stroke(DSColors.violet.opacity(0.7), style: StrokeStyle(lineWidth: 1.5, lineCap: .round, lineJoin: .round))
            }
        }
    }
}
