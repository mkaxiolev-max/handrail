import SwiftUI

struct LivingArchitectureView: View {
    @State private var selectedNode: OrganismNode?

    var body: some View {
        ZStack {
            DSColors.background

            // Metal organism canvas — fills the center, receives zoom/pan/click
            MetalOrganismView(selectedNode: $selectedNode)
                .ignoresSafeArea()

            // Constitutional boundary + privacy membrane (SwiftUI overlay layer)
            GeometryReader { geo in
                let W = geo.size.width
                let H = geo.size.height

                // Privacy membrane: translucent ring around Violet (NDC center)
                // Screen radius = NDC_radius * H * 0.38 (circle, both axes equal in screen space)
                let membraneR = H * 0.22 * 0.38
                Circle()
                    .stroke(DSColors.Spec.violet.opacity(0.18), lineWidth: 10)
                    .frame(width: membraneR * 2, height: membraneR * 2)
                    .position(x: W / 2, y: H / 2)
                    .allowsHitTesting(false)

                // Constitutional boundary: dashed ellipse enclosing chambers + adj + handrail + kernel + yubikey
                // Derived from NDC extents: x ∈ [-0.74, 0.44], y ∈ [-0.77, 0.50]
                // NDC center: (-0.15, -0.135), semi-axes: (0.59, 0.635)
                // Screen center: (0.443W, 0.551H), screen semi-axes: (0.224W, 0.241H)
                let ellipseW = W * 0.448
                let ellipseH = H * 0.482
                let ellipseCX = W * 0.443
                let ellipseCY = H * 0.551
                Ellipse()
                    .stroke(style: StrokeStyle(lineWidth: 1.5, dash: [7, 4]))
                    .foregroundColor(DSColors.Spec.violet.opacity(0.35))
                    .frame(width: ellipseW, height: ellipseH)
                    .position(x: ellipseCX, y: ellipseCY)
                    .allowsHitTesting(false)

                // Node labels
                ForEach(OrganismRenderer.canonicalNodes) { node in
                    let nx = CGFloat(node.position.x) * W * 0.38 + W / 2
                    let ny = (1 - CGFloat(node.position.y) * 0.38 - 0.5) * H
                    Text(node.label)
                        .font(.system(size: 9, weight: .semibold))
                        .foregroundColor(labelColor(node.role))
                        .position(x: nx, y: ny + CGFloat(node.radius) * H * 0.30 + 14)
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
        case .violet:       return DSColors.Spec.violet
        case .chamber:      return DSColors.Spec.chambers
        case .adjudication: return DSColors.Spec.adj
        case .handrail:     return DSColors.Spec.handrail
        case .alexandria:   return DSColors.Spec.alex
        case .kernel:       return DSColors.Spec.kernel
        case .founder:      return DSColors.Spec.founder
        case .programs:     return DSColors.Spec.build
        case .buildSpace:   return DSColors.Spec.build
        case .yubiKey:      return DSColors.online
        case .membrane:     return DSColors.Spec.violet.opacity(0.40)
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
        case .violet:       return DSColors.Spec.violet
        case .chamber:      return DSColors.Spec.chambers
        case .adjudication: return DSColors.Spec.adj
        case .handrail:     return DSColors.Spec.handrail
        case .alexandria:   return DSColors.Spec.alex
        case .kernel:       return DSColors.Spec.kernel
        case .founder:      return DSColors.Spec.founder
        case .programs:     return DSColors.Spec.build
        case .buildSpace:   return DSColors.Spec.build
        case .yubiKey:      return DSColors.online
        case .membrane:     return DSColors.Spec.violet.opacity(0.40)
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
        case .founder:      return "Founder — Principal Authority"
        case .programs:     return "Program Library — Runtime State"
        case .buildSpace:   return "Build Space — Exterior to Constitutional Boundary"
        case .yubiKey:      return "YubiKey — Hardware Quorum Gate"
        case .membrane:     return "Privacy Membrane — Violet Boundary"
        }
    }
}

#Preview {
    LivingArchitectureView()
        .frame(width: 900, height: 700)
        .preferredColorScheme(.dark)
}
