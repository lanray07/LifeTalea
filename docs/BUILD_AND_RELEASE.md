# Build and release

Publisher: O.Bankole. Support: banksmi@mail.com. Repository: https://github.com/lanray07/LifeTalea.

Install JDK 17 and Android SDK platform/build tools 35. Set `ANDROID_HOME` or create untracked `android/local.properties` with `sdk.dir=/absolute/path/to/Android/Sdk`. Use the committed Gradle 8.13 wrapper. The build uses AGP 8.9.2 and Kotlin 2.1.20. First dependency resolution needs network access.

```powershell
.\android\gradlew.bat -p android --no-daemon testDebugUnitTest assembleDebug assembleRelease
.\android\gradlew.bat -p android --no-daemon connectedDebugAndroidTest
.\android\gradlew.bat -p android --no-daemon lintDebug
```

Run Gradle invocations sequentially against this checkout. Overlapping builds can contend for Windows dex files. Device tests target the separate debug package `com.lifetalea.app.debug`; JourneyTest creates explicitly fictional demonstration records. It never seeds the production package. VoiceDeviceTest records a brief foreground microphone diagnostic and deletes its raw recording. Use a dedicated QA device/profile.

Debug output: `android/app/build/outputs/apk/debug/app-debug.apk`. Release output: `android/app/build/outputs/apk/release/app-release-unsigned.apk`. The release artifact is intentionally unsigned. No production keystore or signing secret was generated. Before public release, confirm application ID `com.lifetalea.app`, product SKU `com.lifetalea.premium`, version 0.1.0/code 1 and Amazon signing requirements. Both IDs are provisional until confirmed in the correct developer listing.

Keep signing material outside the repository. Amazon's submission flow applies its distribution signature, but confirm the chosen app's update/signing identity before submitting any binary. Do not reuse another application's authentication PEM.

For the marketing site:

```powershell
npm ci --prefix website
npm run build --prefix website
python scripts/check_website.py
python -m http.server 3000 --directory website/out
```

`website/out` contains static HTML. Default preview canonical URLs use localhost, with noindex/robots disallow. Configure a verified production SITE_URL only when a real hosting destination is ready. The GitHub repository and Markdown policy/support URLs are real source destinations; no GitHub Pages deployment is claimed or configured automatically. A repository Pages deployment would also need a `/LifeTalea` base-path strategy and link/image validation. Do not point canonical URLs at an unconfirmed live site.

CI in `.github/workflows/verify.yml` runs on pull requests or manual dispatch. It builds Android, runs unit tests/lint, builds the site and checks localisation tooling. Physical Fire, billing, microphone and localisation review remain separate gates; a green CI run does not certify store readiness.
