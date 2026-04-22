import SwiftUI

struct OmegaView: View {
    @State private var capGraph: [String: Any] = [:]
    @State private var modelStatus: [String: Any] = [:]
    @State private var semanticCandidates: [[String: Any]] = []
    @State private var currentScore: Double = 0

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Ω Omega")
                            .font(.system(size: 28, weight: .black))
                            .foregroundColor(DSColors.violet)
                        Text("Intelligence surface · scoring · capability graph")
                            .font(.system(size: 12)).foregroundColor(DSColors.textSecondary)
                    }
                    Spacer()
                    if currentScore > 0 {
                        ZStack {
                            Circle().stroke(DSColors.violetDim, lineWidth: 2).frame(width: 64, height: 64)
                            VStack(spacing: 0) {
                                Text(String(format: "%.1f", currentScore))
                                    .font(.system(size: 18, weight: .black, design: .monospaced))
                                    .foregroundColor(DSColors.violet)
                                Text("live").font(.system(size: 8)).foregroundColor(DSColors.textTertiary)
                            }
                        }
                    }
                }

                // Score bands
                VStack(alignment: .leading, spacing: 8) {
                    SectionHeader(title: "SCORE BANDS")
                    HStack(spacing: 10) {
                        BandCard(label: "Omega-Approaching", threshold: 90.0, color: DSColors.accentAmber,
                                 reached: currentScore >= 90)
                        BandCard(label: "Omega-Certified",   threshold: 93.0, color: DSColors.online,
                                 reached: currentScore >= 93)
                        BandCard(label: "Omega-Full",        threshold: 96.0, color: DSColors.violet,
                                 reached: currentScore >= 96)
                    }
                }

                // Model status
                if !modelStatus.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        SectionHeader(title: "MODEL REGISTRY")
                        ModelStatusWidget(status: modelStatus)
                    }
                }

                // Capability unresolved
                let unresolved = capGraph["unresolved"] as? [[String: Any]] ?? []
                if !unresolved.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        SectionHeader(title: "UNRESOLVED CAPABILITIES — TOP STRATEGIC VALUE")
                        ForEach(Array(unresolved.prefix(8).enumerated()), id: \.offset) { _, cap in
                            CapabilityRow(cap: cap)
                        }
                    }
                }

                // Semantic candidates
                if !semanticCandidates.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        SectionHeader(title: "SEMANTIC REFINEMENT CANDIDATES")
                        ForEach(Array(semanticCandidates.prefix(5).enumerated()), id: \.offset) { _, c in
                            SemanticRow(candidate: c)
                        }
                    }
                }
            }
            .padding(24)
        }
        .task {
            async let capFetch      = RuntimeAPIClient.shared.fetchCapabilityGraph()
            async let modelFetch    = RuntimeAPIClient.shared.fetchModelStatus()
            async let semanticFetch = RuntimeAPIClient.shared.fetchSemanticCandidates()
            async let scoreFetch    = RuntimeAPIClient.shared.fetchScore()
            let (cap, mod, sem, sc) = await (capFetch, modelFetch, semanticFetch, scoreFetch)
            capGraph = cap; modelStatus = mod; semanticCandidates = sem
            if let s = sc { currentScore = s }
        }
    }
}

private struct BandCard: View {
    let label: String
    let threshold: Double
    let color: Color
    let reached: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(String(format: "%.0f+", threshold))
                    .font(.system(size: 20, weight: .black, design: .monospaced))
                    .foregroundColor(reached ? color : DSColors.textTertiary)
                if reached {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: 10))
                        .foregroundColor(color)
                }
            }
            Text(label).font(.system(size: 9)).foregroundColor(reached ? DSColors.textSecondary : DSColors.textTertiary)
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(reached ? color.opacity(0.12) : DSColors.surfaceCard)
        .cornerRadius(8)
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(reached ? color.opacity(0.35) : DSColors.surfaceBorder, lineWidth: 1))
    }
}

private struct ModelStatusWidget: View {
    let status: [String: Any]

    var models: [(String, Bool)] {
        let models = status["models"] as? [[String: Any]] ?? []
        return models.compactMap { m -> (String, Bool)? in
            guard let name = m["name"] as? String else { return nil }
            let enabled = m["enabled"] as? Bool ?? false
            return (name, enabled)
        }
    }

    var body: some View {
        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 6) {
            ForEach(models, id: \.0) { name, enabled in
                HStack(spacing: 6) {
                    Circle().fill(enabled ? DSColors.online : DSColors.textTertiary).frame(width: 5, height: 5)
                    Text(name).font(.system(size: 10)).foregroundColor(enabled ? DSColors.textSecondary : DSColors.textTertiary)
                }
                .padding(6).background(DSColors.surfaceCard).cornerRadius(5)
            }
        }
    }
}

private struct CapabilityRow: View {
    let cap: [String: Any]
    var body: some View {
        HStack(spacing: 8) {
            let state = cap["state"] as? String ?? "missing"
            Image(systemName: state == "active" ? "checkmark.circle" : "exclamationmark.circle")
                .font(.system(size: 10)).foregroundColor(state == "active" ? DSColors.online : DSColors.accentAmber)
            VStack(alignment: .leading, spacing: 1) {
                Text(cap["id"] as? String ?? "—")
                    .font(.system(size: 10, design: .monospaced)).foregroundColor(DSColors.textSecondary)
                if let desc = cap["description"] as? String {
                    Text(desc).font(.system(size: 9)).foregroundColor(DSColors.textTertiary).lineLimit(1)
                }
            }
            Spacer()
            if let sv = cap["strategic_value"] as? Int {
                Text("sv:\(sv)").font(.system(size: 8, weight: .semibold))
                    .foregroundColor(sv >= 8 ? DSColors.violet : DSColors.textTertiary)
            }
        }
        .padding(8).background(DSColors.surfaceCard).cornerRadius(5)
    }
}

private struct SemanticRow: View {
    let candidate: [String: Any]
    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: "sparkle").font(.system(size: 9)).foregroundColor(DSColors.violet)
            Text(candidate["term"] as? String ?? candidate["id"] as? String ?? "—")
                .font(.system(size: 10, design: .monospaced)).foregroundColor(DSColors.textSecondary)
            Spacer()
            Text(candidate["impact"] as? String ?? "").font(.system(size: 9)).foregroundColor(DSColors.textTertiary)
        }
        .padding(8).background(DSColors.surfaceCard).cornerRadius(5)
    }
}

#Preview {
    OmegaView()
        .frame(width: 900, height: 700)
        .preferredColorScheme(.dark)
}
