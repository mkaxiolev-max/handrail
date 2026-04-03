import SwiftUI

struct VoiceView: View {
    @State private var calling = false
    var body: some View {
        NavigationStack {
            VStack(spacing: 24) {
                Spacer()
                ZStack {
                    if calling {
                        Circle().stroke(Color.cyan.opacity(0.3), lineWidth: 2)
                            .frame(width: 120, height: 120)
                            .scaleEffect(calling ? 1.4 : 1)
                            .animation(.easeOut(duration: 1).repeatForever(), value: calling)
                    }
                    Circle().fill(Color.cyan.opacity(0.15)).frame(width: 90, height: 90)
                    Image(systemName: calling ? "phone.fill" : "phone").font(.system(size: 40)).foregroundColor(.cyan)
                }
                Text("NS∞ Voice").font(.title2).bold()
                Text("+1 (307) 202-4418").font(.title3).foregroundColor(.secondary)
                Text("HIC-routed · memory-aware · always on").font(.caption).foregroundColor(.secondary)
                Button(calling ? "Calling..." : "Call NS∞") {
                    calling = true
                    if let url = URL(string: "tel:13072024418") {
                        UIApplication.shared.open(url)
                    }
                    DispatchQueue.main.asyncAfter(deadline: .now() + 3) { calling = false }
                }
                .buttonStyle(.borderedProminent)
                .tint(.cyan)
                .disabled(calling)
                VStack(alignment: .leading, spacing: 6) {
                    Text("Try saying:").font(.caption).foregroundColor(.secondary)
                    ForEach(["What time is it", "Check my memory", "What should I focus on", "System status"], id: \.self) { phrase in
                        HStack {
                            Image(systemName: "chevron.right").font(.caption2).foregroundColor(.cyan)
                            Text(phrase).font(.caption)
                        }
                    }
                }.padding()
                Spacer()
            }
            .navigationTitle("Voice")
        }
    }
}
