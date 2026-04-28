import SwiftUI

struct CoherencePanelView: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Text("Coherence Kernel — NCOM")
                    .font(.title2.bold())

                if let rs = appState.readiness?.latest {
                    GroupBox {
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Text("Readiness Score")
                                    .font(.headline)
                                Spacer()
                                Text(String(format: "%.2f / 100", rs.score_100 ?? 0))
                                    .font(.title3.monospaced().bold())
                                    .foregroundStyle(scoreColor(rs.score_100 ?? 0))
                            }
                            if let metrics = rs.sub_metrics {
                                Divider()
                                ForEach(metrics.sorted(by: { $0.key < $1.key }), id: \.key) { k, v in
                                    HStack {
                                        Text(k.replacingOccurrences(of: "_", with: " "))
                                            .font(.caption)
                                        Spacer()
                                        ProgressView(value: v, total: 10.0)
                                            .frame(width: 120)
                                        Text(String(format: "%.1f", v))
                                            .font(.caption.monospaced())
                                            .frame(width: 30, alignment: .trailing)
                                    }
                                }
                            }
                            if let ts = rs.ts {
                                Text("Measured: \(ts)")
                                    .font(.caption2)
                                    .foregroundStyle(.tertiary)
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    } label: { Text("Latest Branch") }
                }

                if let lh = appState.ledger {
                    GroupBox {
                        VStack(alignment: .leading, spacing: 6) {
                            HStack {
                                Image(systemName: lh.all_chains_valid == true ? "checkmark.shield.fill" : "xmark.shield.fill")
                                    .foregroundStyle(lh.all_chains_valid == true ? .green : .red)
                                Text(lh.all_chains_valid == true ? "All chains valid" : "Chain violation detected")
                                    .font(.subheadline)
                            }
                            if let tables = lh.tables {
                                Divider()
                                ForEach(tables.sorted(by: { $0.key < $1.key }), id: \.key) { tbl, info in
                                    HStack {
                                        StatusBadge(label: tbl, isUp: info.chain_valid ?? false)
                                        Spacer()
                                        Text("\(info.count ?? 0) rows")
                                            .font(.caption.monospaced())
                                            .foregroundStyle(.secondary)
                                    }
                                }
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    } label: { Text("Ledger Health") }
                }
            }
            .padding()
        }
    }

    private func scoreColor(_ s: Double) -> Color {
        if s >= 88 { return .green }
        if s >= 70 { return .yellow }
        return .red
    }
}
