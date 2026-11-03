# Localization delivery — 2 November 2026

Historical initial delivery. The 3 November editorial follow-up and current checks are in [TRANSLATION_POLISH.md](TRANSLATION_POLISH.md).

App, website and store drafts cover 22 locales. All translations remain pending native review. This is a tested localization implementation and review package, not a production-release approval.

## Delivered

- App: 191/191 keys in each catalogue, plural categories, a persistent language picker in onboarding/Settings, device-language fallback, Arabic RTL/mirrored navigation, localized numbers and dates, digit normalization for date input and localized PDF date/page formatting.
- Website: 163 strings per locale and 352 exported content pages, locale-aware HTML/metadata/structured data, browser detection, manual selection, browser-language reset and article-preserving switching.
- Store: 22 listing drafts with title, descriptions, bullets, keywords and release notes; eight localized screenshot headlines each. Metadata limits and placeholders are validated. Marketplace/language mappings and publisher distribution choices remain open.
- Screenshots: 176 landscape Fire tablet compositions based on 176 real locale-matched app captures. Fictional story content remains English intentionally: language switching must preserve user-authored stories. Manifest and source/output hashes accompany the drafts.
- Review workflow: 4,033 app review entries and 3,906 website/store/headline review entries. Machine inference uses the pinned MIT M2M100 model locally, plus curated terminology and draft editorial corrections. No family stories enter the translation tooling.

Locales: en-GB, en-US, en-AU, es-ES, es-419, fr-FR, fr-CA, de-DE, it-IT, pt-BR, pt-PT, nl-NL, pl-PL, sv-SE, ja-JP, hi-IN, ar, tr-TR, id-ID, ko-KR, zh-Hans, zh-Hant.

## Executed QA

|Check|Actual result and scope|
|---|---|
|Kotlin unit tests|9 passed; localized digit normalization and partial-date formatting included|
|Physical Fire suite|9 passed on KFTRWI, Fire OS 7/API 28; 181.635 seconds; app journeys, backup, media and recording plus the localization matrix|
|Localization device matrix|22 locales × 8 screens; all string resolution, eight integer plural counts, French manual picker, unsupported-language English fallback, stored-story preservation, home heading bounds and Arabic mirrored navigation|
|Python localization tests|7 passed; placeholders, plural forms, source/target approval binding and debug-only generation|
|Browser locale matching|17 cases passed|
|Website review gate|6 cases passed using in-memory fixtures; real approval records unchanged|
|Website export|Build passed; 352 content pages pass structural, language/direction, canonical/hreflang, JSON-LD, link and preview-indexing checks|
|Browser interactions|French navigation; French-to-German switch retained /features/; Arabic mobile lang=ar/dir=rtl with no horizontal overflow; browser-language reset returned to en-GB; no console warnings/errors observed in that session|
|Store drafts|22 pass structural/placeholder and Amazon metadata-limit checks|
|Android builds|Debug, unsigned release and test APK builds passed; lint reported 0 errors and 280 warnings in the retained build log|
|Static source patterns|Passed; does not establish a comprehensive security audit|

Retained evidence: `deliverables/android/build-logs/localization-debug-final.log`, `localization-build.log`, `instrumentation.log`, `localization-website-build.log`; `deliverables/reports/device-test-run.json`; `device-evidence/localization/result.json`; `website-checks.json`; `website-localization/`; and `deliverables/localization/`.

The initial device run failed two test readiness checks. Isolated reproductions and explicit activity/keyboard readiness fixes passed, followed by the complete 9-test rerun. Earlier failure logs are retained. Foreground Amazon App Tester activity after teardown was not evidence of interference.

## Release gates and known limits

Zero locales have native approval. Longer machine-translated website articles and store descriptions contain visibly awkward wording and require substantive editing, including sensitive privacy, purchase, deletion and consent language. Regional dialects need separate review. Structural coverage does not certify meaning, grammar or accessibility pronunciation.

Draft app resources are under `src/debug`; release resources/picker remain English. The app gate requires current source and target hashes, reviewer identity and review date. The website exports draft locales only in local preview: a configured SITE_URL enables equivalent production review gating. Preview pages are noindex. Store files are marked DRAFT_NOT_SUBMISSION_READY.

Voice command recognition/parser remain explicitly English. TTS uses the chosen locale only when installed services support it; all 22 speech locales have not been certified. Recorded-file transcription has no configured engine. Billing and receipt verification remain unverified. Portrait/other-device screenshots, large text, TalkBack, broader compatibility, security/legal assessment, signing and final marketplace configuration remain open. Overall release status remains BLOCKED.

The existing Amazon draft was not changed or submitted during this localization pass. No production website was deployed. Source and review artifacts are intended for the authorized GitHub push.

Setup and repeatable generation: [LOCALIZATION.md](LOCALIZATION.md). Release dependencies: [RELEASE_READINESS.md](RELEASE_READINESS.md). Local preview: http://127.0.0.1:3000/en-GB/.
