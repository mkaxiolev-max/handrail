import Foundation

@MainActor
final class WebSocketClient: NSObject, ObservableObject, URLSessionWebSocketDelegate {
    static let shared = WebSocketClient()

    @Published var lastPanelPayload: [String: Any] = [:]
    @Published var isConnected = false

    private var task: URLSessionWebSocketTask?
    private lazy var session = URLSession(configuration: .default, delegate: self, delegateQueue: nil)

    func connect() {
        guard let url = URL(string: RuntimeConfig.ncomBase + "/ncom/ws") else { return }
        task = session.webSocketTask(with: url)
        task?.resume()
        isConnected = true
        receive()
    }

    func disconnect() {
        task?.cancel(with: .normalClosure, reason: nil)
        isConnected = false
    }

    private func receive() {
        task?.receive { [weak self] result in
            switch result {
            case .success(let msg):
                if case .string(let text) = msg,
                   let data = text.data(using: .utf8),
                   let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                    Task { @MainActor in self?.lastPanelPayload = json }
                }
                Task { @MainActor in self?.receive() }
            case .failure:
                Task { @MainActor in self?.isConnected = false }
            }
        }
    }

    nonisolated func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask,
                                didCloseWith closeCode: URLSessionWebSocketTask.CloseCode, reason: Data?) {
        Task { @MainActor in self.isConnected = false }
    }
}
