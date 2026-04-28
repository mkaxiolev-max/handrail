import SwiftUI

struct MemoryPanelView: View {
    @EnvironmentObject var appState: AppState
    @State private var tab = 0

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Memory — Atoms & Molecules")
                .font(.title2.bold())

            Picker("", selection: $tab) {
                Text("Atoms (\(appState.atoms.count))").tag(0)
                Text("Molecules (\(appState.molecules.count))").tag(1)
            }
            .pickerStyle(.segmented)
            .frame(maxWidth: 300)

            if tab == 0 {
                if appState.atoms.isEmpty {
                    ContentUnavailableView("No Atoms", systemImage: "circle.dotted",
                                           description: Text("Branch states appear here once committed."))
                } else {
                    List(appState.atoms) { atom in
                        VStack(alignment: .leading, spacing: 2) {
                            HStack {
                                Text(atom.id)
                                    .font(.caption.monospaced())
                                    .foregroundStyle(.secondary)
                                Spacer()
                                Text(String(format: "amp %.2f", atom.amp))
                                    .font(.caption.monospaced())
                                    .foregroundStyle(.secondary)
                            }
                            Text(atom.claim)
                                .font(.body)
                                .lineLimit(2)
                        }
                        .padding(.vertical, 4)
                    }
                    .listStyle(.plain)
                }
            } else {
                if appState.molecules.isEmpty {
                    ContentUnavailableView("No Molecules", systemImage: "link.circle",
                                           description: Text("Molecules form when branches share reinforcement links."))
                } else {
                    List(appState.molecules) { mol in
                        VStack(alignment: .leading, spacing: 4) {
                            Text("members: \(mol.members.joined(separator: " · "))")
                                .font(.caption.monospaced())
                                .foregroundStyle(.secondary)
                            ForEach(mol.claims, id: \.self) { claim in
                                Text("· \(claim)").font(.body).lineLimit(1)
                            }
                        }
                        .padding(.vertical, 4)
                    }
                    .listStyle(.plain)
                }
            }
        }
        .padding()
    }
}
