import Metal
import MetalKit
import simd

struct OrganismNode: Identifiable, Equatable {
    let id: String
    let label: String
    let role: NodeRole
    var position: SIMD2<Float>
    var radius: Float
    var isActive: Bool

    enum NodeRole {
        case violet, chamber, adjudication, handrail, alexandria, kernel, membrane
    }
}

struct Vertex {
    var position: SIMD2<Float>
    var color: SIMD4<Float>
}

final class OrganismRenderer: NSObject, MTKViewDelegate {
    var onNodeSelected: ((OrganismNode) -> Void)?

    private let device: MTLDevice
    private var commandQueue: MTLCommandQueue!
    private var pipelineState: MTLRenderPipelineState!
    private var vertexBuffer: MTLBuffer!
    private var nodes: [OrganismNode]
    private var time: Float = 0

    // Camera state
    private var zoom: Float = 1.0
    private var panOffset: SIMD2<Float> = .zero
    private var selectedNodeID: String? = nil

    static let canonicalNodes: [OrganismNode] = [
        OrganismNode(id: "violet",       label: "Violet",       role: .violet,       position: SIMD2(0, 0),         radius: 0.12, isActive: true),
        OrganismNode(id: "ch1",          label: "Arbiter",      role: .chamber,      position: SIMD2(-0.35, 0.20),  radius: 0.07, isActive: true),
        OrganismNode(id: "ch2",          label: "Voice",        role: .chamber,      position: SIMD2(0.35, 0.20),   radius: 0.07, isActive: true),
        OrganismNode(id: "ch3",          label: "Ether",        role: .chamber,      position: SIMD2(0, 0.42),      radius: 0.07, isActive: true),
        OrganismNode(id: "ch4",          label: "SAN",          role: .chamber,      position: SIMD2(-0.35, -0.20), radius: 0.07, isActive: true),
        OrganismNode(id: "ch5",          label: "Semantic",     role: .chamber,      position: SIMD2(0.35, -0.20),  radius: 0.07, isActive: true),
        OrganismNode(id: "adjudication", label: "Adjudication", role: .adjudication, position: SIMD2(0, -0.42),     radius: 0.08, isActive: true),
        OrganismNode(id: "handrail",     label: "Handrail",     role: .handrail,     position: SIMD2(-0.65, 0),     radius: 0.09, isActive: true),
        OrganismNode(id: "alexandria",   label: "Alexandria",   role: .alexandria,   position: SIMD2(0.65, 0),      radius: 0.09, isActive: true),
        OrganismNode(id: "kernel",       label: "Kernel",       role: .kernel,       position: SIMD2(0, -0.70),     radius: 0.07, isActive: true),
        OrganismNode(id: "membrane",     label: "Membrane",     role: .membrane,     position: SIMD2(0, 0.70),      radius: 0.07, isActive: true),
    ]

    init?(mtkView: MTKView) {
        guard let device = mtkView.device else { return nil }
        self.device = device
        self.nodes = OrganismRenderer.canonicalNodes
        super.init()
        commandQueue = device.makeCommandQueue()
        buildPipeline(mtkView: mtkView)
    }

    // MARK: — Camera controls

    func adjustZoom(delta: Float) {
        zoom = max(0.3, min(4.0, zoom + delta * zoom))
    }

    func adjustPan(dx: Float, dy: Float) {
        panOffset += SIMD2(dx / zoom, dy / zoom)
    }

    // MARK: — Hit testing

    func hitTest(ndc: SIMD2<Float>) {
        // Transform NDC back through camera to world space
        let worldX = (ndc.x / zoom) - panOffset.x
        let worldY = (ndc.y / zoom) - panOffset.y
        let worldPt = SIMD2<Float>(worldX, worldY)

        for node in nodes {
            let dist = length(worldPt - node.position)
            // Generous hit radius: node.radius * 1.5 for finger-sized targets
            if dist < node.radius * 1.5 {
                selectedNodeID = node.id
                onNodeSelected?(node)
                return
            }
        }
        selectedNodeID = nil
    }

    // MARK: — Pipeline

    private func buildPipeline(mtkView: MTKView) {
        let library = device.makeDefaultLibrary()
        let vertexFn   = library?.makeFunction(name: "organism_vertex")
        let fragmentFn = library?.makeFunction(name: "organism_fragment")

        let desc = MTLRenderPipelineDescriptor()
        desc.vertexFunction   = vertexFn
        desc.fragmentFunction = fragmentFn
        desc.colorAttachments[0].pixelFormat = mtkView.colorPixelFormat
        desc.colorAttachments[0].isBlendingEnabled = true
        desc.colorAttachments[0].sourceRGBBlendFactor      = .sourceAlpha
        desc.colorAttachments[0].destinationRGBBlendFactor  = .oneMinusSourceAlpha
        desc.colorAttachments[0].sourceAlphaBlendFactor     = .one
        desc.colorAttachments[0].destinationAlphaBlendFactor = .oneMinusSourceAlpha

        pipelineState = try? device.makeRenderPipelineState(descriptor: desc)
    }

    // MARK: — MTKViewDelegate

    func mtkView(_ view: MTKView, drawableSizeWillChange size: CGSize) {}

    func draw(in view: MTKView) {
        guard let pipelineState,
              let drawable = view.currentDrawable,
              let descriptor = view.currentRenderPassDescriptor,
              let commandBuffer = commandQueue.makeCommandBuffer(),
              let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: descriptor)
        else { return }

        time += 0.016
        let vertices = buildVertices(viewSize: view.drawableSize)
        let byteLen = MemoryLayout<Vertex>.stride * vertices.count
        vertexBuffer = device.makeBuffer(bytes: vertices, length: byteLen, options: [])

