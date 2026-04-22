import SwiftUI

struct LeftRail: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        VStack(spacing: 0) {
            // Mode navigation
            VStack(spacing: 2) {
                ForEach(HabitatMode.allCases) { mode in
                    ModeNavItem(mode: mode, isSelected: appState.currentMode == mode)
                        .onTapGesture { appState.currentMode = mode }
                }
            }
            .padding(.top, 12)
            .padding(.horizontal, 8)

            Divider().padding(.vertical, 12).overlay(DSColors.surfaceBorder)

            // Service status
            VStack(alignment: .leading, spacing: 4) {
                Text("SERVICES")
                    .font(.system(size: 9, weight: .semibold))
                    .foregroundColor(DSColors.textTertiary)
                    .tracking(1.5)
                    .padding(.horizontal, 12)

                ForEach(appState.services) { svc in
                    ServiceStatusRow(svc: svc)
                }
            }

            Spacer()

            // Founder identity block
            FounderIdentityBlock()
                .padding(.bottom, 16)
        }
        .background(DSColors.surfaceElevated)
        .overlay(alignment: .trailing) {
            Rectangle().fill(DSColors.surfaceBorder).frame(width: 1)
        }
    }
}

private struct ModeNavItem: View {
    let mode: HabitatMode
    let isSelected: Bool

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: mode.icon)
                .font(.system(size: 13))
                .frame(width: 18)
                .foregroundColor(isSelected ? DSColors.violet : DSColors.textSecondary)
            Text(mode.rawValue)
                .font(.system(size: 12, weight: isSelected ? .semibold : .regular))
                .foregroundColor(isSelected ? DSColors.textPrimary : DSColors.textSecondary)
            Spacer()
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 7)
        .background(isSelected ? DSColors.violetFaint : Color.clear)
        .cornerRadius(6)
        .overlay(
            RoundedRectangle(cornerRadius: 6)
                .stroke(isSelected ? DSColors.violetDim : Color.clear, lineWidth: 1)
        )
    }
}

private struct ServiceStatusRow: View {
    @ObservedObject var svc: ServiceHealth

    var body: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(statusColor)
                .frame(width: 5, height: 5)
            Text(svc.name)
                .font(.system(size: 10))
                .foregroundColor(DSColors.textSecondary)
            Spacer()
            Text(":\(svc.port)")
                .font(.system(size: 9, design: .monospaced))
                .foregroundColor(DSColors.textTertiary)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 2)
    }

    var statusColor: Color {
        switch svc.status {
        case .online:   return DSColors.online
        case .offline:  return DSColors.offline
        case .degraded: return DSColors.degraded
        case .unknown:  return DSColors.textTertiary
        }
    }
}

private struct FounderIdentityBlock: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            Rectangle().fill(DSColors.surfaceBorder).frame(height: 1).padding(.bottom, 8)
            HStack(spacing: 8) {
                Circle()
                    .fill(DSColors.violetDim)
                    .frame(width: 28, height: 28)
                    .overlay(
                        Text(String(appState.founderIdentity.name.prefix(1)))
                            .font(.system(size: 11, weight: .bold))
                            .foregroundColor(DSColors.violet)
                    )
                VStack(alignment: .leading, spacing: 1) {
                    Text(appState.founderIdentity.name)
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundColor(DSColors.textPrimary)
                    Text(appState.founderIdentity.entity)
                        .font(.system(size: 9))
                        .foregroundColor(DSColors.textTertiary)
                }
            }
            .padding(.horizontal, 12)
        }
    }
}
