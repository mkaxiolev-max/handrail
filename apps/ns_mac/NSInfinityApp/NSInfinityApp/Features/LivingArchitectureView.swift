import SwiftUI

struct LivingArchitectureView: View {
    @State private var selectedNode: OrganismNode?

    var body: some View {
        ZStack {
            DSColors.background

            // Metal organism canvas — fills the center, receives zoom/pan/click
            MetalOrganismView(selectedNode: $selectedNode)
                .ignoresSafeArea()

            // Node labels overlaid in SwiftUI coordinate space
            GeometryReader { geo in
                ForEach(OrganismRenderer.canonicalNodes) { node in
                    let nx = CGFloat(node.position.x) * geo.size.width  * 0.38 + geo.size.width  / 2
                    let ny = (1 - CGFloat(node.position.y) * 0.38 - 0.5) * geo.size.height
                    Text(node.label)
                        .font(.system(size: 9, weight: .semibold))
                        .foregroundColor(labelColor(node.role))
                        .position(x: nx, y: ny + CGFloat(node.radius) * geo.size.height * 0.30 + 14)
                        .allowsHitTesting(false)
                }
            }

            // Selected node detail panel — bottom left
            if let node = selectedNode {
                NodeDetailPanel(node: node, onDismiss: { selectedNode = nil })
                    .padding(20)
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottomLeading)
                    .transition(.asymmetric(
                        insertion: .opacity.combined(with: .move(edge: .bottom)),
                        removal:   .opacity
                    ))
                    .animation(.spring(response: 0.28, dampingFraction: 0.80), value: selectedNode?.id)
            }

            // Camera hint
            VStack {
                HStack {
                    Spacer()
                    HStack(spacing: 8) {
                        Label("Pinch to zoom", systemImage: "plus.magnifyingglass")
                        Label("Drag to pan",   systemImage: "hand.draw")
                        Label("Click node",    systemImage: "cursorarrow.click")
                    }
                    .font(.system(size: 9))
                    .foregroundColor(DSColors.textTertiary)
                    .padding(.horizontal, 10).padding(.vertical, 5)
                    .background(DSColors.surfaceCard.opacity(0.8))
                    .cornerRadius(6)
                    .padding(16)
                }
                Spacer()
            }
        }
        .animation(.spring(response: 0.25, dampingFraction: 0.85), value: selectedNode?.id)
    }

    func labelColor(_ role: OrganismNode.NodeRole) -> Color {
        switch role {
        case .violet:       return DSColors.violet
        case .chamber:      return DSColors.accentCyan
        case .adjudication: return DSColors.accentAmber
        case .handrail:     return DSColors.online
        case .alexandria:   return DSColors.accentCyan
        case .kernel:       return DSColors.offline
        case .membrane:     return DSColors.violetDim
        }
    }
}

private struct NodeDetailPanel: View {
    let node: OrganismNode
    let onDismiss: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Circle().fill(nodeColor).frame(width: 8, height: 8)
                Text(node.label)
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(DSColors.textPrimary)
                Spacer()
                Button { onDismiss() } label: {
                    Image(systemName: "xmark")
                        .font(.system(size: 9))
                        .foregroundColor(DSColors.textTertiary)
                }.buttonStyle(.plain)
            }
            Text(node.role.description)
                .font(.system(size: 11))
                .foregroundColor(DSColors.textSecondary)
            Text(node.id)
                .font(.system(size: 9, design: .monospaced))
                .foregroundColor(DSColors.textTertiary)
        }
        .padding(14)
        .frame(width: 260)
        .background(DSColors.surfaceCard.opacity(0.97))
        .cornerRadius(10)
        .overlay(RoundedRectangle(cornerRadius: 10).stroke(nodeColor.opacity(0.35), lineWidth: 1))
        .shadow(color: nodeColor.opacity(0.12), radius: 16)
    }

    var nodeColor: Color {
        switch node.role {
        case .violet:       return DSColors.violet
        case .chamber:      return DSColors.accentCyan
        case .adjudication: return DSColors.accentAmber
        case .handrail:     return DSColors.online
        case .alexandria:   return DSColors.accentCyan
        case .kernel:       return DSColors.offline
        case .membrane:     return DSColors.violetDim
        }
    }
}

extension OrganismNode.NodeRole: CustomStringConvertible {
    public var description: String {
        switch self {
        case .violet:       return "Relational Shell — Constitutional AI OS"
        case .chamber:      return "Plural Cognition Chamber"
        case .adjudication: return "Lawful Selector — Adjudication Engine"
        case .handrail:     return "Deterministic Execution — CPS Gate"
        case .alexandria:   return "Continuity Spine — Knowledge Reality"
        case .kernel:       return "Boundary & Safety — Dignity Kernel"
        case .membrane:     return "Privacy Membrane"
        }
    }
}

#Preview {
    LivingArchitectureView()
        .frame(width: 900, height: 700)
        .preferredColorScheme(.dark)
}
