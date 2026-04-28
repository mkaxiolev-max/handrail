import XCTest
@testable import NSFounderCockpit

final class APIClientTests: XCTestCase {
    func testHealthCheckReturnsTrueForLiveNSCore() async throws {
        let (ok, ms) = await APIClient.shared.checkHealth(RuntimeConfig.nsCoreBase + "/healthz")
        XCTAssertTrue(ok, "NS Core /healthz should return 200")
        XCTAssertGreaterThan(ms, 0, "Latency should be positive")
    }

    func testHealthCheckReturnsFalseForDeadPort() async throws {
        let (ok, _) = await APIClient.shared.checkHealth("http://127.0.0.1:1/nope")
        XCTAssertFalse(ok, "Dead port should return false")
    }

    func testAllServicesHealthBatch() async throws {
        let results = await HealthAPI.checkAll()
        XCTAssertFalse(results.isEmpty, "Should return health for all registered services")
        let nsCore = results.first(where: { $0.id == "ns_core" })
        XCTAssertNotNil(nsCore, "ns_core should be in health results")
        XCTAssertTrue(nsCore?.isUp == true, "NS Core should be up during acceptance")
    }

    func testNCOMHealthCheck() async throws {
        let (ok, _) = await APIClient.shared.checkHealth(RuntimeConfig.ncomBase + "/ncom/healthz")
        XCTAssertTrue(ok, "NCOM dashboard on :9020 should be reachable")
    }

    func testMacAdapterHealthCheck() async throws {
        let (ok, _) = await APIClient.shared.checkHealth(RuntimeConfig.macBase + "/healthz")
        XCTAssertTrue(ok, "Mac Adapter on :8765 should be reachable")
    }
}
