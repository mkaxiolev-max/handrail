import SwiftUI

enum Panel: String, CaseIterable, Identifiable {
    case command     = "Command"
    case reality     = "Reality"
    case canon       = "Canon"
    case contradictions = "Contradictions"
    case memory      = "Memory"
    case storytime   = "Storytime"
    case coherence   = "Coherence"
    case system      = "System"
    case score       = "Score"

    var id: String { rawValue }

    var icon: String {
        switch self {
        case .command:        return "terminal.fill"
        case .reality:        return "eye.fill"
        case .canon:          return "checkmark.seal.fill"
        case .contradictions: return "exclamationmark.triangle.fill"
        case .memory:         return "brain.head.profile"
        case .storytime:      return "text.bubble.fill"
        case .coherence:      return "waveform.path.ecg"
        case .system:         return "server.rack"
        case .score:          return "chart.bar.fill"
        }
    }
}

struct RootView: View {
    @EnvironmentObject var appState: AppState
    @State private var selectedPanel: Panel = .command

    var body: some View {
        NavigationSplitView {
            SidebarView(selected: $selectedPanel)
        } detail: {
            Group {
                switch selectedPanel {
                case .command:        CommandPanelView()
                case .reality:        RealityPanelView()
                case .canon:          CanonPanelView()
                case .contradictions: ContradictionsPanelView()
                case .memory:         MemoryPanelView()
                case .storytime:      StorytimePanelView()
                case .coherence:      CoherencePanelView()
                case .system:         SystemPanelView()
                case .score:          ScorePanelView()
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .onAppear { appState.startPolling() }
        .onDisappear { appState.stopPolling() }
    }
}
