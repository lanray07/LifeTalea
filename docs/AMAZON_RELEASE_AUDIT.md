> Historical pre-RVS snapshot from the earlier 3 November pass. Current billing work: [AMAZON_RVS_IMPLEMENTATION.md](AMAZON_RVS_IMPLEMENTATION.md); current gate state: RELEASE_READINESS.md.

# Amazon release audit — 3 November 2026

**BLOCKED; updated local review package prepared, not approved for submission.** Read RELEASE_READINESS.md and AMAZON_OWNER_ACTIONS.md before using any asset.

Completed locally:

- Retrieved the correct existing public Appstore authentication PEM through the verified LifeTalea console, parsed its RSA public-key type/size and bundled it. The final APK contains matching bytes; no shared secret or private signing key was retrieved.
- Disabled production purchases, production SDK-only entitlement grants and trust in a legacy cached Premium flag pending actual server RVS. Improved debug restore ordering, current-user binding and active-receipt aggregation. These changes do not implement RVS or establish live purchase behavior.
- Duplicated memories now copy independent attachment files and album links; failed copies roll back database work and remove partial copied files.
- Restored keepsake pages get fresh IDs, protecting existing books when archive page IDs collide. Export enforces importer manifest/collection/final-byte bounds. Dates consistently use years 0001–9999.
- Added preservation/date regressions and real audio seek/pause checks; rebuilt and reran local checks, the Fire suite and screenshot exports. Exact results and failed attempts are in TEST_REPORT.md.
- Retired old metadata/report bootstrap scripts that could overwrite authored translations or regenerate obsolete readiness claims. The new package builder reads current files, checks binary/capture provenance and validates its internal manifest. The original acceptance checklist remains in scope; no new completion percentage is invented.
- Prepared a 3,296-character testing-instruction draft (below the observed 4,000-character console limit), an uncreated IAP product draft with prices deliberately pending, draft metadata for 22 locales, icons, 176 landscape compositions and their original captures. QA APK and screenshot drafts are labelled separately from the unsigned English candidate.

Amazon console was inspected read-only: the app is Incomplete; Submit App is disabled; there are zero IAP items; testing instructions are empty; export certification is unchecked. Existing code-1 uploaded APK has DRM applied, but its hash was not obtained and it is not established as the new local candidate. Twelve Fire tablets are selected, with no Fire TV/automotive. The public key was downloaded; no fields, products, prices, uploads or account settings were changed. The browser recheck is recorded in `deliverables/reports/amazon-console-review.json`.

The extra portrait/landscape check at 1.3× font and Wi-Fi-disabled reopen passed (three home-screen cases) after the owner unlocked the tablet. Original settings were restored, and all three images were manually inspected. This remains a limited home-screen smoke, not the full device/accessibility/offline matrix. Earlier Compose startup timeouts remain a separate unresolved test-reliability concern. Formal Security Scan startup failed; narrow static checks do not replace that assessment.

The local ZIP lives under `deliverables/amazon-submission/`. `package-index.json` contains its SHA-256; `audit.json` records provenance and remaining gates. The ZIP is ignored by Git. Its `manifest.json` covers every packaged payload, and `prepare_amazon_submission.py --check` verifies the read-back bytes. No Amazon upload or submission occurred.
