import Metal
import MetalKit
import simd

// ── Domain types ──────────────────────────────────────────────────────────────

struct OrganismNode: Identifiable, Equatable {
    let id: String
    let label: String
    let role: NodeRole
    var position: SIMD2<Float>
    var radius: Float
    var isActive: Bool

    enum NodeRole {
        case violet, chamber, adjudication, handrail, alexandria, kernel, membrane
        case founder, programs, yubiKey, buildSpace
    }
}

struct Vertex {
    var position: SIMD2<Float>
    var color: SIMD4<Float>
}

struct CameraUniforms {
    var zoom: Float
    var pan: SIMD2<Float>
    var time: Float
}

struct ParticleUniforms {
    var time: Float
    var resolution: SIMD2<Float>
    var zoom: Float
    var pan: SIMD2<Float>
}

// ── NodeOverlayState: governance/stress/memory-pressure ─────────────────────

struct NodeOverlayState {
    var stress: Float        = 0   // 0–1 — red pulse
    var governance: Float    = 0   // 0–1 — amber halo
    var memoryPressure: Float = 0  // 0–1 — blue desaturate
    var executionReady: Float = 1  // 0–1 — green ring brightens
}

// ── Design token bridge (Metal SIMD4 mirror of DSColors.Spec) ────────────────

struct DesignTokenSIMD {
    static let violet:   SIMD4<Float> = SIMD4(0.000, 0.831, 1.000, 1.00)  // #00D4FF
    static let chamber:  SIMD4<Float> = SIMD4(0.420, 0.000, 1.000, 0.85)  // #6B00FF
    static let adj:      SIMD4<Float> = SIMD4(0.000, 1.000, 0.533, 0.90)  // #00FF88
    static let handrail: SIMD4<Float> = SIMD4(0.000, 1.000, 1.000, 0.90)  // #00FFFF
    static let alex:     SIMD4<Float> = SIMD4(1.000, 1.000, 0.000, 0.90)  // #FFFF00
    static let kernel:   SIMD4<Float> = SIMD4(1.000, 0.200, 0.200, 0.90)  // #FF3333
    static let founder:  SIMD4<Float> = SIMD4(1.000, 0.420, 0.000, 0.90)  // #FF6B00
    static let build:    SIMD4<Float> = SIMD4(0.290, 0.435, 0.647, 0.85)  // #4A6FA5
    static let bg:       SIMD4<Float> = SIMD4(0.039, 0.055, 0.153, 1.00)  // #0A0E27
    static let yubiKey:  SIMD4<Float> = SIMD4(0.000, 1.000, 1.000, 0.85)  // #00FFFF
    static let membrane: SIMD4<Float> = SIMD4(0.000, 0.831, 1.000, 0.30)  // #00D4FF faint
}

// ── OrganismRenderer ─────────────────────────────────────────────────────────

final class OrganismRenderer: NSObject, MTKViewDelegate {
    var onNodeSelected: ((OrganismNode) -> Void)?

    private let device: MTLDevice
    private var commandQueue: MTLCommandQueue!
    private var pipelineState: MTLRenderPipelineState!
    private var particlePipeline: MTLRenderPipelineState!
    private var vertexBuffer: MTLBuffer!
    private var nodes: [OrganismNode]
    private var time: Float = 0

    // Camera state
    private var zoom: Float = 1.0
    private var panOffset: SIMD2<Float> = .zero
    private var selectedNodeID: String? = nil

    // Overlay states keyed by node id
    var overlayStates: [String: NodeOverlayState] = [:]

    // ── Canonical topology ───────────────────────────────────────────────────

