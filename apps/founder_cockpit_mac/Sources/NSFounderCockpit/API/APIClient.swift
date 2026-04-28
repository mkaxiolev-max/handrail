import Foundation

enum APIError: Error, LocalizedError {
    case badURL
    case httpError(Int)
    case decodingError(Error)
    case networkError(Error)

    var errorDescription: String? {
        switch self {
        case .badURL:               return "Bad URL"
        case .httpError(let c):     return "HTTP \(c)"
        case .decodingError(let e): return "Decode: \(e.localizedDescription)"
        case .networkError(let e):  return e.localizedDescription
        }
    }
}

actor APIClient {
    static let shared = APIClient()

    private let session: URLSession = {
        let cfg = URLSessionConfiguration.default
        cfg.timeoutIntervalForRequest = RuntimeConfig.requestTimeout
        cfg.timeoutIntervalForResource = RuntimeConfig.requestTimeout
        return URLSession(configuration: cfg)
    }()

    func get<T: Decodable>(_ urlString: String) async throws -> T {
        guard let url = URL(string: urlString) else { throw APIError.badURL }
        do {
            let (data, resp) = try await session.data(from: url)
            if let http = resp as? HTTPURLResponse, !(200..<300).contains(http.statusCode) {
                throw APIError.httpError(http.statusCode)
            }
            do {
                return try JSONDecoder().decode(T.self, from: data)
            } catch {
                throw APIError.decodingError(error)
            }
        } catch let e as APIError { throw e }
        catch { throw APIError.networkError(error) }
    }

    func post<Req: Encodable, Res: Decodable>(_ urlString: String, body: Req) async throws -> Res {
        guard let url = URL(string: urlString) else { throw APIError.badURL }
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try JSONEncoder().encode(body)
        do {
            let (data, resp) = try await session.data(for: req)
            if let http = resp as? HTTPURLResponse, !(200..<300).contains(http.statusCode) {
                throw APIError.httpError(http.statusCode)
            }
            do {
                return try JSONDecoder().decode(Res.self, from: data)
            } catch {
                throw APIError.decodingError(error)
            }
        } catch let e as APIError { throw e }
        catch { throw APIError.networkError(error) }
    }

    func checkHealth(_ urlString: String) async -> (Bool, Double) {
        guard let url = URL(string: urlString) else { return (false, -1) }
        let start = Date()
        do {
            let (_, resp) = try await session.data(from: url)
            let ms = Date().timeIntervalSince(start) * 1000
            let ok = (resp as? HTTPURLResponse).map { (200..<300).contains($0.statusCode) } ?? false
            return (ok, ms)
        } catch {
            return (false, -1)
        }
    }
}
