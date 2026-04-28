// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "NSFounderCockpit",
    platforms: [.macOS(.v14)],
    products: [
        .executable(name: "NSFounderCockpit", targets: ["NSFounderCockpit"]),
    ],
    dependencies: [],
    targets: [
        .executableTarget(
            name: "NSFounderCockpit",
            path: "Sources/NSFounderCockpit",
            resources: [
                .process("Resources"),
            ]
        ),
        .testTarget(
            name: "NSFounderCockpitTests",
            dependencies: ["NSFounderCockpit"],
            path: "Tests/NSFounderCockpitTests"
        ),
    ]
)
