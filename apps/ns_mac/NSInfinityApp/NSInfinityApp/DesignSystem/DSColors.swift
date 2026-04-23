import SwiftUI

enum DSColors {
    // Canonical Living Architecture spec tokens (ground truth — exact hex)
    enum Spec {
        static let violet   = Color(red: 0.000, green: 0.831, blue: 1.000)  // #00D4FF
        static let founder  = Color(red: 1.000, green: 0.420, blue: 0.000)  // #FF6B00
        static let chambers = Color(red: 0.420, green: 0.000, blue: 1.000)  // #6B00FF
        static let adj      = Color(red: 0.000, green: 1.000, blue: 0.533)  // #00FF88
        static let handrail = Color(red: 0.000, green: 1.000, blue: 1.000)  // #00FFFF
        static let alex     = Color(red: 1.000, green: 1.000, blue: 0.000)  // #FFFF00
        static let kernel   = Color(red: 1.000, green: 0.200, blue: 0.200)  // #FF3333
        static let build    = Color(red: 0.290, green: 0.435, blue: 0.647)  // #4A6FA5
        static let bg       = Color(red: 0.039, green: 0.055, blue: 0.153)  // #0A0E27
    }

    // Violet system — relational shell (UI accent; see Spec.violet for org-map node color)
    static let violet          = Color(red: 0.56, green: 0.35, blue: 0.95)
    static let violetDim       = Color(red: 0.56, green: 0.35, blue: 0.95, opacity: 0.35)
    static let violetFaint     = Color(red: 0.56, green: 0.35, blue: 0.95, opacity: 0.10)

    // Surface system
    static let background      = Color(red: 0.039, green: 0.055, blue: 0.153)  // #0A0E27
    static let surfaceElevated = Color(red: 0.09, green: 0.09, blue: 0.12)
    static let surfaceCard     = Color(red: 0.11, green: 0.11, blue: 0.15)
    static let surfaceBorder   = Color(red: 0.20, green: 0.20, blue: 0.28)

    // Status
    static let online          = Color(red: 0.20, green: 0.85, blue: 0.45)
    static let offline         = Color(red: 0.85, green: 0.25, blue: 0.25)
    static let degraded        = Color(red: 0.95, green: 0.65, blue: 0.10)
    static let blocked         = Color(red: 0.85, green: 0.25, blue: 0.25)
    static let complete        = Color(red: 0.20, green: 0.85, blue: 0.45)

    // Typography
    static let textPrimary     = Color.white
    static let textSecondary   = Color(white: 0.65)
    static let textTertiary    = Color(white: 0.40)

    // Accent
    static let accentCyan      = Color(red: 0.10, green: 0.90, blue: 0.90)
    static let accentAmber     = Color(red: 0.95, green: 0.75, blue: 0.10)

    // Semantic voice/state colors
    enum Semantic {
        case inactive, active, alert, processing, responding

        var color: Color {
            switch self {
            case .inactive:   return DSColors.textTertiary
            case .active:     return DSColors.online
            case .alert:      return DSColors.accentAmber
            case .processing: return DSColors.accentCyan
            case .responding: return DSColors.violet
            }
        }
    }
}

// MARK: — Typography helpers

extension Font {
    // SF Pro Display — fallback to .system if SF Pro Display is unavailable
    static func displayBlack(_ size: CGFloat) -> Font {
        Font.custom("SFProDisplay-Black", size: size).bold()
    }
    static func displayBold(_ size: CGFloat) -> Font {
        Font.custom("SFProDisplay-Bold", size: size)
    }
    static func displayRegular(_ size: CGFloat) -> Font {
        Font.custom("SFProDisplay-Regular", size: size)
    }

    static func habitatTitle() -> Font {
        .system(size: 28, weight: .black, design: .default)
    }
    static func habitatSection() -> Font {
        .system(size: 10, weight: .semibold, design: .default)
    }
    static func habitatMono(_ size: CGFloat = 11) -> Font {
        .system(size: size, design: .monospaced)
    }
    static func habitatCaption() -> Font {
        .system(size: 9, design: .default)
    }
}

extension Color {
    static let dsBackground      = DSColors.background
    static let dsSurface         = DSColors.surfaceElevated
    static let dsCard            = DSColors.surfaceCard
    static let dsBorder          = DSColors.surfaceBorder
    static let dsViolet          = DSColors.violet
    static let dsOnline          = DSColors.online
    static let dsOffline         = DSColors.offline
}
