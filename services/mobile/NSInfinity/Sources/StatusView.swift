import SwiftUI

struct StatusView: View {
    @EnvironmentObject var client: NSClient
    @State private var intel: [[String: Any]] = []

    var body: some View {
        NavigationStack {
            List {
                Section("Connection") {
                    HStack {
                        Circle().fill(client.isConnected ? .green : .red).frame(width: 8, height: 8)
                        Text(client.isConnected ? "NS Online" : "Offline")
                        Spacer()
                        Text(client.baseURL).font(.caption2).foregroundColor(.secondary).lineLimit(1)
                    }
                }
                Section("Health") {
                    ForEach(Array(client.healthStatus.sorted(by: { $0.key < $1.key })), id: \.key) { k, v in
                        HStack {
                            Text(k).font(.caption)
                            Spacer()
                            Text("\(v)").font(.caption2).foregroundColor(.secondary)
                        }
                    }
                }
                Section("Proactive Intel") {
                    if intel.isEmpty {
                        Text("Pull to refresh").foregroundColor(.secondary).font(.caption)
                    } else {
                        ForEach(Array(intel.enumerated()), id: \.offset) { _, s in
                            VStack(alignment: .leading, spacing: 4) {
                                HStack {
                                    let pri = (s["priority"] as? String ?? "low")
                                    Text(pri.uppercased()).font(.caption2)
                                        .padding(.horizontal, 5).padding(.vertical, 2)
                                        .background(priColor(pri).opacity(0.2)).cornerRadius(4)
                                    Spacer()
                                    if let op = s["action_op"] as? String {
                                        Text(op).font(.caption2).foregroundColor(.secondary)
                                    }
                                }
                                Text(s["suggestion"] as? String ?? "").font(.caption)
                            }
                        }
                    }
                }
            }
            .navigationTitle("Status")
            .refreshable {
                await client.checkHealth()
                intel = await client.fetchIntel()
            }
            .task {
                await client.checkHealth()
                intel = await client.fetchIntel()
            }
        }
    }

    func priColor(_ p: String) -> Color {
        switch p { case "critical": return .red; case "high": return .orange; case "medium": return .yellow; default: return .gray }
    }
}
