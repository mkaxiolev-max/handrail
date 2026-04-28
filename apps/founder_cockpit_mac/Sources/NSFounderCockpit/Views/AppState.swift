import SwiftUI
import Combine

@MainActor
final class AppState: ObservableObject {
    @Published var services: [ServiceHealth] = []
    @Published var queryResponse: QueryResponse?
    @Published var canonRecords: [CanonRecord] = []
    @Published var contradictions: ContradictionsResponse?
    @Published var contradictionGraph: ContradictionGraph?
    @Published var atoms: [MemoryAtom] = []
    @Published var molecules: [MemoryMolecule] = []
    @Published var storytime: StorytimeResponse?
    @Published var risLanes: [String: RISSingleLane] = [:]
    @Published var readiness: ReadinessPanel?
    @Published var ledger: LedgerHealth?
    @Published var systemState: SystemStateResponse?
    @Published var score: CockpitScore?
    @Published var isPolling = false
    @Published var lastRefresh: Date?

    private var pollingTask: Task<Void, Never>?

    func startPolling() {
        guard !isPolling else { return }
        isPolling = true
        pollingTask = Task {
            while !Task.isCancelled {
                await refresh()
                try? await Task.sleep(nanoseconds: UInt64(RuntimeConfig.pollInterval * 1_000_000_000))
            }
        }
    }

    func stopPolling() {
        pollingTask?.cancel()
        isPolling = false
    }

    func refresh() async {
        async let sv = HealthAPI.checkAll()
        async let cs = try? CanonAPI.list()
        async let ct = try? HandrailAPI.contradictions()
        async let at = try? MemoryAPI.atoms()
        async let mo = try? MemoryAPI.molecules()
        async let st = try? StorytimeAPI.fetch()
        async let rs = try? HandrailAPI.readinessScore()
        async let lh = try? HandrailAPI.ledgerHealth()
        async let ss = try? CommandAPI.systemState()
        async let ris = try? RISAPI.sources()

        let (svr, csr, ctr, atr, mor, str_, rsr, lhr, ssr, risr) =
            await (sv, cs, ct, at, mo, st, rs, lh, ss, ris)

        services = svr
        canonRecords = csr?.records ?? canonRecords
        contradictions = ctr
        atoms = atr?.atoms ?? atoms
        molecules = mor?.molecules ?? molecules
        storytime = str_
        readiness = rsr
        ledger = lhr
        systemState = ssr
        risLanes = risr?.lanes ?? risLanes
        lastRefresh = Date()
        score = AppScoringEngine.compute(state: self)
    }

    func sendQuery(_ prompt: String) async {
        queryResponse = try? await CommandAPI.query(prompt: prompt)
    }
}
