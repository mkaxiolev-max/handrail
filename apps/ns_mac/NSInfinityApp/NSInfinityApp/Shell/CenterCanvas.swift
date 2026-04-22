import SwiftUI

// CenterCanvas is intentionally minimal — mode routing lives in AppShell
// to enable proper animated transitions via .id(currentMode) + .transition()
struct CenterCanvas: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        // Routing is handled in AppShell.modeContent — this view is a transparent pass-through
        // kept for future overlay/ambient decoration at the canvas layer
        Color.clear
    }
}
