import SwiftUI

@main
struct NSFounderCockpitApp: App {
    @StateObject private var appState = AppState()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(appState)
                .frame(minWidth: 1200, minHeight: 750)
        }
        .commands {
            CommandGroup(replacing: .newItem) {}
        }
    }
}
