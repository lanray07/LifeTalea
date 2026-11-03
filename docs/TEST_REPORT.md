# Current RVS evidence — UI QA INCOMPLETE / release BLOCKED

20 server tests and 18 unit tests passed. The last physical run on the current debug app passed 17/17, including all 4 receipt tests. All current instrumentation tests passed, including the corrected full 22-locale capture test. The separate current-app layout smoke is INCOMPLETE: 2 cases completed; failure: RuntimeError: ADB operation failed: ('shell', 'uiautomator', 'dump'). Original QA settings were restored.

All 176 current-APK screenshot compositions were refreshed and byte-validated; they remain drafts with zero native approvals. A fresh unlocked-device layout/offline check remains required. This report records incomplete QA; it does not waive a release gate.

Server RVS/client implementation and local tests are complete enough to review; deployment, real credentials/TLS/public pin, product/prices, live Amazon transactions and independent security/privacy/legal/native/remaining product gates remain open. No deployment or submission occurred. See AMAZON_RVS_IMPLEMENTATION.md and amazon-rvs-verification.json for exact hashes and scope.

## Executed evidence

- Node server: 20/20 local contract/crypto/HTTP/startup/key-helper tests. No real Amazon receipts or credentials.
- Kotlin unit tests: 18 passing, current JUnit XML retained.
- Fire: 17/17 passed on the current debug app, including all 4 signed-receipt tests. All current instrumentation tests passed, including the corrected full 22-locale capture test.
- Android build: debug/release/test APKs and lint completed in amazon-rvs-build.log; the later test-only build is amazon-rvs-test-readiness-build.log. Lint: 0 errors and 260 warnings. Release is unsigned, verifier URL/pin empty, and purchases off.
- All 12 non-device collateral groups passed: server/Python tests, locale resources/isolation, authored-copy checks, metadata, browser locale/review/static-export regressions, TypeScript, exported website structure and narrow source patterns. These are not independent security or native linguistic approval.
- Screenshots: All 176 current-APK screenshot compositions were refreshed and byte-validated; they remain drafts with zero native approvals. The validator requires a passing current full run and per-capture byte hashes for a refresh. Native approvals remain zero.
- Layout/offline: The separate current-app layout smoke is INCOMPLETE: 2 cases completed; failure: RuntimeError: ADB operation failed: ('shell', 'uiautomator', 'dump').

Current instrumentation evidence is in instrumentation.log. Historical locale failures are retained in amazon-rvs-device-first-failed.log and amazon-rvs-device-navigation-failed.log. The layout capture failure is retained in amazon-rvs-layout-first-failed.log. The follow-up locked-device preflight changed no settings; the corrected capture retry has not completed on the tablet. Original power/rotation/font/Wi-Fi settings from the executed runs were restored. Docker execution and independent security assessment remain unverified.
