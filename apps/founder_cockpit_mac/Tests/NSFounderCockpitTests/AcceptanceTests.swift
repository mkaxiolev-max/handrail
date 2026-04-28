import XCTest
@testable import NSFounderCockpit

final class AcceptanceTests: XCTestCase {
    func testEndpointRegistryHas14Entries() {
        XCTAssertGreaterThanOrEqual(EndpointRegistry.all.count, 14,
                                    "Registry should cover all 14 monitored endpoints")
    }

    func testQueryRoutesThroughIMOGate() async throws {
        let resp = try await CommandAPI.query(prompt: "acceptance smoke test")
        XCTAssertFalse(resp.verb.isEmpty, "verb must not be empty")
        let validVerbs = ["collapse_ready", "hold_ncom", "force_more_branches", "abort"]
        XCTAssertTrue(validVerbs.contains(resp.verb),
                      "verb \(resp.verb) is not a valid IMO gate verb")
        XCTAssertGreaterThanOrEqual(resp.confidence, 0.0)
        XCTAssertLessThanOrEqual(resp.confidence, 1.0)
    }

    func testCanonListResponds() async throws {
        let canon = try await CanonAPI.list()
        XCTAssertGreaterThanOrEqual(canon.count, 0)
    }

    func testContradictionListResponds() async throws {
        let ct = try await HandrailAPI.contradictions()
        XCTAssertGreaterThanOrEqual(ct.count, 0)
        XCTAssertGreaterThanOrEqual(ct.pressure_score, 0.0)
        XCTAssertLessThanOrEqual(ct.pressure_score, 1.0)
    }

    func testMemoryAtomsRespond() async throws {
        let atoms = try await MemoryAPI.atoms()
        XCTAssertGreaterThanOrEqual(atoms.count, 0)
    }

    func testStorytimeResponds() async throws {
        let st = try await StorytimeAPI.fetch()
        XCTAssertFalse(st.rule.isEmpty, "Storytime rule must not be empty")
    }

    func testNCOMReadinessResponds() async throws {
        let rs = try await HandrailAPI.readinessScore()
        XCTAssertEqual(rs.panel, "readiness_score")
    }

    func testLedgerHealthResponds() async throws {
        let lh = try await HandrailAPI.ledgerHealth()
        XCTAssertNotNil(lh.all_chains_valid, "Ledger health must report chain validity")
        XCTAssertTrue(lh.all_chains_valid == true, "All ledger chains must be valid")
    }
}
