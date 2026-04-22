import SwiftUI

struct BuildSpaceView: View {
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "hammer.fill")
                .font(.system(size: 40))
                .foregroundColor(DSColors.accentAmber)
            Text("Build Space")
                .font(.system(size: 28, weight: .black))
                .foregroundColor(DSColors.textPrimary)
            Text("Speculative exterior — Ring 6 and beyond")
                .font(.system(size: 13))
                .foregroundColor(DSColors.textSecondary)
            Text("Ring 5 must be complete before Build Space activates")
                .font(.system(size: 11))
                .foregroundColor(DSColors.textTertiary)
                .padding(10)
                .background(DSColors.surfaceCard)
                .cornerRadius(6)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
