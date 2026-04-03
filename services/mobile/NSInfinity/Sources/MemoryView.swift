import SwiftUI

struct MemoryView: View {
    @EnvironmentObject var client: NSClient
    var body: some View {
        NavigationStack {
            Group {
                if client.memoryEntries.isEmpty {
                    VStack { Spacer(); Text("No memory entries").foregroundColor(.secondary); Spacer() }
                } else {
                    List(Array(client.memoryEntries.enumerated()), id: \.offset) { _, entry in
                        VStack(alignment: .leading, spacing: 3) {
                            Text(entry["event_type"] as? String ?? "—")
                                .font(.caption).bold().foregroundColor(.cyan)
                            if let data = entry["data"] as? [String: Any],
                               let summary = data["summary"] as? String {
                                Text(summary).font(.caption2).foregroundColor(.secondary)
                            }
                            if let ts = entry["ts"] as? String {
                                Text(String(ts.prefix(19))).font(.caption2).foregroundColor(.secondary.opacity(0.5))
                            }
                        }
                    }
                }
            }
            .navigationTitle("Memory")
            .refreshable { await client.fetchMemory() }
            .task { await client.fetchMemory() }
        }
    }
}
