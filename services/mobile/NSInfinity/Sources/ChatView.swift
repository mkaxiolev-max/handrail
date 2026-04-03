import SwiftUI

struct ChatView: View {
    @EnvironmentObject var client: NSClient
    @State private var input = ""
    @State private var messages: [(role: String, text: String)] = []
    @State private var isLoading = false
    @State private var hicResult: [String: Any] = [:]

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                if let op = hicResult["op"] as? String {
                    HStack {
                        Image(systemName: "bolt.fill").foregroundColor(.cyan).font(.caption)
                        Text("HIC → \(op)").font(.caption).foregroundColor(.secondary)
                        Spacer()
                        Text(hicResult["risk"] as? String ?? "").font(.caption2)
                            .padding(3).background(Color.cyan.opacity(0.15)).cornerRadius(4)
                    }
                    .padding(.horizontal).padding(.vertical, 4)
                    .background(Color.secondary.opacity(0.05))
                }
                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(alignment: .leading, spacing: 8) {
                            ForEach(Array(messages.enumerated()), id: \.offset) { i, msg in
                                MessageBubble(role: msg.role, text: msg.text).id(i)
                            }
                        }.padding()
                    }
                    .onChange(of: messages.count) { _, _ in
                        if let last = messages.indices.last { proxy.scrollTo(last, anchor: .bottom) }
                    }
                }
                HStack {
                    TextField("Ask NS∞...", text: $input)
                        .textFieldStyle(.roundedBorder)
                        .disabled(isLoading)
                        .onChange(of: input) { _, val in
                            if val.count > 3 {
                                Task {
                                    let r = await client.fetchHIC(val)
                                    await MainActor.run { if r["ok"] as? Bool == true { hicResult = r } }
                                }
                            } else {
                                hicResult = [:]
                            }
                        }
                    Button(action: send) {
                        Image(systemName: isLoading ? "hourglass" : "arrow.up.circle.fill").font(.title2)
                    }.disabled(input.isEmpty || isLoading)
                }.padding()
            }
            .navigationTitle("NS∞")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Circle().fill(client.isConnected ? .green : .red).frame(width: 8, height: 8)
                }
            }
        }
    }

    func send() {
        let text = input.trimmingCharacters(in: .whitespaces)
        guard !text.isEmpty else { return }
        messages.append((role: "user", text: text))
        input = ""
        hicResult = [:]
        isLoading = true
        Task {
            let response = await client.sendChat(text)
            await MainActor.run {
                messages.append((role: "ns", text: response.isEmpty ? "—" : response))
                isLoading = false
            }
        }
    }
}

struct MessageBubble: View {
    let role: String
    let text: String
    var body: some View {
        HStack {
            if role == "user" { Spacer() }
            Text(text)
                .padding(10)
                .background(role == "user" ? Color.blue.opacity(0.8) : Color.secondary.opacity(0.2))
                .foregroundColor(role == "user" ? .white : .primary)
                .cornerRadius(12)
            if role == "ns" { Spacer() }
        }
    }
}
