// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "NSInfinity",
    platforms: [.iOS(.v17), .macOS(.v14)],
    products: [
        .executable(name: "NSInfinity", targets: ["NSInfinity"])
    ],
    targets: [
        .executableTarget(
            name: "NSInfinity",
            path: "Sources",
            swiftSettings: [
                .unsafeFlags(["-Xfrontend", "-disable-reflection-metadata"])
            ]
        )
    ]
)