    static let canonicalNodes: [OrganismNode] = [
        // Core
        OrganismNode(id: "violet",       label: "Violet",       role: .violet,       position: SIMD2(0, 0),          radius: 0.12, isActive: true),
        // Five chambers — Forge, Institute, Board, Omega, Registry
        OrganismNode(id: "ch1",          label: "Institute",    role: .chamber,      position: SIMD2(-0.35, 0.20),   radius: 0.07, isActive: true),
        OrganismNode(id: "ch2",          label: "Board",        role: .chamber,      position: SIMD2(0.35, 0.20),    radius: 0.07, isActive: true),
        OrganismNode(id: "ch3",          label: "Forge",        role: .chamber,      position: SIMD2(0, 0.42),       radius: 0.07, isActive: true),
        OrganismNode(id: "ch4",          label: "Omega",        role: .chamber,      position: SIMD2(-0.35, -0.20),  radius: 0.07, isActive: true),
        OrganismNode(id: "ch5",          label: "Registry",     role: .chamber,      position: SIMD2(0.35, -0.20),   radius: 0.07, isActive: true),
        // Constitutional interior
        OrganismNode(id: "adjudication", label: "Adjudication", role: .adjudication, position: SIMD2(0, -0.42),      radius: 0.08, isActive: true),
        OrganismNode(id: "handrail",     label: "Handrail",     role: .handrail,     position: SIMD2(-0.65, 0),      radius: 0.09, isActive: true),
        OrganismNode(id: "kernel",       label: "Kernel",       role: .kernel,       position: SIMD2(0, -0.70),      radius: 0.07, isActive: true),
        OrganismNode(id: "yubikey",      label: "YubiKey",      role: .yubiKey,      position: SIMD2(0.15, -0.50),   radius: 0.05, isActive: true),
        // Constitutional exterior
        OrganismNode(id: "alexandria",   label: "Alexandria",   role: .alexandria,   position: SIMD2(0.65, 0),       radius: 0.09, isActive: true),
        OrganismNode(id: "programs",     label: "Programs",     role: .programs,     position: SIMD2(0.75, 0.45),    radius: 0.06, isActive: true),
        OrganismNode(id: "buildspace",   label: "Build Space",  role: .buildSpace,   position: SIMD2(0.80, -0.55),   radius: 0.06, isActive: true),
        OrganismNode(id: "founder",      label: "Founder",      role: .founder,      position: SIMD2(-0.78, 0.62),   radius: 0.06, isActive: true),
        OrganismNode(id: "membrane",     label: "Membrane",     role: .membrane,     position: SIMD2(0, 0.70),       radius: 0.05, isActive: true),
    ]

    // ── Init ─────────────────────────────────────────────────────────────────

    init?(mtkView: MTKView) {
        guard let device = mtkView.device else { return nil }
        self.device = device
        self.nodes = OrganismRenderer.canonicalNodes
        super.init()
        commandQueue = device.makeCommandQueue()
        buildPipelines(mtkView: mtkView)
    }

    // ── Camera controls ──────────────────────────────────────────────────────

    func adjustZoom(delta: Float) {
        zoom = max(0.25, min(5.0, zoom + delta * zoom))
    }

    func adjustPan(dx: Float, dy: Float) {
        panOffset += SIMD2(dx / zoom, dy / zoom)
    }

    func resetCamera() {
        zoom = 1.0; panOffset = .zero
    }

    // ── Hit testing ──────────────────────────────────────────────────────────

    func hitTest(ndc: SIMD2<Float>) {
        let worldX = (ndc.x / zoom) - panOffset.x
        let worldY = (ndc.y / zoom) - panOffset.y
        let pt = SIMD2<Float>(worldX, worldY)
        for node in nodes {
            if length(pt - node.position) < node.radius * 1.6 {
                selectedNodeID = node.id
                onNodeSelected?(node)
                return
            }
        }
        selectedNodeID = nil
    }

    // ── Pipeline ─────────────────────────────────────────────────────────────

