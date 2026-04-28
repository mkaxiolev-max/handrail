import SwiftUI

struct CommandPanelView: View {
    @EnvironmentObject var appState: AppState
    @State private var prompt = ""
    @State private var isLoading = false

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Command — IMO Gate Query")
                .font(.title2.bold())

            HStack {
                TextField("Enter prompt…", text: $prompt)
                    .textFieldStyle(.roundedBorder)
                    .onSubmit { submit() }
                Button("Submit") { submit() }
                    .disabled(prompt.trimmingCharacters(in: .whitespaces).isEmpty || isLoading)
            }

            if isLoading {
                ProgressView("Routing through IMO gate…")
            }

            if let resp = appState.queryResponse {
                GroupBox {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack { Text("Verb:"); VerbBadge(verb: resp.verb) }
                        HStack {
                            Text("Score:")
                            Text(String(format: "%.1f / 100", resp.score_100))
                                .font(.body.monospaced())
                        }
                        HStack {
                            Text("Confidence:")
                            Text(String(format: "%.0f%%", resp.confidence * 100))
                                .font(.body.monospaced())
                        }
                        Divider()
                        Text(resp.answer)
                            .font(.body)
                        if let bid = resp.branch_id {
                            Text("branch: \(bid)")
                                .font(.caption.monospaced())
                                .foregroundStyle(.secondary)
                        }
                        if let pid = resp.proposal_id {
                            Text("proposal: \(pid)")
                                .font(.caption.monospaced())
                                .foregroundStyle(.secondary)
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                } label: {
                    Text("IMO Gate Decision")
                }
            }
            Spacer()
        }
        .padding()
    }

    private func submit() {
        let p = prompt.trimmingCharacters(in: .whitespaces)
        guard !p.isEmpty else { return }
        isLoading = true
        Task {
            await appState.sendQuery(p)
            isLoading = false
        }
    }
}
