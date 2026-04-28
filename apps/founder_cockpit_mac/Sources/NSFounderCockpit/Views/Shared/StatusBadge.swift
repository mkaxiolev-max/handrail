import SwiftUI

struct StatusBadge: View {
    let label: String
    let isUp: Bool

    var body: some View {
        HStack(spacing: 4) {
            Circle()
                .fill(isUp ? Color.green : Color.red)
                .frame(width: 8, height: 8)
            Text(label)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }
}

struct VerbBadge: View {
    let verb: String

    var color: Color {
        switch verb {
        case "collapse_ready":      return .green
        case "hold_ncom":           return .yellow
        case "force_more_branches": return .orange
        default:                    return .red
        }
    }

    var body: some View {
        Text(verb)
            .font(.caption.monospaced())
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(color.opacity(0.2))
            .foregroundStyle(color)
            .clipShape(RoundedRectangle(cornerRadius: 4))
    }
}

struct SectionHeader: View {
    let title: String
    var body: some View {
        Text(title)
            .font(.headline)
            .padding(.top, 8)
    }
}
