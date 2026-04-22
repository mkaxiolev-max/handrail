import SwiftUI
import AppKit

@main
struct NSInfinityApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    @StateObject private var appState = AppState.shared

    var body: some Scene {
        WindowGroup("NS∞ Founder Habitat") {
            AppShell()
                .environmentObject(appState)
                .frame(minWidth: 1280, minHeight: 800)
        }
        .windowStyle(.hiddenTitleBar)
        .windowToolbarStyle(.unified(showsTitle: false))
        .commands {
            NSInfinityCommands()
        }
    }
}

struct NSInfinityCommands: Commands {
    var body: some Commands {
        CommandGroup(replacing: .newItem) {}
        CommandMenu("Habitat") {
            Button("Founder Home") {}
                .keyboardShortcut("1", modifiers: .command)
            Button("Living Architecture") {}
                .keyboardShortcut("2", modifiers: .command)
            Button("Engine Room") {}
                .keyboardShortcut("3", modifiers: .command)
            Button("Alexandria") {}
                .keyboardShortcut("4", modifiers: .command)
            Button("Governance") {}
                .keyboardShortcut("5", modifiers: .command)
            Button("Build Space") {}
                .keyboardShortcut("6", modifiers: .command)
        }
    }
}
