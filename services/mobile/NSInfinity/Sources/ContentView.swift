import SwiftUI

struct ContentView: View {
    @EnvironmentObject var client: NSClient
    var body: some View {
        TabView {
            ChatView()
                .tabItem { Label("Chat", systemImage: "bubble.left.and.bubble.right") }
            VoiceView()
                .tabItem { Label("Voice", systemImage: "phone.fill") }
            MemoryView()
                .tabItem { Label("Memory", systemImage: "brain") }
            StatusView()
                .tabItem { Label("Status", systemImage: "antenna.radiowaves.left.and.right") }
        }
        .tint(.cyan)
        .onAppear { Task { await client.checkHealth() } }
    }
}
