# LifeTalea

Private family stories, photographs, voice memories and keepsakes. Native Kotlin/Jetpack Compose for Fire tablets, with a Next.js marketing website.

**Development preview — release BLOCKED.** This repository is not an approved or production-ready Amazon Appstore release. The evidence and remaining gates are recorded in [Release readiness](docs/RELEASE_READINESS.md) and [Test report](docs/TEST_REPORT.md).

Publisher: **O.Bankole** · Support: **banksmi@mail.com** · [Source repository](https://github.com/lanray07/LifeTalea)

## Implemented source

- Room-backed memories and albums, many-to-many organisation, approximate/unknown dates, tags, favourites, search and timeline.
- Private photograph import and foreground voice recording with pause/resume, local playback and editable manual transcripts.
- English command parser, optional device SpeechRecognizer and TextToSpeech with touch/text alternatives.
- Scrapbook drafts, page ordering, captions, layout choices and local PDF generation.
- Local archive export, integrity validation, restore preview, duplicate preservation and optional AES-GCM archive encryption.
- Free/Premium boundaries and Amazon SDK adapter; purchasing remains disabled without the correct app authentication/product configuration.
- Translation extraction, provider/cache/placeholder validation and review-gated Android resource generation.
- Original book/waveform identity, generated editorial illustration, editable covers/backgrounds and screenshot source template.
- Website preview with 352 localized pages across 22 locales, language switching, RTL, structured data, metadata, sitemap, privacy and support content.

Automatic recorded-file transcription is **unavailable**. All 22 app catalogues have 191/191 structurally valid keys; debug builds include translated drafts, while release builds retain English until native approval. Website/store drafts and 176 tablet screenshot drafts are prepared. Native review remains incomplete, and some machine-translated article wording is visibly rough. Voice commands remain English; speech services vary by device. Archives have a 32 MiB total/16 MiB per-item limit. See [localization delivery](docs/LOCALIZATION_DELIVERY.md) for evidence and limits.

## Run locally

Use JDK 17, Android SDK platform/build tools 35 and the committed Gradle wrapper. Configure `ANDROID_HOME` or untracked `android/local.properties`. No backend or API key is required for local memory functionality.

```powershell
.\android\gradlew.bat -p android --no-daemon testDebugUnitTest assembleDebug assembleRelease
npm ci --prefix website
npm run build --prefix website
python -m http.server 3000 --directory website/out
```

Open http://localhost:3000/en-GB/. Debug installs use `com.lifetalea.app.debug`; the provisional production ID is `com.lifetalea.app`. The unsigned release is `android/app/build/outputs/apk/release/app-release-unsigned.apk`. Final workspace artifact paths and checksums are listed in `deliverables/DELIVERABLES_MANIFEST.csv`. APKs/build caches are generated locally and are not committed as source.

## Delivery documentation

|Area|Documentation|
|---|---|
|Architecture and scope|[Architecture](docs/ARCHITECTURE.md), [Implementation plan](docs/IMPLEMENTATION_PLAN.md)|
|Build/configuration|[Build and release](docs/BUILD_AND_RELEASE.md), [development env template](.env.example), [website env template](website/.env.example)|
|Tests and release gates|[Test report](docs/TEST_REPORT.md), [Acceptance criteria](deliverables/reports/ACCEPTANCE_CRITERIA.md), [Results CSV](deliverables/reports/ACCEPTANCE_TEST_RESULTS.csv)|
|Languages|[Localisation workflow and target list](docs/LOCALIZATION.md), [coverage report](deliverables/reports/LOCALIZATION_TEST_REPORT.md)|
|Voice and transcripts|[Voice capabilities](docs/VOICE_COMPATIBILITY.md), [Transcription status](docs/TRANSCRIPTION.md)|
|Purchasing|[Monetisation](docs/MONETIZATION.md), [Amazon test report](deliverables/reports/AMAZON_BILLING_TEST_REPORT.md)|
|Privacy/preservation|[Privacy notice](docs/PRIVACY_POLICY.md), [Security](docs/PRIVACY_AND_SECURITY.md), [Backup](docs/BACKUP_AND_RESTORE.md)|
|Store preparation|[Submission guide](docs/AMAZON_SUBMISSION.md), [Draft metadata](deliverables/store-assets/metadata/en-GB/listing.json), [Screenshot matrix](deliverables/store-assets/manifests/required-screenshots.csv)|
|Compatibility/research|[Fire report](deliverables/reports/FIRE_DEVICE_COMPATIBILITY.md), [Primary-source research](docs/RESEARCH.md)|
|Design/assets|[Design review](docs/DESIGN_REVIEW.md), [Asset provenance](deliverables/brand-assets/PROVENANCE.md)|
|Inventory|[Deliverables manifest](deliverables/DELIVERABLES_MANIFEST.csv)|

## Before publication

Complete the transcription integration; correct and natively review all locale drafts; finish other device-size screenshot variants; configure and verify Amazon purchases/receipts; broaden Fire/orientation/accessibility/offline tests; harden archive storage for larger libraries; complete the security/privacy assessment; confirm signing, package/product identity, marketplace availability and name clearance. Publication requires explicit authorisation.

Amazon no longer distributes its Appstore on non-Amazon Android devices. A compatible phone APK needs a separate selected distribution and billing channel. No live store URL or website deployment is claimed. GitHub source, policy and support documentation are the current public destinations.
