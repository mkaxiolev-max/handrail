import SwiftUI

struct ContradictionsPanelView: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("Contradictions")
                    .font(.title2.bold())
                Spacer()
                if let ct = appState.contradictions {
                    Text(String(format: "Pressure: %.2f", ct.pressure_score))
                        .font(.subheadline.monospaced())
                        .foregroundStyle(ct.pressure_score > 0.5 ? .red : .secondary)
                }
            }

            if let ct = appState.contradictions {
                if ct.items.isEmpty {
                    ContentUnavailableView(
                        "No Contradictions",
                        systemImage: "checkmark.circle",
                        description: Text("All branches are internally consistent.")
                    )
                } else {
                    List(ct.items) { item in
                        VStack(alignment: .leading, spacing: 4) {
                            Text(item.claim)
                                .font(.body)
                            Text("contradicts: \(item.contradicts.joined(separator: ", "))")
                                .font(.caption.monospaced())
                                .foregroundStyle(.red.opacity(0.8))
                        }
                        .padding(.vertical, 4)
                    }
                    .listStyle(.plain)
                }
            } else {
                ProgressView()
            }
        }
        .padding()
    }
}
