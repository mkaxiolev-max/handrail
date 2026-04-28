import XCTest
@testable import NSFounderCockpit

final class ScoringEngineTests: XCTestCase {
    @MainActor
    func testScoreComputesWithEmptyState() async {
        let state = AppState()
        let score = AppScoringEngine.compute(state: state)
        XCTAssertEqual(score.dimensions.count, 9, "Must have 9 scoring dimensions")
        XCTAssertGreaterThanOrEqual(score.score100, 0)
        XCTAssertLessThanOrEqual(score.score100, 100)
    }

    @MainActor
    func testGradeMapping() {
        let state = AppState()
        state.services = [
            ServiceHealth(id: "ns_core", label: "NS Core", isUp: true, latencyMs: 5, raw: "ok"),
            ServiceHealth(id: "ncom",    label: "NCOM",    isUp: true, latencyMs: 3, raw: "ok"),
            ServiceHealth(id: "mac",     label: "Mac",     isUp: true, latencyMs: 2, raw: "ok"),
        ]
        let score = AppScoringEngine.compute(state: state)
        XCTAssertNotNil(score.grade)
        XCTAssertTrue(["S","A","B","C","F"].contains(score.grade))
    }

    @MainActor
    func testAllDimensionsHaveLabels() {
        let state = AppState()
        let score = AppScoringEngine.compute(state: state)
        for dim in score.dimensions {
            XCTAssertFalse(dim.label.isEmpty, "Each dimension must have a label")
            XCTAssertFalse(dim.id.isEmpty,    "Each dimension must have an id")
        }
    }

    func testWeightsAreBalanced() {
        let score = CockpitScore(dimensions: [
            .init(id: "t1", label: "T1", score: 10, note: ""),
            .init(id: "t2", label: "T2", score: 10, note: ""),
            .init(id: "t3", label: "T3", score: 10, note: ""),
            .init(id: "t4", label: "T4", score: 10, note: ""),
            .init(id: "t5", label: "T5", score: 10, note: ""),
            .init(id: "t6", label: "T6", score: 10, note: ""),
            .init(id: "t7", label: "T7", score: 10, note: ""),
            .init(id: "t8", label: "T8", score: 10, note: ""),
            .init(id: "t9", label: "T9", score: 10, note: ""),
        ])
        XCTAssertEqual(score.score100, 100.0, accuracy: 0.01)
        XCTAssertEqual(score.grade, "S")
    }
}
