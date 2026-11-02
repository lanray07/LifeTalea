# LifeTalea research and release constraints

Checked 2 November 2026. These are source findings, not completed application tests, legal clearance or account configuration. No console changes or submissions were made.

## Amazon submission requirements

Tablet listing requirements include 3–10 screenshots (PNG/JPEG, either orientation); icons at 114² and 512²; a plain-text long description up to 4,000 characters; and a short description limited to 2,000 bytes. Amazon describes the latter as approximately 1,200 English characters. Use both a conservative character check and UTF-8 byte validation. The current submission guide recommends 3–5 feature bullets and confirms an optional comma-separated keywords field. Screenshot dimensions and icon format are recorded in REQUIREMENTS.json. Show the actual app with fictional data, without photographs of someone using it. [Submission guide](https://developer.amazon.com/docs/app-submission/appstore-details.html).

Amazon's older ASO article specifies a 200-character display title and allows more feature bullets than the newer submission guide. Prefer 3–5 and verify the title in the console before submission. The proposed title is 42 characters. [Amazon ASO guidance](https://developer.amazon.com/apps-and-games/blogs/2024/06/app-store-optimization).

### Store languages are not app languages or countries

Amazon documents Dutch, Australian/Indian/US English, French, German, Italian, Japanese, Polish, Brazilian/European Portuguese, Spanish and Swedish storefront localisations. Its console illustration also shows UK English and Mexican Spanish; the prose and illustration are inconsistent. Confirm regional fields in the actual submission interface. Arabic, Hindi, Turkish, Indonesian, Korean and Chinese can be binary-language targets without assuming corresponding storefront fields. Distribution is selected separately under availability, and a marketplace may serve multiple countries. Keep the country selection pending the publisher's decision. [International distribution](https://www.developer.amazon.com/docs/app-submission/distribute-your-app-internationally.html).

### Important secondary-platform constraint

Amazon discontinued its Appstore for non-Amazon Android devices on 20 August 2025; Fire tablets and Fire TV remain supported. A phone-compatible APK does not establish an Amazon phone distribution channel. Plan a separate secondary distribution/billing build when the publisher chooses that channel. [Amazon announcement](https://developer.amazon.com/apps-and-games/blogs/2025/02/upcoming-changes-to-amazon-appstore-for-android-devices-and-coins-program).

## Amazon purchasing

Official integration instructions demonstrate pinned SDK `com.amazon.device:amazon-appstore-sdk:3.0.9` and require the app-specific public `AppstoreAuthenticationKey.pem` under the Android assets directory. Obtain it from the correct app/version in the Developer Console; it is not a secret API credential. Do not substitute another application's key. [SDK integration](https://developer.amazon.com/docs/appstore-sdk/integrate-appstore-sdk.html).

Mode detection uses `LicensingService.getAppstoreSDKMode()` after `LicensingService.verifyLicense()`. States distinguish SANDBOX, PRODUCTION and UNKNOWN; UNKNOWN indicates the SDK has not been initialised. Production grants must reject sandbox/unknown responses. [Transition guide](https://developer.amazon.com/docs/in-app-purchasing/transitioning-to-appstore-sdk.html).

App Tester supplies sandbox API responses. DevTest supports local end-to-end testing with SDK 3.0.3+ on Fire OS 6+ without uploading a binary. LAT exercises Amazon production services for selected testers without charging them. Amazon's test process also includes server-side Receipt Verification Service validation. Until product configuration, authentication, receipt verification and required purchase/restore/cancel/failure tests are completed, billing stays BLOCKED. [IAP testing overview](https://developer.amazon.com/docs/in-app-purchasing/iap-testing-overview.html).

## Name and competing approaches

A limited exact-name web query for “LifeTalea” produced no reliable exact-match product evidence in this session. That is not a trademark, company, domain or Appstore-name search clearance. Retain the working name pending formal searches in intended jurisdictions and actual listing availability.

| Product | First-party evidence | Implication for LifeTalea |
|---|---|---|
| StoryCorps | Guided mobile interviews and archive upload are part of its documented workflow. [Product page](https://storycorps.org/participate/storycorps-app/) | A local-only default can be a useful distinction; do not claim competitors lack private options. |
| Storii | Its FAQ describes scheduled telephone life-story calls and online story access. [FAQ](https://www.storii.com/faqs) | Tablet-first self-directed capture differs from a telephone service. |
| Remento | Recorded stories can appear in books as transcripts or transformed narratives; book ordering is part of its workflow. [Book help](https://help.remento.co/en/articles/8365908-how-do-i-order-and-print-my-book) | Editable local stories and local PDF export can serve users who prefer to manage preservation themselves. |

These are feature comparisons, not usability studies or market-demand validation. No download, conversion, revenue or search-volume figures were obtained.

## Product and keyword hypotheses

Audience hypothesis: adults recording relatives' stories and families organising old photographs may value a calm tablet interface without mandatory accounts. Validate through observed interviews and task tests before treating it as demand evidence.

| Search intent hypothesis | Destination | Proof required before advertising |
|---|---|---|
| family memory journal / private family journal | Home, journal page | CRUD and persistence |
| record family stories / voice journal | Recording page | Hardware recording and playback |
| organise old family photographs | Albums page | Import, album organisation |
| digital scrapbook / family memory timeline | Scrapbook, timeline pages | Draft/reorder/filter tests |
| printable family memory book | Keepsake page | PDF validation and billing entitlement |
| offline memory journal | Offline page | Network-disabled journeys |
| transcribe family recordings | Transcription status page | A real configured engine; currently unavailable |

This mapping has no volume or ranking evidence. Translate intent naturally after native review; do not mechanically repeat phrases or advertise unverified features. The one-time Premium price is the user's proposed commercial assumption, not research-derived willingness to pay.

## Remaining research gates

- Confirm exact listing-locale variants, title field limit and distribution choices in the correct developer account.
- Complete trademark/name clearance and publisher identity/contact information.
- Test representative Fire models and OS versions; API compatibility alone is insufficient.
- Evaluate transcription unit economics before including a paid cloud service in a one-time entitlement.
- Check final legal/privacy disclosures against real integrations before publishing.
