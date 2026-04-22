#include <metal_stdlib>
using namespace metal;

// ── Shared types ──────────────────────────────────────────────────────────────

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
    float2 uv;          // world-space position for particle SDF
};

// ── Organism vertex ───────────────────────────────────────────────────────────

vertex VertexOut organism_vertex(uint vid                         [[vertex_id]],
                                  device const VertexIn* vertices [[buffer(0)]],
                                  constant CameraUniforms& cam     [[buffer(1)]]) {
    VertexOut out;
    float2 p = vertices[vid].position;
    out.uv   = p;
    p = (p + cam.pan) * cam.zoom;
    out.position = float4(p.x, p.y, 0.0, 1.0);
    out.color    = vertices[vid].color;
    return out;
}

fragment float4 organism_fragment(VertexOut in [[stage_in]]) {
    return in.color;
}

// ── Particle field ────────────────────────────────────────────────────────────

struct ParticleVertex {
    float2 position;
};

struct ParticleUniforms {
    float  time;
    float2 resolution;
    float  zoom;
    float2 pan;
};

struct ParticleOut {
    float4 position    [[position]];
    float  brightness;
    float  size        [[point_size]];
};

struct ParticleFragIn {
    float  brightness;
    float2 point_coord [[point_coord]];
};

// Hash functions for pseudo-random particles
float hash(float n) { return fract(sin(n) * 43758.5453); }
float hash2(float2 p) { return fract(sin(dot(p, float2(127.1, 311.7))) * 43758.5453); }

vertex ParticleOut particle_vertex(uint vid                             [[vertex_id]],
                                    constant ParticleUniforms& uniforms  [[buffer(0)]]) {
    ParticleOut out;

    // Deterministic particle position from ID
    float id = float(vid);
    float2 seed = float2(hash(id), hash(id + 100.0));

    // Distribute particles in a wide field
    float2 pos = (seed * 2.0 - 1.0) * 1.8;

    // Slow drift
    float drift = uniforms.time * 0.02 * (hash(id + 200.0) * 2.0 - 1.0);
    pos.y += drift;

    // Wrap vertically
    pos.y = fmod(pos.y + 2.0, 4.0) - 2.0;

    // Apply camera transform
    pos = (pos + uniforms.pan) * uniforms.zoom;

    out.position   = float4(pos.x, pos.y, 0.0, 1.0);
    out.brightness = 0.15 + 0.35 * hash(id + 300.0) + 0.15 * sin(uniforms.time * (1.0 + hash(id + 400.0)));
    out.size       = 1.5 + 1.5 * hash(id + 500.0);
    return out;
}

fragment float4 particle_fragment(ParticleFragIn in [[stage_in]]) {
    // Point sprite: soft circle
    float2 uv = in.point_coord * 2.0 - 1.0;
    float d = length(uv);
    if (d > 1.0) discard_fragment();
    float alpha = (1.0 - d * d) * in.brightness;
    // Violet-tinted particles
    return float4(0.56 * alpha, 0.35 * alpha, 0.95 * alpha, alpha * 0.7);
}
