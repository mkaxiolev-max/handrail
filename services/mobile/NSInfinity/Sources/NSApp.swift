import SwiftUI

@main
struct NSInfinityApp: App {
    @StateObject private var client = NSClient()
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(client)
        }
    }
}
