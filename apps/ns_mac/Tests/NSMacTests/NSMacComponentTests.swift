import XCTest
@testable import NSMac

final class NSMacComponentTests: XCTestCase {
    func testAllComponentsEnumerated() {
        XCTAssertEqual(NSMacRuntime.components.count, 5)
    }
    func testVersionIsCanonical() {
        XCTAssertEqual(NSMacRuntime.version, "1.0")
    }
    func testUnknownComponentRejected() {
        XCTAssertFalse(NSMacRuntime.componentExists("PhantomComponent"))
    }
    func testComponentEnumStable() {
        let expected = ["FounderHome","LivingArchitecture","VoicePanel","ScoreHistory","KeyboardHandler"]
        XCTAssertEqual(NSMacRuntime.components, expected)
    }
}
