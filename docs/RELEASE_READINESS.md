# Release readiness — BLOCKED

Current public draft: verified version 4, revised English copy and transcription reviewer instructions saved and read back on 10 November. Not submitted.

10 November: version 4 is live on Amazon Test 1 and installed through the Appstore over version 3. The Amazon signing identity, all DEX files, both native transcription libraries and model were verified. Fictional English processing/review/edit/append, invalid-audio/manual fallback, reset-account restore and unpaid purchase cancellation passed. Only the three owner-approved QA packages were removed to free space; the regular app was retained. See AMAZON_RELEASE_REVIEW_2026-11-10.md. Public submission remains blocked by the remaining release gates.

Earlier reports below retain their dates and scope.

Updated 4 November 2026. Current device and collateral checks passed. The original acceptance requirements remain in scope.

The Supabase production verifier is deployed with server-only credentials and its own RSA signing identity. HTTPS health and a signed rejection of synthetic invalid receipt identifiers passed. Separately, one Amazon-distributed LAT purchase activated Premium through the signed verification path; this is not a public retail launch test. See AMAZON_SUPABASE_DEPLOYMENT.md and amazon-supabase-deployment.json.

Amazon Premium was submitted to the TEST channel and is Approved, with the owner's £4.99 UK one-time price and Amazon-calculated marketplace prices. The public app and paid upgrade have not been published. Amazon reports Test in-progress. The corrected invitation was redeemed and the Amazon-distributed app installed. One authorized purchase activated Premium; restore retained the active entitlement and canceling the earlier confirmation retained Free. The actual final charge is unconfirmed. Initial confirmation needed app resume; fresh restore and LAT revocation/account/offline/reboot cases remain open. See AMAZON_LAT_STATUS.md and amazon-lat-purchase-tests.json. The standard release remains purchases-disabled; the separate LAT candidate uses the deployed URL and public pin.

Real App Tester sandbox tests exposed a canceled-receipt bug. The fixed QA build passed cancellation, purchase-dialog cancellation, fresh purchase, restore and cancellation of the new fulfilled receipt. SDK cancellations now revoke a receipt and prevent a late active response from reinstating it. The account-switch observation belongs to the earlier QA APK and is labelled accordingly. See amazon-billing-sandbox-tests.json.

Current local evidence: 20 Node core tests, three edge adapter tests, 20 Kotlin unit tests and 17/17 physical Fire tests. Lint: 0 errors, 258 warnings. Layout/offline status: PASS. All original device settings, App Tester catalogue and SDK mode were restored. All 176 current-APK screenshot compositions were refreshed and byte-validated; they remain drafts with zero native approvals.

Remaining: first-launch confirmation delay, fresh restore and LAT revocation/account/offline/reboot tests;  recorded-file transcription; native approval and matching release assets; outstanding product, backup/crash recovery, accessibility/performance/device checks; independent server/client security and final privacy/legal/signing review. No public release readiness or Amazon public approval is claimed. See AMAZON_OWNER_ACTIONS.md.
