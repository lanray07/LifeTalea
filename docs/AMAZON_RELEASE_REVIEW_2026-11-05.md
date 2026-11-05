# LifeTalea Amazon release review — 5 November 2026

**Public submission is blocked.** Amazon's public review screen showed Ready to Submit, version code 1, English, 12 of 40 Fire tablets selected, no TV or automotive devices selected, and no testing instructions. The public description still contains a development-status notice. The visible filename and version code do not establish the exact APK bytes. Test 1 is live on version code 2.

The version 2 Appstore update installed over version 1 on the first Fire HD 10 with the same signing certificate. Premium stayed active after restore, a short Wi-Fi-off refresh and reconnection. A second Fire HD 10 used a direct installation of the verified Amazon-distributed version 2 APK. Premium restored on its first launch and remained active after manual restore. Amazon confirmed an entitlement reset for the selected tester. A cold launch then showed Free tier. The purchase confirmation was visible by 4.3 seconds after the first tap, and Back returned to Free tier. No payment was submitted during that run. Reboot recovery, account switching and interruption during purchase remain open.

The live verifier returned healthy and signed an inactive response for synthetic invalid receipt identifiers. All 23 verifier and edge tests passed. The 20 Android unit tests and 17 physical Fire instrumentation tests passed for the billing lifecycle update. Those debug results and the Amazon-installed results have separate APK provenance.

Before public submission:

- Verify the exact public candidate, its purchase configuration and its published Premium item. Review supported devices and countries, replace development copy with descriptions of the shipped features, validate screenshots and save reviewer instructions.
- Complete the agreed native-language approvals and remaining device, accessibility, performance and recovery checks. The original requirements also include recorded-file transcription and other product work listed in `KNOWN_LIMITATIONS.md`.
- Complete the independent security assessment and the publisher's final privacy, provider, export and store disclosure review. Review the verifier's LAT test-receipt setting when transitioning to public billing.

This package includes historical 4 November evidence as a separate archive and the current version 2 LAT files as separate entries. Use the historical archive for provenance and the 5 November reports for current results. The unsigned version 2 APK is the LAT upload, and the public draft has its own release ID.
