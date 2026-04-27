// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "NSMac",
    platforms: [.macOS(.v13)],
    products: [
        .library(name: "NSMac", targets: ["NSMac"]),
    ],
    targets: [
        .target(
            name: "NSMac",
            path: "Sources/NSMac"
        ),
        .testTarget(
            name: "NSMacTests",
            dependencies: ["NSMac"],
            path: "Tests/NSMacTests"
        ),
    ]
)
