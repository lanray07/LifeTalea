# Release readiness — BLOCKED

Updated 4 November 2026. Current device and collateral checks passed. The original acceptance requirements remain in scope.

The Supabase production verifier is deployed with server-only credentials and its own RSA signing identity. HTTPS health and a signed rejection of synthetic invalid receipt identifiers passed. This does not verify an actual production purchase. See AMAZON_SUPABASE_DEPLOYMENT.md and amazon-supabase-deployment.json.

Amazon Premium was submitted to the TEST channel and is Approved, with the owner's £4.99 UK one-time price and Amazon-calculated marketplace prices. The public app and paid upgrade have not been published. The connected LAT candidate was uploaded and Amazon now reports Test in-progress and the corrected tester invitation Pending (inbox receipt unconfirmed). Invitation redemption/installation and actual purchase verification remain pending. The standard release remains purchases-disabled; the separate LAT candidate uses the deployed URL and public pin.

Real App Tester sandbox tests exposed a canceled-receipt bug. The fixed QA build passed cancellation, purchase-dialog cancellation, fresh purchase, restore and cancellation of the new fulfilled receipt. SDK cancellations now revoke a receipt and prevent a late active response from reinstating it. The account-switch observation belongs to the earlier QA APK and is labelled accordingly. See amazon-billing-sandbox-tests.json.

Current local evidence: 20 Node core tests, three edge adapter tests, 20 Kotlin unit tests and 17/17 physical Fire tests. Lint: 0 errors, 258 warnings. Layout/offline status: PASS. All original device settings, App Tester catalogue and SDK mode were restored. All 176 current-APK screenshot compositions were refreshed and byte-validated; they remain drafts with zero native approvals.

Remaining: deployed-server LAT purchase/restore/cancellation/account/offline tests;  recorded-file transcription; native approval and matching release assets; outstanding product, backup/crash recovery, accessibility/performance/device checks; independent server/client security and final privacy/legal/signing review. No public release readiness or Amazon public approval is claimed. See AMAZON_OWNER_ACTIONS.md.
