#include <metal_stdlib>
using namespace metal;

// Matches Swift struct Vertex { SIMD2<Float> position; SIMD4<Float> color }
struct VertexIn {
    float2 position;
    float4 color;
};

struct CameraUniforms {
    float  zoom;
    float2 pan;
    float  time;
};

struct VertexOut {
    float4 position [[position]];
    float4 color;
};

vertex VertexOut organism_vertex(uint vid                           [[vertex_id]],
                                  device const VertexIn* vertices   [[buffer(0)]],
                                  constant CameraUniforms& cam       [[buffer(1)]]) {
    VertexOut out;
    float2 p = vertices[vid].position;
    // Apply pan and zoom
    p = (p + cam.pan) * cam.zoom;
    out.position = float4(p.x, p.y, 0.0, 1.0);
    out.color    = vertices[vid].color;
    return out;
}

fragment float4 organism_fragment(VertexOut in [[stage_in]]) {
    return in.color;
}
