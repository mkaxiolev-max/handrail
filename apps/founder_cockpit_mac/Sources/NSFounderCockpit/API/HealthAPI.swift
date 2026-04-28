import Foundation

struct HealthAPI {
    private struct SimpleHealth: Decodable {
        let status: String?
        let ok: Bool?
        let service: String?
    }

    static func checkAll() async -> [ServiceHealth] {
        let endpoints: [(id: String, label: String, url: String)] = [
            ("handrail",   "Handrail",    RuntimeConfig.handrailBase  + "/healthz"),
            ("ns_core",    "NS Core",     RuntimeConfig.nsCoreBase    + "/healthz"),
            ("continuum",  "Continuum",   RuntimeConfig.continuumBase + "/continuum/status"),
            ("ris",        "RIS",         RuntimeConfig.risBase       + "/ris/sources"),
            ("ncom",       "NCOM :9020",  RuntimeConfig.ncomBase      + "/ncom/healthz"),
            ("mac",        "Mac Adapter", RuntimeConfig.macBase       + "/healthz"),
        ]
        return await withTaskGroup(of: ServiceHealth.self) { group in
            for ep in endpoints {
                group.addTask {
                    let (ok, ms) = await APIClient.shared.checkHealth(ep.url)
                    return ServiceHealth(id: ep.id, label: ep.label, isUp: ok,
                                         latencyMs: ms, raw: ok ? "ok" : "unreachable")
                }
            }
            var results: [ServiceHealth] = []
            for await h in group { results.append(h) }
            return results
        }
    }
}
