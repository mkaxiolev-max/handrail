import SwiftUI

struct StorytimePanelView: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Text("Storytime — Gate Narration")
                    .font(.title2.bold())

                if let st = appState.storytime {
                    GroupBox {
                        VStack(alignment: .leading, spacing: 6) {
                            Text("What Happened")
                                .font(.headline)
                            ForEach(Array(st.what_happened.enumerated()), id: \.offset) { _, item in
                                Text("· \(item)")
                                    .font(.body)
                            }
                            if st.what_happened.isEmpty {
                                Text("No gate events yet.")
                                    .foregroundStyle(.secondary)
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    } label: { Text("Events") }

                    GroupBox {
                        VStack(alignment: .leading, spacing: 6) {
                            Text("Uncertain (hold_ncom)")
                                .font(.headline)
                            ForEach(st.what_is_uncertain, id: \.self) { pid in
                                Text("· \(pid)")
                                    .font(.caption.monospaced())
                                    .foregroundStyle(.yellow)
                            }
                            if st.what_is_uncertain.isEmpty {
                                Text("Nothing held in NCOM.")
                                    .foregroundStyle(.secondary)
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    } label: { Text("NCOM Hold") }

                    GroupBox {
                        VStack(alignment: .leading, spacing: 6) {
                            Text("Changed (collapse_ready)")
                                .font(.headline)
                            ForEach(st.what_changed, id: \.self) { pid in
                                Text("· \(pid)")
                                    .font(.caption.monospaced())
                                    .foregroundStyle(.green)
                            }
                            if st.what_changed.isEmpty {
                                Text("No canon-eligible decisions yet.")
                                    .foregroundStyle(.secondary)
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    } label: { Text("Canon-Eligible") }

                    Text(st.rule)
                        .font(.caption.italic())
                        .foregroundStyle(.secondary)
                } else {
                    ProgressView()
                }
            }
            .padding()
        }
    }
}