        encoder.setRenderPipelineState(pipelineState)
        encoder.setVertexBuffer(vertexBuffer, offset: 0, index: 0)

        var uniforms = CameraUniforms(zoom: zoom, pan: panOffset, time: time)
        encoder.setVertexBytes(&uniforms, length: MemoryLayout<CameraUniforms>.stride, index: 1)
        encoder.drawPrimitives(type: .triangle, vertexStart: 0, vertexCount: vertices.count)
        encoder.endEncoding()

        commandBuffer.present(drawable)
        commandBuffer.commit()
    }

    private func buildVertices(viewSize: CGSize) -> [Vertex] {
        var verts: [Vertex] = []
        let aspect = Float(viewSize.width / max(viewSize.height, 1))

        // Draw connections
        for node in nodes where node.id != "violet" {
            let center = nodes.first(where: { $0.id == "violet" })!
            let alpha: Float = node.id == selectedNodeID ? 0.7 : 0.2
            let color = nodeColor(node).opacity(alpha)
            verts.append(contentsOf: makeLink(from: center.position, to: node.position,
                                               width: 0.004, aspect: aspect, color: color))
        }

        // Draw node circles
        for node in nodes {
            let isSelected = node.id == selectedNodeID
            let baseColor = nodeColor(node)
            let fillColor = isSelected ? baseColor.opacity(1.0) : baseColor.opacity(0.75)
            let pulse = node.id == "violet" ? 0.025 * sin(time * 2.1) : 0
            let highlightBoost: Float = isSelected ? 0.02 : 0

            verts.append(contentsOf: makeCircle(
                center: node.position,
                radius: node.radius + pulse + highlightBoost,
                aspect: aspect, color: fillColor, segments: 40
            ))

            // Selection ring
            if isSelected {
                verts.append(contentsOf: makeRing(
                    center: node.position,
                    radius: node.radius + 0.025,
                    aspect: aspect, color: baseColor.opacity(0.9),
                    lineWidth: 0.006, segments: 40
                ))
            }
        }
        return verts
    }

    private func nodeColor(_ node: OrganismNode) -> SIMD4<Float> {
        switch node.role {
        case .violet:       return SIMD4(0.56, 0.35, 0.95, 1.0)
        case .chamber:      return SIMD4(0.10, 0.90, 0.90, 0.85)
        case .adjudication: return SIMD4(0.95, 0.75, 0.10, 0.90)
        case .handrail:     return SIMD4(0.20, 0.85, 0.45, 0.90)
        case .alexandria:   return SIMD4(0.10, 0.65, 0.95, 0.90)
        case .kernel:       return SIMD4(0.95, 0.25, 0.45, 0.90)
        case .membrane:     return SIMD4(0.75, 0.55, 0.95, 0.80)
        }
    }

    private func makeCircle(center: SIMD2<Float>, radius: Float, aspect: Float,
                             color: SIMD4<Float>, segments: Int) -> [Vertex] {
        var verts: [Vertex] = []
        let step = (2.0 * Float.pi) / Float(segments)
        for i in 0..<segments {
            let a0 = Float(i) * step
            let a1 = Float(i + 1) * step
            let cx = SIMD2<Float>(center.x, center.y)
            let p0 = cx + SIMD2(cos(a0) * radius / aspect, sin(a0) * radius)
            let p1 = cx + SIMD2(cos(a1) * radius / aspect, sin(a1) * radius)
            verts.append(Vertex(position: cx, color: color))
            verts.append(Vertex(position: p0, color: color.opacity(0.55)))
            verts.append(Vertex(position: p1, color: color.opacity(0.55)))
        }
        return verts
    }

    private func makeRing(center: SIMD2<Float>, radius: Float, aspect: Float,
                           color: SIMD4<Float>, lineWidth: Float, segments: Int) -> [Vertex] {
        var verts: [Vertex] = []
        let step = (2.0 * Float.pi) / Float(segments)
        let r0 = radius - lineWidth * 0.5
        let r1 = radius + lineWidth * 0.5
        for i in 0..<segments {
            let a0 = Float(i) * step
            let a1 = Float(i + 1) * step
            let p00 = center + SIMD2(cos(a0) * r0 / aspect, sin(a0) * r0)
            let p01 = center + SIMD2(cos(a0) * r1 / aspect, sin(a0) * r1)
            let p10 = center + SIMD2(cos(a1) * r0 / aspect, sin(a1) * r0)
            let p11 = center + SIMD2(cos(a1) * r1 / aspect, sin(a1) * r1)
            verts.append(Vertex(position: p00, color: color))
            verts.append(Vertex(position: p01, color: color))
            verts.append(Vertex(position: p10, color: color))
            verts.append(Vertex(position: p01, color: color))
            verts.append(Vertex(position: p11, color: color))
            verts.append(Vertex(position: p10, color: color))
        }
        return verts
    }

    private func makeLink(from a: SIMD2<Float>, to b: SIMD2<Float>, width: Float,
                           aspect: Float, color: SIMD4<Float>) -> [Vertex] {
        let dir = normalize(b - a)
        let perp = SIMD2<Float>(-dir.y, dir.x) * SIMD2(width / aspect, width)
        let p0 = a + perp; let p1 = a - perp
        let p2 = b + perp; let p3 = b - perp
        return [
            Vertex(position: p0, color: color), Vertex(position: p1, color: color), Vertex(position: p2, color: color),
            Vertex(position: p1, color: color), Vertex(position: p3, color: color), Vertex(position: p2, color: color),
        ]
    }
}

struct CameraUniforms {
    var zoom: Float
    var pan: SIMD2<Float>
    var time: Float
}

private extension SIMD4 where Scalar == Float {
    func opacity(_ a: Float) -> SIMD4<Float> { SIMD4(x, y, z, a) }
}
