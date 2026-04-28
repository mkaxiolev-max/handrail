import SwiftUI

struct CanonPanelView: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("Canon — Collapse-Ready Records")
                    .font(.title2.bold())
                Spacer()
                Text("\(appState.canonRecords.count) records")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }

            if appState.canonRecords.isEmpty {
                ContentUnavailableView(
                    "No Canon Records",
                    systemImage: "checkmark.seal",
                    description: Text("Canon records appear when IMO gate returns collapse_ready.")
                )
            } else {
                List(appState.canonRecords) { record in
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            VerbBadge(verb: record.verb)
                            Text(record.branch_id)
                                .font(.caption.monospaced())
                                .foregroundStyle(.secondary)
                        }
                        Text(record.claim)
                            .font(.body)
                        if let receipt = record.imo_receipt {
                            Text(receipt)
                                .font(.caption.monospaced())
                                .foregroundStyle(.tertiary)
                                .lineLimit(1)
                        }
                    }
                    .padding(.vertical, 4)
                }
                .listStyle(.plain)
            }
        }
        .padding()
    }
}