    private func buildPipelines(mtkView: MTKView) {
        guard let library = device.makeDefaultLibrary() else { return }

        // Organism pipeline
        let vFn = library.makeFunction(name: "organism_vertex")
        let fFn = library.makeFunction(name: "organism_fragment")
        let orgDesc = MTLRenderPipelineDescriptor()
        orgDesc.vertexFunction   = vFn
        orgDesc.fragmentFunction = fFn
        orgDesc.colorAttachments[0].pixelFormat = mtkView.colorPixelFormat
        blendAlpha(orgDesc.colorAttachments[0])
        pipelineState = try? device.makeRenderPipelineState(descriptor: orgDesc)

        // Particle pipeline
        let pvFn = library.makeFunction(name: "particle_vertex")
        let pfFn = library.makeFunction(name: "particle_fragment")
        let ptDesc = MTLRenderPipelineDescriptor()
        ptDesc.vertexFunction   = pvFn
        ptDesc.fragmentFunction = pfFn
        ptDesc.colorAttachments[0].pixelFormat = mtkView.colorPixelFormat
        blendAlpha(ptDesc.colorAttachments[0])
        particlePipeline = try? device.makeRenderPipelineState(descriptor: ptDesc)
    }

    private func blendAlpha(_ att: MTLRenderPipelineColorAttachmentDescriptor) {
        att.isBlendingEnabled              = true
        att.sourceRGBBlendFactor           = .sourceAlpha
        att.destinationRGBBlendFactor       = .oneMinusSourceAlpha
        att.sourceAlphaBlendFactor         = .one
        att.destinationAlphaBlendFactor     = .oneMinusSourceAlpha
    }

    // ── MTKViewDelegate ──────────────────────────────────────────────────────

    func mtkView(_ view: MTKView, drawableSizeWillChange size: CGSize) {}

    func draw(in view: MTKView) {
        guard let pipelineState, let particlePipeline,
              let drawable    = view.currentDrawable,
              let descriptor  = view.currentRenderPassDescriptor,
              let cmdBuf      = commandQueue.makeCommandBuffer(),
              let encoder     = cmdBuf.makeRenderCommandEncoder(descriptor: descriptor)
        else { return }

        time += 0.016
        let size = view.drawableSize

        // 1. Particle field (background layer)
        drawParticles(encoder: encoder, viewSize: size, particleCount: 280)

        // 2. Organism
        drawOrganism(encoder: encoder, viewSize: size)

        encoder.endEncoding()
        cmdBuf.present(drawable)
        cmdBuf.commit()
    }

    // ── Particle pass ─────────────────────────────────────────────────────────

    private func drawParticles(encoder: MTLRenderCommandEncoder, viewSize: CGSize, particleCount: Int) {
        guard let particlePipeline else { return }
        encoder.setRenderPipelineState(particlePipeline)
        var uniforms = ParticleUniforms(
            time: time,
            resolution: SIMD2(Float(viewSize.width), Float(viewSize.height)),
            zoom: zoom,
            pan: panOffset
        )
        encoder.setVertexBytes(&uniforms, length: MemoryLayout<ParticleUniforms>.stride, index: 0)
        encoder.drawPrimitives(type: .point, vertexStart: 0, vertexCount: particleCount)
    }

    // ── Organism pass ─────────────────────────────────────────────────────────

    private func drawOrganism(encoder: MTLRenderCommandEncoder, viewSize: CGSize) {
        guard let pipelineState else { return }
        let aspect = Float(viewSize.width / max(viewSize.height, 1))
        let verts = buildVertices(aspect: aspect)
        let byteLen = MemoryLayout<Vertex>.stride * verts.count
        vertexBuffer = device.makeBuffer(bytes: verts, length: byteLen, options: [])

        encoder.setRenderPipelineState(pipelineState)
        encoder.setVertexBuffer(vertexBuffer, offset: 0, index: 0)
        var cam = CameraUniforms(zoom: zoom, pan: panOffset, time: time)
        encoder.setVertexBytes(&cam, length: MemoryLayout<CameraUniforms>.stride, index: 1)
        encoder.drawPrimitives(type: .triangle, vertexStart: 0, vertexCount: verts.count)
    }

    // ── Vertex construction ──────────────────────────────────────────────────

