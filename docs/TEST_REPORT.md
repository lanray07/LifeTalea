# Current RVS evidence — UI QA INCOMPLETE / release BLOCKED

20 server tests and 18 unit tests passed. The last physical run on the current debug app passed 16/17, including all 4 receipt tests, but the locale UI test failed. The subsequent test-only navigation-readiness update is built but has not been executed on the locked tablet. The current test APK must not be described as fully verified. The layout smoke was not rerun on this app. Power/rotation settings from the failed run were restored.

No validated current screenshot set is included in the partial review package. Older screenshots and earlier passing runs are historical evidence. A fresh unlocked-device batch and full capture validation remain required. This report is a deliberate incomplete-QA disposition, not a waiver or a passing release gate.

Server RVS/client implementation and local tests are complete enough to review; deployment, real credentials/TLS/public pin, product/prices, live Amazon transactions and independent security/privacy/legal/native/remaining product gates remain open. No deployment or submission occurred. See AMAZON_RVS_IMPLEMENTATION.md and amazon-rvs-verification.json for exact hashes and scope.

## Executed evidence

- Node server: 20/20 local contract/crypto/HTTP/startup/key-helper tests. No real Amazon receipts or credentials.
- Kotlin unit tests: 18 passing, current JUnit XML retained.
- Fire: 16/17 passed on the current debug app, including all 4 signed-receipt tests; the full suite failed its locale navigation test. The subsequent test-only readiness build has not run.
- Android build: debug/release/test APKs and lint completed in amazon-rvs-build.log; the later test-only build is amazon-rvs-test-readiness-build.log. Lint: 0 errors and 260 warnings. Release is unsigned, verifier URL/pin empty, and purchases off.
- All 12 non-device collateral groups passed: server/Python tests, locale resources/isolation, authored-copy checks, metadata, browser locale/review/static-export regressions, TypeScript, exported website structure and narrow source patterns. These are not independent security or native linguistic approval.
- Historical screenshot bytes retain their original APK provenance. The validator now refuses to relabel them as current and requires a passing full run plus capture-byte hashes before a refresh. No current screenshot set or layout smoke is certified.

Current raw failure evidence: instrumentation.log, amazon-rvs-device-first-failed.log and amazon-rvs-device-navigation-failed.log. The latest locked-device preflight stopped before installing, clearing QA data or changing power settings. Original power/rotation settings from the executed runs were restored. Docker execution and independent security assessment remain unverified.
