import SwiftUI

struct GovernanceView: View {
    @State private var decisions: [[String: Any]] = []
    @State private var continuumState: [String: Any] = [:]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Text("Governance")
                    .font(.system(size: 28, weight: .black))
                    .foregroundColor(DSColors.textPrimary)

                // Continuum / TierLatch
                VStack(alignment: .leading, spacing: 8) {
                    SectionHeader(title: "CONTINUUM / TIER LATCH")
                    HStack(spacing: 16) {
                        let tier = continuumState["tier"] as? Int ?? 0
                        TierLatchBadge(tier: tier)
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Tier \(tier)").font(.system(size: 16, weight: .bold)).foregroundColor(DSColors.textPrimary)
                            Text(tierLabel(tier)).font(.system(size: 11)).foregroundColor(DSColors.textSecondary)
                            Text("Ratchet-only up — irreversible").font(.system(size: 9)).foregroundColor(DSColors.textTertiary)
                        }
                    }
                    .padding(12)
                    .background(DSColors.surfaceCard)
                    .cornerRadius(8)
                }

                // Never-events
                VStack(alignment: .leading, spacing: 8) {
                    SectionHeader(title: "NEVER-EVENTS")
                    ForEach(neverEvents, id: \.self) { ne in
                        HStack(spacing: 8) {
                            Image(systemName: "shield.fill").font(.system(size: 10)).foregroundColor(DSColors.violet)
                            Text(ne).font(.system(size: 11, design: .monospaced)).foregroundColor(DSColors.textSecondary)
                            Spacer()
                            Text("HELD").font(.system(size: 9, weight: .bold)).foregroundColor(DSColors.online)
                        }
                        .padding(8)
                        .background(DSColors.surfaceCard)
                        .cornerRadius(6)
                    }
                }

                // YubiKey quorum
                VStack(alignment: .leading, spacing: 8) {
                    SectionHeader(title: "YUBIKEY QUORUM")
                    HStack(spacing: 12) {
                        QuorumSlot(slot: 1, serial: "26116460", active: true)
                        QuorumSlot(slot: 2, serial: "—", active: false)
                        QuorumSlot(slot: 3, serial: "—", active: false)
                    }
                    .padding(12)
                    .background(DSColors.surfaceCard)
                    .cornerRadius(8)
                }
            }
            .padding(24)
        }
        .task {
            continuumState = await RuntimeAPIClient.shared.fetchContinuumState()
        }
    }

    func tierLabel(_ t: Int) -> String {
        switch t { case 0: return "Active"; case 2: return "Isolated"; case 3: return "Suspended"; default: return "Unknown" }
    }

    let neverEvents = [
        "dignity.never_event",
        "sys.self_destruct",
        "auth.bypass",
        "policy.override"
    ]
}

private struct TierLatchBadge: View {
    let tier: Int
    var body: some View {
        ZStack {
            Circle().fill(tier == 0 ? DSColors.online.opacity(0.15) : DSColors.offline.opacity(0.15))
                .frame(width: 52, height: 52)
            Text("T\(tier)").font(.system(size: 20, weight: .black, design: .monospaced))
                .foregroundColor(tier == 0 ? DSColors.online : DSColors.offline)
        }
    }
}

private struct QuorumSlot: View {
    let slot: Int
    let serial: String
    let active: Bool
    var body: some View {
        VStack(spacing: 4) {
            Image(systemName: active ? "key.fill" : "key").font(.system(size: 16))
                .foregroundColor(active ? DSColors.violet : DSColors.textTertiary)
            Text("Slot \(slot)").font(.system(size: 9)).foregroundColor(DSColors.textTertiary)
            Text(serial).font(.system(size: 8, design: .monospaced)).foregroundColor(active ? DSColors.textSecondary : DSColors.textTertiary)
            Text(active ? "ACTIVE" : "PENDING").font(.system(size: 8, weight: .bold))
                .foregroundColor(active ? DSColors.online : DSColors.textTertiary)
        }
        .padding(8)
        .background(DSColors.surfaceElevated)
        .cornerRadius(6)
    }
}

struct SectionHeader: View {
    let title: String
    var body: some View {
        Text(title)
            .font(.system(size: 10, weight: .semibold))
            .foregroundColor(DSColors.textTertiary)
            .tracking(1.5)
    }
}
