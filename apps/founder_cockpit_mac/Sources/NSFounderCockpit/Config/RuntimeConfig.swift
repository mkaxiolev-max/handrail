import Foundation

enum RuntimeConfig {
    static let handrailBase  = "http://127.0.0.1:8011"
    static let nsCoreBase    = "http://127.0.0.1:9000"
    static let continuumBase = "http://127.0.0.1:8788"
    static let risBase       = "http://127.0.0.1:8014"
    static let ncomBase      = "http://127.0.0.1:9020"
    static let macBase       = "http://127.0.0.1:8765"

    static let pollInterval: TimeInterval = 5.0
    static let requestTimeout: TimeInterval = 8.0
}
