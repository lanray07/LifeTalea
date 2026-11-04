# Release readiness — BLOCKED

Updated 4 November 2026. Current device and collateral checks passed. The original acceptance requirements remain in scope.

The Supabase production verifier is deployed with server-only credentials and its own RSA signing identity. HTTPS health and a signed rejection of synthetic invalid receipt identifiers passed. Separately, one Amazon-distributed LAT purchase activated Premium through the signed verification path; this is not a public retail launch test. See AMAZON_SUPABASE_DEPLOYMENT.md and amazon-supabase-deployment.json.

Amazon Premium was submitted to the TEST channel and is Approved, with the owner's £4.99 UK one-time price and Amazon-calculated marketplace prices. The public app and paid upgrade have not been published. Amazon reports Test in-progress. The corrected invitation was redeemed and the Amazon-distributed app installed. One authorized purchase activated Premium; restore retained the active entitlement and canceling the earlier confirmation retained Free. The actual final charge is unconfirmed. Initial confirmation needed app resume; fresh restore and LAT revocation/account/offline/reboot cases remain open. See AMAZON_LAT_STATUS.md and amazon-lat-purchase-tests.json. The standard release remains purchases-disabled; the separate LAT candidate uses the deployed URL and public pin.

Real App Tester sandbox tests exposed a canceled-receipt bug. The fixed QA build passed cancellation, purchase-dialog cancellation, fresh purchase, restore and cancellation of the new fulfilled receipt. SDK cancellations now revoke a receipt and prevent a late active response from reinstating it. The account-switch observation belongs to the earlier QA APK and is labelled accordingly. See amazon-billing-sandbox-tests.json.

Current local evidence: 20 Node core tests, three edge adapter tests, 20 Kotlin unit tests and 17/17 physical Fire tests. Lint: 0 errors, 258 warnings. Layout/offline status: PASS. All original device settings, App Tester catalogue and SDK mode were restored. All 176 current-APK screenshot compositions were refreshed and byte-validated; they remain drafts with zero native approvals.

Remaining: first-launch confirmation delay, fresh restore and LAT revocation/account/offline/reboot tests;  recorded-file transcription; native approval and matching release assets; outstanding product, backup/crash recovery, accessibility/performance/device checks; independent server/client security and final privacy/legal/signing review. No public release readiness or Amazon public approval is claimed. See AMAZON_OWNER_ACTIONS.md.

Executed evidence:

- Core Node contract/crypto/HTTP/startup/rate/timeout/key-helper tests: 20/20. These use fictional upstream responses; actual Amazon tests are reported separately.
- Edge adapter tests: three passed (secrets fail closed, request bounds, quota, receipt delegation and error redaction).
- Kotlin: 20 passed, including SDK revocation identity/epoch binding and rejection of late active responses after cancellation. The retained red regression log demonstrates the original bug.
- Physical KFTRWI, Fire HD 10 (2021), Fire OS 7/API 28: 17/17 passed in 182.529 seconds, including 4 signed-receipt fixture tests, core writing/media/backup/PDF/short recording flows and the 22-locale capture matrix. This suite uses the standard debug APK; SDK App Tester uses a separate QA APK with its own hash.
- Three home-screen layout checks: portrait/landscape at 1.3× text and Wi-Fi-disabled reopen. Scope excludes full-screen accessibility and prolonged offline Premium behavior.
- All 13 collateral groups passed: Python, locale resources/isolation, editorial regression, metadata, browser locale/review/static-export, TypeScript, website structure and narrow source patterns.
- 176 current-APK screenshot drafts byte-validated. Native approvals: zero. Five fresh visual samples were reviewed and their exact hashes recorded; this is not a complete visual or native-language review.
- Supabase service-role-only quota RPC access verified; anon/authenticated execute denied; private quota RLS enabled. No customer identifiers are stored in that table. Security-advisor no-policy notice is intentional deny-all for normal roles. Existing project password warning was not changed.

Earlier failed locale/layout runs are retained as historical evidence. Their later success does not establish reliability on every device. Docker execution, an independent security audit, native-language review, legal review and the remaining LAT recovery/revocation/account matrix remain unverified. One LAT purchase activated Premium; no further payment was attempted.
