import SwiftUI

struct SystemPanelView: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Text("System State")
                    .font(.title2.bold())

                if let ss = appState.systemState {
                    GroupBox {
                        VStack(alignment: .leading, spacing: 8) {
                            row("NS Core",          ss.ns_core)
                            row("Coherence Kernel", ss.coherence_kernel)
                            row("IMO Gate",         ss.imo_gate)
                            row("Timestamp",        ss.ts)
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    } label: { Text("NS Core State") }
                }

                GroupBox {
                    VStack(alignment: .leading, spacing: 8) {
                        ForEach(EndpointRegistry.all) { ep in
                            HStack {
                                Text(ep.label)
                                    .font(.caption)
                                    .frame(width: 120, alignment: .leading)
                                Text(ep.url)
                                    .font(.caption.monospaced())
                                    .foregroundStyle(.secondary)
                                    .lineLimit(1)
                                Spacer()
                                Text(ep.method)
                                    .font(.caption.monospaced())
                                    .foregroundStyle(.tertiary)
                            }
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                } label: { Text("Endpoint Registry (\(EndpointRegistry.all.count))") }
            }
            .padding()
        }
    }

    @ViewBuilder
    private func row(_ label: String, _ value: String) -> some View {
        HStack {
            Text(label + ":").font(.caption).foregroundStyle(.secondary).frame(width: 120, alignment: .leading)
            Text(value).font(.caption.monospaced())
        }
    }
}
