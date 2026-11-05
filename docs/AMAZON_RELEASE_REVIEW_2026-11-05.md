# LifeTalea Amazon release review — 5 November 2026

**Public submission is blocked.** Amazon accepted `LifeTalea-0.1.0-public-v3-unsigned.apk` as the public draft's version code 3. The review page shows the new English (U.S.) short and long descriptions and 1,092 characters of reviewer instructions. Targeting shows 12 of 40 Fire tablets and zero TV or automotive devices. Test 1 is live on version code 2. The Premium item is still marked TEST in Amazon's IAP dashboard.

The version 3 release build passed Android packaging and APK inspection. Its DEX includes the production verifier URL and public signing pin, and the merged manifest passed the exported-component allowlist. The unsigned upload SHA-256 is `4e0e94c22fcd3054eb1aa2975f5424c91900be7fba98364f94b6e67ac40be2b2`. Amazon's review page confirms its filename and version code. A download attempt did not yield the stored version 3 APK, so the Amazon-processed bytes and runtime behavior remain unverified. Two of the three DEX files matched version 2 byte for byte. The third differed, so version 2 runtime results are recorded separately.

The version 2 Appstore update installed over version 1 on the first Fire HD 10 with the same signing certificate. Premium stayed active after restore, a short Wi-Fi-off refresh and reconnection. A second Fire HD 10 used a direct installation of the verified Amazon-distributed version 2 APK. Premium restored on its first launch and remained active after manual restore. Amazon confirmed an entitlement reset for the selected tester. A cold launch then showed Free tier. The purchase confirmation was visible by 4.3 seconds after the first tap, and Back returned to Free tier. No payment was submitted during that run. Reboot recovery, account switching and interruption during purchase remain open.

The live verifier returned healthy and signed an inactive response for synthetic invalid receipt identifiers. All 23 verifier and edge tests passed. The 20 Android unit tests and 17 physical Fire instrumentation tests passed for the billing lifecycle update. Those debug results and the Amazon-installed results have separate APK provenance.

Before public submission:

- Verify the Amazon-processed version 3 candidate on Fire and complete the public Premium item workflow. Review supported devices and countries, validate screenshots against the release build, and finalize billing-specific copy and review steps when the item is ready.
- Complete the agreed native-language approvals and remaining device, accessibility, performance and recovery checks. The original requirements also include recorded-file transcription and other product work listed in `KNOWN_LIMITATIONS.md`.
- Complete the independent security assessment and the publisher's final privacy, provider, export and store disclosure review. Review the verifier's LAT test-receipt setting when transitioning to public billing.

This package includes historical 4 November evidence, the version 2 LAT files and the unsigned version 3 public draft candidate under separate paths. Rebuild version 3 with `assembleRelease`, `lifetaleaPurchasesEnabled=true`, `lifetaleaRvsUrl` set to the deployed production verify endpoint and `lifetaleaRvsPublicKey` set to the public SPKI in `server/receipt-verifier/supabase/public-signing-key.json`.