    private func buildVertices(aspect: Float) -> [Vertex] {
        var v: [Vertex] = []
        let violet = nodes.first(where: { $0.id == "violet" })!

        // Connections + autopoietic flow dots
        for (idx, node) in nodes.enumerated() where node.id != "violet" {
            let ov = overlayStates[node.id]
            let edgePhase = Float(idx) * 0.75
            let waveAlpha = 0.18 + 0.14 * sin(time * 1.8 + edgePhase)
            let baseAlpha: Float = node.id == selectedNodeID ? 0.70 : waveAlpha
            let stressBoost = (ov?.stress ?? 0) * 0.3
            v += makeLink(from: violet.position, to: node.position,
                          width: 0.0035, aspect: aspect,
                          color: nodeColor(node).opacity(baseAlpha + stressBoost))
            // Travelling dot — directional flow indicator
            let phase = Float(idx) * 0.618
            let t = (time * 0.25 + phase).truncatingRemainder(dividingBy: 1.0)
            let dotPos = violet.position + (node.position - violet.position) * t
            v += makeCircle(center: dotPos, radius: 0.014, aspect: aspect,
                            color: nodeColor(node).opacity(0.85), segments: 8)
        }

        // Node circles + overlay halos
        for node in nodes {
            let isSelected = node.id == selectedNodeID
            let ov = overlayStates[node.id] ?? NodeOverlayState()
            let base = nodeColor(node)

            // Stress halo (red)
            if ov.stress > 0.05 {
                let haloColor = SIMD4<Float>(1.000, 0.200, 0.200, ov.stress * 0.4 * (0.7 + 0.3 * sin(time * 4)))
                v += makeCircle(center: node.position, radius: node.radius + 0.022,
                                aspect: aspect, color: haloColor, segments: 32)
            }
            // Governance halo (amber)
            if ov.governance > 0.05 {
                let haColor = SIMD4<Float>(0.95, 0.75, 0.10, ov.governance * 0.35)
                v += makeRing(center: node.position, radius: node.radius + 0.018,
                              aspect: aspect, color: haColor, lineWidth: 0.008, segments: 32)
            }
            // Memory pressure (blue desaturate — drawn as cool overlay)
            if ov.memoryPressure > 0.05 {
                let mpColor = SIMD4<Float>(0.10, 0.65, 0.95, ov.memoryPressure * 0.25)
                v += makeCircle(center: node.position, radius: node.radius,
                                aspect: aspect, color: mpColor, segments: 32)
            }
            // Execution ready (bright green ring)
            if ov.executionReady > 0.5 && node.id == "handrail" {
                let erColor = SIMD4<Float>(0.20, 0.85, 0.45, ov.executionReady * 0.6)
                v += makeRing(center: node.position, radius: node.radius + 0.012,
                              aspect: aspect, color: erColor, lineWidth: 0.005, segments: 32)
            }

            // Violet radial glow halos — pulsing per spec
            if node.id == "violet" {
                let outerAlpha = 0.06 + 0.04 * sin(time * 1.4)
                let innerAlpha = 0.10 + 0.06 * sin(time * 1.4)
                v += makeCircle(center: node.position, radius: 0.24, aspect: aspect,
                                color: DesignTokenSIMD.violet.opacity(outerAlpha), segments: 48)
                v += makeCircle(center: node.position, radius: 0.17, aspect: aspect,
                                color: DesignTokenSIMD.violet.opacity(innerAlpha), segments: 48)
            }

            // Core circle
            let violetPulse: Float = node.id == "violet"
                ? 0.022 * sin(time * 2.2) + 0.010 * sin(time * 5.1)
                : 0
            let selectedBoost: Float = isSelected ? 0.015 : 0
            let fillColor = isSelected ? base.opacity(1.0) : base.opacity(0.78)
            if node.role == .handrail || node.role == .kernel || node.role == .yubiKey {
                let lw: Float = node.role == .handrail ? 0.018 : node.role == .kernel ? 0.016 : 0.014
                v += makeRing(center: node.position, radius: node.radius + selectedBoost,
                              aspect: aspect, color: fillColor, lineWidth: lw, segments: 40)
            } else {
                v += makeCircle(center: node.position,
                                radius: node.radius + violetPulse + selectedBoost,
                                aspect: aspect, color: fillColor, segments: 40)
            }

            // Selection ring
            if isSelected {
                v += makeRing(center: node.position, radius: node.radius + 0.028,
                              aspect: aspect, color: base.opacity(0.95), lineWidth: 0.006, segments: 40)
            }
        }
        return v
    }

