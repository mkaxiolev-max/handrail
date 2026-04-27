import Foundation

/// NSMac runtime coverage manifest module.
/// Existence-level surface for FounderHome, LivingArchitecture,
/// VoicePanel, ScoreHistory, KeyboardHandler.
public enum NSMacComponent: String, CaseIterable {
    case founderHome        = "FounderHome"
    case livingArchitecture = "LivingArchitecture"
    case voicePanel         = "VoicePanel"
    case scoreHistory       = "ScoreHistory"
    case keyboardHandler    = "KeyboardHandler"
}

public struct NSMacRuntime {
    public static let version = "1.0"
    public static let components = NSMacComponent.allCases.map(\.rawValue)
    public static func componentExists(_ name: String) -> Bool {
        components.contains(name)
    }
}
