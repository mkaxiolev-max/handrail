import SwiftUI

struct RealityPanelView: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Reality — Service Health")
                .font(.title2.bold())

            let upCount = appState.services.filter { $0.isUp }.count
            let total = appState.services.count

            HStack {
                Text("\(upCount)/\(total) services up")
                    .font(.subheadline)
                    .foregroundStyle(upCount == total ? .green : upCount > 0 ? .yellow : .red)
                Spacer()
                if let r = appState.lastRefresh {
                    Text("Refreshed \(r.formatted(date: .omitted, time: .standard))")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            LazyVGrid(columns: [GridItem(.adaptive(minimum: 200))], spacing: 12) {
                ForEach(appState.services) { svc in
                    ServiceHealthCard(service: svc)
                }
            }

            if !appState.risLanes.isEmpty {
                Divider()
                Text("RIS Lanes")
                    .font(.headline)
                ForEach(appState.risLanes.sorted(by: { $0.key < $1.key }), id: \.key) { lane, info in
                    HStack {
                        StatusBadge(label: lane, isUp: (info.status ?? "") == "ok")
                        Spacer()
                        if let rc = info.record_count {
                            Text("\(rc) records")
                                .font(.caption.monospaced())
                                .foregroundStyle(.secondary)
                        }
                    }
                }
            }
            Spacer()
        }
        .padding()
    }
}

struct ServiceHealthCard: View {
    let service: ServiceHealth
    var body: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 4) {
                StatusBadge(label: service.label, isUp: service.isUp)
                if service.latencyMs > 0 {
                    Text(String(format: "%.0f ms", service.latencyMs))
                        .font(.caption.monospaced())
                        .foregroundStyle(.secondary)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }
}
