import SwiftUI

struct ScorePanelView: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                HStack(alignment: .firstTextBaseline) {
                    Text("Cockpit Score")
                        .font(.title2.bold())
                    Spacer()
                    if let s = appState.score {
                        VStack(alignment: .trailing) {
                            Text(String(format: "%.1f / 100", s.score100))
                                .font(.largeTitle.bold().monospaced())
                                .foregroundStyle(gradeColor(s.grade))
                            Text("Grade: \(s.grade)")
                                .font(.headline)
                                .foregroundStyle(gradeColor(s.grade))
                        }
                    }
                }

                if let s = appState.score {
                    GroupBox {
                        VStack(alignment: .leading, spacing: 10) {
                            ForEach(s.dimensions) { dim in
                                VStack(alignment: .leading, spacing: 2) {
                                    HStack {
                                        Text(dim.label)
                                            .font(.subheadline)
                                        Spacer()
                                        Text(String(format: "%.1f / %.0f", dim.score, dim.max))
                                            .font(.caption.monospaced())
                                    }
                                    ProgressView(value: dim.score, total: dim.max)
                                        .tint(dim.score >= 8 ? .green : dim.score >= 5 ? .yellow : .red)
                                    if !dim.note.isEmpty {
                                        Text(dim.note)
                                            .font(.caption2)
                                            .foregroundStyle(.secondary)
                                    }
                                }
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    } label: { Text("9-Dimension Rubric") }
                } else {
                    ProgressView("Computing score…")
                }
            }
            .padding()
        }
    }

    private func gradeColor(_ g: String) -> Color {
        switch g {
        case "S": return .green
        case "A": return .blue
        case "B": return .yellow
        default:  return .red
        }
    }
}
