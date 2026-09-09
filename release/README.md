# Release Artifacts

Built from commit: see `git log -1` (mobile_app/ source).

| File | Purpose | Size |
|---|---|---|
| `app-release.apk` | Install directly on any Android phone (production URL) | ~70 MB |
| `app-debug.apk` | Debug/testing build (arm/arm64) | ~142 MB |
| `app-release.aab` | Upload to Google Play Console | ~62 MB |

These binaries are intentionally NOT tracked in git (GitHub blocks >100 MB
files; repos shouldn't host builds). Rebuild locally with:

    cd mobile_app
    flutter build apk --release && flutter build appbundle --release
    cp build/app/outputs/flutter-apk/app-release.apk  ../release/
    cp build/app/outputs/flutter-apk/app-debug.apk    ../release/
    cp build/app/outputs/bundle/release/app-release.aab ../release/

See docs/ANDROID_BUILD.md for the full guide.
