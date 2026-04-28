import Foundation

struct Endpoint: Identifiable {
    let id: String
    let url: String
    let method: String
    let label: String
    var status: EndpointStatus = .unknown
}

enum EndpointStatus {
    case ok, degraded, down, unknown
    var color: String {
        switch self {
        case .ok:      return "green"
        case .degraded: return "yellow"
        case .down:    return "red"
        case .unknown: return "gray"
        }
    }
}

enum EndpointRegistry {
    static let all: [Endpoint] = [
        Endpoint(id: "handrail_health",    url: RuntimeConfig.handrailBase  + "/healthz",                method: "GET", label: "Handrail"),
        Endpoint(id: "ns_core_health",     url: RuntimeConfig.nsCoreBase    + "/healthz",                method: "GET", label: "NS Core"),
        Endpoint(id: "continuum_health",   url: RuntimeConfig.continuumBase + "/continuum/status",       method: "GET", label: "Continuum"),
        Endpoint(id: "ris_sources",        url: RuntimeConfig.risBase        + "/ris/sources",            method: "GET", label: "RIS"),
        Endpoint(id: "ncom_health",        url: RuntimeConfig.ncomBase       + "/ncom/healthz",           method: "GET", label: "NCOM"),
        Endpoint(id: "mac_health",         url: RuntimeConfig.macBase        + "/healthz",                method: "GET", label: "Mac Adapter"),
        Endpoint(id: "router_decision",    url: RuntimeConfig.nsCoreBase    + "/router/decision",        method: "GET", label: "Router"),
        Endpoint(id: "ether_trace",        url: RuntimeConfig.nsCoreBase    + "/ether/retrieval_trace",  method: "GET", label: "Ether"),
        Endpoint(id: "system_state",       url: RuntimeConfig.nsCoreBase    + "/system/state",           method: "GET", label: "System State"),
        Endpoint(id: "canon",              url: RuntimeConfig.nsCoreBase    + "/canon",                  method: "GET", label: "Canon"),
        Endpoint(id: "contradictions",     url: RuntimeConfig.nsCoreBase    + "/contradictions",         method: "GET", label: "Contradictions"),
        Endpoint(id: "memory_atoms",       url: RuntimeConfig.nsCoreBase    + "/memory/atoms",           method: "GET", label: "Atoms"),
        Endpoint(id: "memory_molecules",   url: RuntimeConfig.nsCoreBase    + "/memory/molecules",       method: "GET", label: "Molecules"),
        Endpoint(id: "storytime",          url: RuntimeConfig.nsCoreBase    + "/storytime",              method: "GET", label: "Storytime"),
    ]
}
