# NS∞ iOS App

SwiftUI shell for NS∞. Connects to NS via ngrok or production domain.

## Build
Open in Xcode, set team, build to simulator or device (iOS 17+).

## Config
Set NS_BASE_URL env var or it defaults to the ngrok static domain.

## Views
- Chat: text chat with HIC pre-routing display
- Voice: tap-to-call +1(307)202-4418 with HIC phrase suggestions
- Memory: live memory feed
- Status: health + proactive intel from /intel/proactive

## Endpoints used
- GET  /healthz
- POST /chat/quick
- GET  /memory/recent
- GET  /intel/proactive
- POST /hic/compile
