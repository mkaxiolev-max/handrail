import SwiftUI

struct SidebarView: View {
    @Binding var selected: Panel
    @EnvironmentObject var appState: AppState

    var healthDot: Color {
        let allUp = appState.services.filter { $0.isUp }.count
        let total = appState.services.count
        if total == 0 { return .gray }
        if allUp == total { return .green }
        if allUp > total / 2 { return .yellow }
        return .red
    }

    var body: some View {
        List(Panel.allCases, selection: $selected) { panel in
            Label(panel.rawValue, systemImage: panel.icon)
                .tag(panel)
        }
        .listStyle(.sidebar)
        .navigationSplitViewColumnWidth(180)
        .safeAreaInset(edge: .bottom) {
            HStack {
                Circle()
                    .fill(healthDot)
                    .frame(width: 8, height: 8)
                Text(appState.lastRefresh.map { "Last: \(Self.fmt($0))" } ?? "Never")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
            .padding(8)
        }
    }

    private static func fmt(_ date: Date) -> String {
        let f = DateFormatter()
        f.dateFormat = "HH:mm:ss"
        return f.string(from: date)
    }
}
