import SwiftUI
import MetalKit

// NSViewRepresentable bridge: MTKView + zoom/pan + node hit-testing inside SwiftUI
struct MetalOrganismView: NSViewRepresentable {
    @Binding var selectedNode: OrganismNode?

    func makeNSView(context: Context) -> OrganismMTKView {
        let view = OrganismMTKView()
        view.device = MTLCreateSystemDefaultDevice()
        view.clearColor = MTLClearColor(red: 0.05, green: 0.05, blue: 0.07, alpha: 1.0)
        view.colorPixelFormat = .bgra8Unorm
        view.framebufferOnly = false
        view.enableSetNeedsDisplay = false
        view.isPaused = false
        view.preferredFramesPerSecond = 60

        guard let renderer = OrganismRenderer(mtkView: view) else { return view }
        renderer.onNodeSelected = { node in
            DispatchQueue.main.async { selectedNode = node }
        }
        view.delegate = renderer
        view.renderer = renderer
        context.coordinator.renderer = renderer

        // Zoom via magnification gesture
        let magnify = NSMagnificationGestureRecognizer(target: context.coordinator,
                                                       action: #selector(Coordinator.handleMagnify(_:)))
        view.addGestureRecognizer(magnify)

        // Pan via click-drag
        let pan = NSPanGestureRecognizer(target: context.coordinator,
                                         action: #selector(Coordinator.handlePan(_:)))
        view.addGestureRecognizer(pan)

        return view
    }

    func updateNSView(_ nsView: OrganismMTKView, context: Context) {}

    func makeCoordinator() -> Coordinator { Coordinator() }

    final class Coordinator: NSObject {
        var renderer: OrganismRenderer?

        @objc func handleMagnify(_ gr: NSMagnificationGestureRecognizer) {
            let delta = Float(gr.magnification)
            renderer?.adjustZoom(delta: delta)
            gr.magnification = 0
        }

        @objc func handlePan(_ gr: NSPanGestureRecognizer) {
            guard let view = gr.view else { return }
            let t = gr.translation(in: view)
            let size = view.bounds.size
            renderer?.adjustPan(dx: Float(t.x / size.width * 2),
                                  dy: Float(-t.y / size.height * 2))
            gr.setTranslation(.zero, in: view)
        }
    }
}

// Custom MTKView subclass to forward click hit-testing to renderer
final class OrganismMTKView: MTKView {
    weak var renderer: OrganismRenderer?

    override func mouseDown(with event: NSEvent) {
        let loc = convert(event.locationInWindow, from: nil)
        let ndc = SIMD2<Float>(
            Float(loc.x / bounds.width) * 2 - 1,
            Float(loc.y / bounds.height) * 2 - 1
        )
        renderer?.hitTest(ndc: ndc)
    }
}
