import AppKit
import SwiftUI

// Global keyboard shortcut handler — augments SwiftUI .commands with
// AppKit-level NSEvent monitoring for power-user bindings.
final class KeyboardHandler: ObservableObject {
    static let shared = KeyboardHandler()

    private var localMonitor: Any?
    private weak var appState: AppState?

    private init() {}

    func activate(appState: AppState) {
        self.appState = appState
        localMonitor = NSEvent.addLocalMonitorForEvents(matching: .keyDown) { [weak self] event in
            self?.handle(event: event) ?? event
        }
    }

    func deactivate() {
        if let m = localMonitor { NSEvent.removeMonitor(m) }
        localMonitor = nil
    }

    @discardableResult
    private func handle(event: NSEvent) -> NSEvent? {
        guard let appState else { return event }
        let cmd  = event.modifierFlags.contains(.command)
        let shift = event.modifierFlags.contains(.shift)

        // Cmd+1-6 → mode switch
        if cmd && !shift {
            switch event.charactersIgnoringModifiers {
            case "1": appState.currentMode = .founderHome;  return nil
            case "2": appState.currentMode = .livingArch;   return nil
            case "3": appState.currentMode = .engineRoom;   return nil
            case "4": appState.currentMode = .alexandria;   return nil
            case "5": appState.currentMode = .governance;   return nil
            case "6": appState.currentMode = .buildSpace;   return nil
            // Cmd+V → toggle voice overlay (don't intercept paste — only when no text field focused)
            case "v":
                if NSApp.keyWindow?.firstResponder is NSTextView { return event }
                appState.voiceState = appState.voiceState == .dormant ? .ready : .dormant
                return nil
            // Cmd+R → force refresh
            case "r":
                return nil  // HealthPoller handles this via its timer; consume to avoid system reload
            default: break
            }
        }
        return event
    }
}
