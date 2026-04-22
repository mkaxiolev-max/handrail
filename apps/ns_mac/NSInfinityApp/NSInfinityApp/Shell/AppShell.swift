import SwiftUI
import AppKit

struct AppShell: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        ZStack {
            DSColors.background.ignoresSafeArea()

            VStack(spacing: 0) {
                TopBar()
                    .frame(height: 48)

                HStack(spacing: 0) {
                    LeftRail()
                        .frame(width: 220)

                    ZStack {
                        DSColors.background
                        modeContent
                            .id(appState.currentMode)   // force view replacement on mode change
                            .transition(.asymmetric(
                                insertion: .opacity.combined(with: .scale(scale: 0.97, anchor: .center)),
                                removal:   .opacity.combined(with: .scale(scale: 1.02, anchor: .center))
                            ))
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .animation(.spring(response: 0.28, dampingFraction: 0.82), value: appState.currentMode)

                    RightInspector()
                        .frame(width: 280)
                }
                .frame(maxHeight: .infinity)

                BottomTimeline()
                    .frame(height: 140)
            }

            VoiceOverlay()
        }
        .preferredColorScheme(.dark)
    }

    @ViewBuilder
    private var modeContent: some View {
        switch appState.currentMode {
        case .founderHome:  FounderHomeView()
        case .livingArch:   LivingArchitectureView()
        case .engineRoom:   EngineRoomView()
        case .alexandria:   AlexandriaView()
        case .governance:   GovernanceView()
        case .buildSpace:   BuildSpaceView()
        }
    }
}
