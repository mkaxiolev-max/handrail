import SwiftUI

struct VoiceOverlay: View {
    @EnvironmentObject var appState: AppState
    @State private var isExpanded = false

    var body: some View {
        VStack {
            Spacer()
            HStack {
                Spacer()
                ZStack(alignment: .bottomTrailing) {
                    if isExpanded {
                        VoicePanel(appState: appState, isExpanded: $isExpanded)
                            .transition(.asymmetric(
                                insertion: .scale(scale: 0.85, anchor: .bottomTrailing).combined(with: .opacity),
                                removal:   .scale(scale: 0.85, anchor: .bottomTrailing).combined(with: .opacity)
                            ))
                            .offset(x: 0, y: -60)
                    }
                    VoiceOrb(state: appState.voiceState, isExpanded: $isExpanded)
                }
                .padding(.trailing, 32)
                .padding(.bottom, 160)
                .animation(.spring(response: 0.32, dampingFraction: 0.78), value: isExpanded)
            }
        }
    }
}

// MARK: — Orb

struct VoiceOrb: View {
    let state: VoiceState
    @Binding var isExpanded: Bool
    @State private var pulse: Bool = false

    var body: some View {
        ZStack {
            if state == .listening || state == .processing {
                Circle()
                    .stroke(stateColor.opacity(0.25), lineWidth: 2)
                    .frame(width: pulse ? 72 : 52, height: pulse ? 72 : 52)
                    .animation(.easeInOut(duration: 0.9).repeatForever(autoreverses: true), value: pulse)
                Circle()
                    .stroke(stateColor.opacity(0.12), lineWidth: 2)
                    .frame(width: pulse ? 90 : 68, height: pulse ? 90 : 68)
                    .animation(.easeInOut(duration: 1.2).repeatForever(autoreverses: true).delay(0.2), value: pulse)
            }
            Circle()
                .fill(RadialGradient(
                    colors: [stateColor.opacity(0.95), stateColor.opacity(0.45)],
                    center: .center, startRadius: 2, endRadius: 24
                ))
                .frame(width: 50, height: 50)
                .overlay(
                    Image(systemName: stateIcon)
                        .font(.system(size: 17, weight: .semibold))
                        .foregroundColor(.white)
                )
                .shadow(color: stateColor.opacity(0.55), radius: 14)
                .onTapGesture { isExpanded.toggle() }
        }
        .onAppear { pulse = true }
    }

    var stateColor: Color { state.color.color }

    var stateIcon: String {
        switch state {
        case .dormant:    return "mic.slash"
        case .ready:      return "mic"
        case .listening:  return "waveform"
        case .processing: return "cpu"
        case .responding: return "speaker.wave.2"
        case .muted:      return "mic.slash.fill"
        }
    }
}

// MARK: — Expanded Panel

private struct VoicePanel: View {
    let appState: AppState
    @Binding var isExpanded: Bool
    @State private var sessions: [[String: Any]] = []
    @State private var inputText: String = ""

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Header
            HStack {
                Image(systemName: "waveform").font(.system(size: 11)).foregroundColor(DSColors.violet)
                Text("VOICE LANE").font(.system(size: 10, weight: .bold)).foregroundColor(DSColors.textSecondary).tracking(1.2)
                Spacer()
                Circle().fill(appState.voiceState == .dormant ? DSColors.textTertiary : DSColors.online)
                    .frame(width: 6, height: 6)
                Text(appState.voiceState.label).font(.system(size: 9)).foregroundColor(DSColors.textTertiary)
                Button { isExpanded = false } label: {
                    Image(systemName: "xmark").font(.system(size: 9)).foregroundColor(DSColors.textTertiary)
                }.buttonStyle(.plain).padding(.leading, 6)
            }
            .padding(.horizontal, 12).padding(.vertical, 8)

            Divider().overlay(DSColors.surfaceBorder)

            // Active sessions
            if sessions.isEmpty {
                Text(appState.isServicesOnline ? "No active voice sessions" : "NS offline — voice unavailable")
                    .font(.system(size: 10)).foregroundColor(DSColors.textTertiary)
                    .padding(12)
            } else {
                ForEach(Array(sessions.prefix(3).enumerated()), id: \.offset) { _, s in
                    SessionRow(session: s)
                }
            }

            Divider().overlay(DSColors.surfaceBorder)

            // Quick text-to-NS input
            HStack(spacing: 6) {
                TextField("Ask NS…", text: $inputText)
                    .font(.system(size: 11))
                    .textFieldStyle(.plain)
                    .foregroundColor(DSColors.textPrimary)
                Button("↑") {
                    Task { await sendToNS() }
                }
                .buttonStyle(.plain)
                .font(.system(size: 14, weight: .bold))
                .foregroundColor(inputText.isEmpty ? DSColors.textTertiary : DSColors.violet)
                .disabled(inputText.isEmpty)
            }
            .padding(.horizontal, 10).padding(.vertical, 8)
        }
        .frame(width: 280)
        .background(DSColors.surfaceCard.opacity(0.97))
        .cornerRadius(12)
        .overlay(RoundedRectangle(cornerRadius: 12).stroke(DSColors.violetDim, lineWidth: 1))
        .shadow(color: DSColors.violet.opacity(0.15), radius: 20)
        .task { sessions = await RuntimeAPIClient.shared.fetchVoiceSessions()["active_sessions"] as? [[String: Any]] ?? [] }
    }

    func sendToNS() async {
        guard !inputText.isEmpty else { return }
        let text = inputText
        inputText = ""
        _ = await RuntimeAPIClient.shared.sendChat(text)
    }
}

private struct SessionRow: View {
    let session: [String: Any]
    var body: some View {
        HStack(spacing: 8) {
            Circle().fill(DSColors.online).frame(width: 5, height: 5)
            Text(session["session_id"] as? String ?? "session")
                .font(.system(size: 9, design: .monospaced)).foregroundColor(DSColors.textSecondary).lineLimit(1)
            Spacer()
            Text(session["state"] as? String ?? "active")
                .font(.system(size: 8)).foregroundColor(DSColors.textTertiary)
        }
        .padding(.horizontal, 12).padding(.vertical, 4)
    }
}