    // ── Geometry helpers ──────────────────────────────────────────────────────

    private func nodeColor(_ node: OrganismNode) -> SIMD4<Float> {
        switch node.role {
        case .violet:       return DesignTokenSIMD.violet
        case .chamber:      return DesignTokenSIMD.chamber
        case .adjudication: return DesignTokenSIMD.adj
        case .handrail:     return DesignTokenSIMD.handrail
        case .alexandria:   return DesignTokenSIMD.alex
        case .kernel:       return DesignTokenSIMD.kernel
        case .founder:      return DesignTokenSIMD.founder
        case .programs:     return DesignTokenSIMD.build
        case .buildSpace:   return DesignTokenSIMD.build
        case .yubiKey:      return DesignTokenSIMD.yubiKey
        case .membrane:     return DesignTokenSIMD.membrane
        }
    }

    private func makeCircle(center: SIMD2<Float>, radius: Float, aspect: Float,
                             color: SIMD4<Float>, segments: Int) -> [Vertex] {
        var v: [Vertex] = []; let step = Float.pi * 2 / Float(segments)
        for i in 0..<segments {
            let a0 = Float(i) * step; let a1 = a0 + step
            let c = SIMD2<Float>(center.x, center.y)
            let p0 = c + SIMD2(cos(a0) * radius / aspect, sin(a0) * radius)
            let p1 = c + SIMD2(cos(a1) * radius / aspect, sin(a1) * radius)
            v += [Vertex(position: c, color: color),
                  Vertex(position: p0, color: color.opacity(0.50)),
                  Vertex(position: p1, color: color.opacity(0.50))]
        }
        return v
    }

    private func makeRing(center: SIMD2<Float>, radius: Float, aspect: Float,
                           color: SIMD4<Float>, lineWidth: Float, segments: Int) -> [Vertex] {
        var v: [Vertex] = []; let step = Float.pi * 2 / Float(segments)
        let r0 = radius - lineWidth * 0.5; let r1 = radius + lineWidth * 0.5
        for i in 0..<segments {
            let a0 = Float(i) * step; let a1 = a0 + step
            let p00 = center + SIMD2(cos(a0) * r0 / aspect, sin(a0) * r0)
            let p01 = center + SIMD2(cos(a0) * r1 / aspect, sin(a0) * r1)
            let p10 = center + SIMD2(cos(a1) * r0 / aspect, sin(a1) * r0)
            let p11 = center + SIMD2(cos(a1) * r1 / aspect, sin(a1) * r1)
            v += [Vertex(position: p00, color: color), Vertex(position: p01, color: color),
                  Vertex(position: p10, color: color), Vertex(position: p01, color: color),
                  Vertex(position: p11, color: color), Vertex(position: p10, color: color)]
        }
        return v
    }

    private func makeLink(from a: SIMD2<Float>, to b: SIMD2<Float>, width: Float,
                           aspect: Float, color: SIMD4<Float>) -> [Vertex] {
        let dir = normalize(b - a)
        let perp = SIMD2<Float>(-dir.y, dir.x) * SIMD2(width / aspect, width)
        let p0 = a + perp; let p1 = a - perp; let p2 = b + perp; let p3 = b - perp
        return [Vertex(position: p0, color: color), Vertex(position: p1, color: color),
                Vertex(position: p2, color: color), Vertex(position: p1, color: color),
                Vertex(position: p3, color: color), Vertex(position: p2, color: color)]
    }
}

private extension SIMD4 where Scalar == Float {
    func opacity(_ a: Float) -> SIMD4<Float> { SIMD4(x, y, z, a) }
}

private func += <T>(lhs: inout [T], rhs: [T]) { lhs.append(contentsOf: rhs) }
