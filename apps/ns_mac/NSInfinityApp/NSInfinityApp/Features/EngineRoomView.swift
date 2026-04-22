import SwiftUI

struct EngineRoomView: View {
    @State private var cpsInput: String = ""
    @State private var cpsResult: String = ""
    @State private var isExecuting = false
    @State private var executionHistory: [(String, Bool)] = []   // (op, success)

    var body: some View {
        HStack(spacing: 0) {
            // Left: CPS execution
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    Text("Engine Room")
                        .font(.habitatTitle())
                        .foregroundColor(DSColors.textPrimary)

                    // CPS execution panel
                    VStack(alignment: .leading, spacing: 10) {
                        SectionHeader(title: "CPS EXECUTION — POST /ops/cps")

                        ZStack(alignment: .topLeading) {
                            if cpsInput.isEmpty {
                                Text(#"{"ops": [{"op": "fs.pwd"}]}"#)
                                    .font(.habitatMono())
                                    .foregroundColor(DSColors.textTertiary)
                                    .padding(.leading, 9).padding(.top, 9)
                                    .allowsHitTesting(false)
                            }
                            TextEditor(text: $cpsInput)
                                .font(.habitatMono())
                                .foregroundColor(DSColors.textPrimary)
                                .scrollContentBackground(.hidden)
                                .background(Color.clear)
                                .frame(height: 130)
                        }
                        .padding(8)
                        .background(DSColors.surfaceCard)
                        .cornerRadius(6)
                        .overlay(RoundedRectangle(cornerRadius: 6)
                            .stroke(isExecuting ? DSColors.violet.opacity(0.5) : DSColors.surfaceBorder, lineWidth: 1))

                        HStack(spacing: 10) {
                            Button("Execute") {
                                Task { await executeCPS() }
                            }
                            .disabled(cpsInput.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isExecuting)
                            .buttonStyle(PrimaryButtonStyle())

                            if isExecuting {
                                ProgressView().scaleEffect(0.65)
                                Text("executing…").font(.system(size: 10)).foregroundColor(DSColors.textTertiary)
                            }

                            Spacer()

                            Button("Clear") { cpsInput = ""; cpsResult = "" }
                                .buttonStyle(.plain)
                                .font(.system(size: 11))
                                .foregroundColor(DSColors.textTertiary)
                        }

                        if !cpsResult.isEmpty {
                            Text(cpsResult)
                                .font(.habitatMono(10))
                                .foregroundColor(cpsResult.hasPrefix("ERROR") ? DSColors.offline : DSColors.accentCyan)
                                .padding(10)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .background(DSColors.surfaceCard)
                                .cornerRadius(6)
                        }
                    }

                    // Quick ops
                    VStack(alignment: .leading, spacing: 8) {
                        SectionHeader(title: "QUICK OPS")
                        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible())], spacing: 8) {
                            ForEach(quickOps, id: \.0) { op, plan in
                                QuickOpButton(label: op) {
                                    cpsInput = prettyPrint(plan)
                                    Task { await executeCPS() }
                                }
                            }
                        }
                    }
                }
                .padding(24)
            }
            .frame(maxWidth: .infinity)

            // Right: execution history
            VStack(alignment: .leading, spacing: 0) {
                Rectangle().fill(DSColors.surfaceBorder).frame(width: 1)
            }
            .frame(width: 1)

            VStack(alignment: .leading, spacing: 0) {
                VStack(alignment: .leading, spacing: 6) {
                    SectionHeader(title: "EXECUTION HISTORY")
                        .padding(.horizontal, 14).padding(.top, 16)
                    Divider().overlay(DSColors.surfaceBorder)
                    ScrollView {
                        VStack(spacing: 4) {
                            if executionHistory.isEmpty {
                                Text("No executions yet").font(.system(size: 10))
                                    .foregroundColor(DSColors.textTertiary).padding(12)
                            } else {
                                ForEach(Array(executionHistory.reversed().enumerated()), id: \.offset) { _, h in
                                    HStack(spacing: 6) {
                                        Circle().fill(h.1 ? DSColors.online : DSColors.offline).frame(width: 5, height: 5)
                                        Text(h.0).font(.habitatMono(9)).foregroundColor(DSColors.textSecondary).lineLimit(1)
                                    }
                                    .padding(.horizontal, 12).padding(.vertical, 3)
                                }
                            }
                        }
                    }
                }
                Spacer()
            }
            .frame(width: 200)
            .background(DSColors.surfaceElevated)
        }
    }

    let quickOps: [(String, String)] = [
        ("fs.pwd",        #"{"ops":[{"op":"fs.pwd"}]}"#),
        ("git.status",    #"{"ops":[{"op":"git.status"}]}"#),
        ("sys.uptime",    #"{"ops":[{"op":"sys.uptime"}]}"#),
        ("docker.ps",     #"{"ops":[{"op":"docker.compose_ps"}]}"#),
        ("ns.flywheel",   #"{"ops":[{"op":"ns.flywheel"}]}"#),
        ("ns.capability", #"{"ops":[{"op":"ns.capability_graph"}]}"#),
    ]

    func executeCPS() async {
        let raw = cpsInput.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let data = raw.data(using: .utf8),
              let plan = try? JSONSerialization.jsonObject(with: data) as? [String: Any]
        else {
            cpsResult = "ERROR: invalid JSON"
            return
        }
        isExecuting = true
        let opName = (plan["ops"] as? [[String: Any]])?.first?["op"] as? String ?? "cps"
        do {
            let result = try await RuntimeAPIClient.shared.executeCPS(plan: plan)
            let out = try JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys])
            cpsResult = String(data: out, encoding: .utf8) ?? "{}"
            executionHistory.append((opName, true))
        } catch {
            cpsResult = "ERROR: \(error.localizedDescription)"
            executionHistory.append((opName, false))
        }
        isExecuting = false
    }

    func prettyPrint(_ raw: String) -> String {
        guard let data = raw.data(using: .utf8),
              let obj = try? JSONSerialization.jsonObject(with: data),
              let pretty = try? JSONSerialization.data(withJSONObject: obj, options: .prettyPrinted),
              let str = String(data: pretty, encoding: .utf8)
        else { return raw }
        return str
    }
}

struct PrimaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 12, weight: .semibold))
            .foregroundColor(.white)
            .padding(.horizontal, 14)
            .padding(.vertical, 7)
            .background(DSColors.violet.opacity(configuration.isPressed ? 0.65 : 1.0))
            .cornerRadius(6)
    }
}

private struct QuickOpButton: View {
    let label: String
    let action: () -> Void
    var body: some View {
        Button(action: action) {
            Text(label)
                .font(.habitatMono(10))
                .foregroundColor(DSColors.accentCyan)
                .padding(.horizontal, 8)
                .padding(.vertical, 6)
                .frame(maxWidth: .infinity)
                .background(DSColors.surfaceCard)
                .cornerRadius(5)
                .overlay(RoundedRectangle(cornerRadius: 5).stroke(DSColors.surfaceBorder, lineWidth: 1))
        }
        .buttonStyle(.plain)
    }
}

#Preview {
    EngineRoomView()
        .frame(width: 1000, height: 700)
        .preferredColorScheme(.dark)
}
