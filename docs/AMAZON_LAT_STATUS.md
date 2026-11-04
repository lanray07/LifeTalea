# Amazon LAT status - 4 November 2026

Amazon reports **Test in-progress** for LifeTalea billing verification 2026-11-04. The corrected tester invitation was redeemed and the app installed through the connected tablet's Amazon Appstore LAT notification. The canonical `com.lifetalea.app` package reports installer `com.amazon.venezia`; SDK sandbox mode remained `none`. The connected tablet was the 7th Fire; initial web delivery selected the 9th Fire, so installation used the connected tablet's own notification.

The Amazon-distributed APK signature verifies. SHA-256: `520f9eb047802364d50a9f427c80930d67f73ca24a877c52091629a070ad3ec8`. Its three DEX files match the unsigned LAT upload byte for byte. Production endpoint, signing pin, authentication PEM and exported components were checked; sandbox trust and fixtures are absent. See `amazon-distributed-apk-inspection.json`. Update continuity and independent security assessment remain unverified.

One authorized Premium transaction completed and the app displayed **Premium is active**. The inspected code grants this only after validating the deployed receipt service's signed assertion. Authorization was GBP4.99 maximum total including tax; confirmation displayed GBP4.99 and Verify and Pay. The actual final charge is unconfirmed. Amazon's [LAT tester guidance](https://developer.amazon.com/docs/app-testing/prepare-app-testers.html) describes zero-cost test IAP; this report does not claim a verified GBP0 charge. No second payment is authorized or attempted.

Observed tests on this exact Amazon-distributed APK:

- Purchase: Free changed to Premium after one confirmation submission.
- Restore with existing active entitlement: Premium remained active. Cleared-cache or fresh-install regrant was not tested.
- Canceled purchase dialog: Back canceled the first confirmation; Free remained and Get Premium reenabled.
- First-launch issue: the first request did not display confirmation for several minutes. Home/reopen displayed it; the later request appeared promptly. Cause is unproven. Investigate lifecycle registration and retest first launch using [Amazon SDK guidance](https://developer.amazon.com/docs/in-app-purchasing/iap-implement-iap.html).
- Offline: Wi-Fi disabled and cached Premium visible before refresh. Foreground changed to another app during the subsequent check; offline refresh/reboot recovery remains unverified. Wi-Fi restored enabled; no reboot or account change performed.
- LAT receipt revocation, account switching, interrupted purchase and fresh restore remain open. Separate App Tester regression results are not substitutes for LAT cases.

App-only evidence images and hashes are in `amazon-lat-purchase-tests.json`. Raw receipts, order details, tester contacts, invitation tokens and the downloaded APK are excluded from Git and the review package. Original power settings were restored; SDK mode was unchanged. No preexisting production memories/media were edited or deleted; first-run onboarding was completed in the new installation.

Public release remains **BLOCKED**. First-launch confirmation delay, remaining LAT matrix, independent security/privacy/legal review, native-language approvals, transcription and outstanding product/device/accessibility requirements remain open. The formal security scan failed at startup; no audit result exists. See AMAZON_OWNER_ACTIONS.md. Standard release purchases remain disabled; the separate LAT build uses the production endpoint and public pin.
