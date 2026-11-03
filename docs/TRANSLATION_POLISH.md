# Translation polish — 3 November 2026

The app, website and store drafts received 4,327 field changes compared with commit `b55f040`: 1,823 app fields, 2,238 website fields and 266 store fields. Nineteen translated locale variants changed; all 22 locales remain in the validation matrix. English source/regional variants were retained. No native approvals were added.

The authored correction set is in `localization/polish/`. It replaces literal or mixed-language phrases in onboarding, dates, search, voice, book layouts, backups, purchases and support. All 15 website articles were rewritten for each base non-English language and adapted to regional variants. Store descriptions, bullets, keywords and release notes use that edited copy. English voice-command examples remain exact supported phrases; personal stories are never translated by this tooling.

Examples include French “Actualiser” replacing “Réfrigérer” for Refresh, “Version gratuite” replacing “Terre libre”, natural labels for page captions and previews, and explicit statements that microphone denial does not prevent writing. Purchase notices retain the no-charge warning when billing is unconfigured. Free-tier copy explicitly retains unlimited written memories and the three-minute recording limit. Privacy, archive-size, transcription, cloud-sync and development-status disclosures remain present.

## Checks

|Check|Result and scope|
|---|---|
|Android build|PASS: debug, unsigned release, test APK, unit-test task and lint; 0 lint errors, 260 warnings. Nine passing Kotlin/JUnit results retained; unchanged unit work can be reused by Gradle.|
|Fire device suite|PASS: nine tests on KFTRWI / Fire OS 7 / API 28, 178.956 seconds; captures eight real screens in each of 22 locales.|
|Python|11 tests passed, including complete authored datasets, command phrase boundaries and safe Portuguese word substitutions.|
|Draft and review gates|Strict 191/191 app-key coverage per locale; website/store validation for 22 locales; 17 browser-locale matching cases and six website review-gate cases passed. Zero native approvals.|
|Website build and static checks|PASS: final Next build, static-export postprocessing and all 352 content pages checked.|
|Rendered website|PASS: 132 checks covering 22 locales, three articles and desktop/mobile widths (1280/390); exact edited paragraphs, lang/dir, no horizontal overflow, headings and overlays checked. French-to-German article preservation and German header navigation passed; no console errors/warnings or failed HTTP requests remained.|
|Store screenshots|176 refreshed 1920 × 1200 JPEG compositions exported from the current physical captures. Nonblank pixels, dimensions, encoding, hashes and image similarity to each locale-matched capture were checked.|

The initial physical run timed out waiting for Compose UI roots in two tests; seven passed. An isolated JourneyTest passed, a normal activity launch completed, and the final complete fresh-QA run passed all nine tests. No app runtime fix or definite root cause is claimed for that initial readiness failure. Failure and final logs are retained.

Browser inspection confirmed polished French/German article text and article-preserving language switching. In-app automation then timed out during the Arabic mobile check. Playwright is the fallback already allowed by the project testing instructions. Temporary browser sizing reset was attempted but the browser control remained unresponsive. The separate Playwright session uses its own browser context. Language choices were exercised through the local preview's selector; its browser-language button resets that preference.

Expanded browser checks also found Windows static-export prefetch 404s. The pinned Next 16.4.4 export used OS path separators in nested payload filenames while the client requested dotted names. `normalize_static_export.cjs` supplies byte-identical aliases after each build, preserving the existing payloads and HTML. The narrow reproduction went from 404s to clean navigation; the complete browser rerun passed. The regression test checks the exact requested name, bytes, idempotence, unchanged HTML and conflicting-alias refusal. No dependency upgrade or installed-library patch was needed.

Actual manual app samples in this pass: French Settings, Arabic editor and Traditional Chinese keepsakes. Other current captures are checked automatically; automated checks cannot establish native fluency, pronunciation or exhaustive visual accessibility. The image validator no longer automatically claims that manual samples were reviewed.

## Reproduce and review

```powershell
python -m pip install -r scripts/qa-requirements.txt
python scripts/polish_translations.py --check
python -m unittest discover -s tests -v
python scripts/localize.py validate --strict
python scripts/localize.py check-release
python scripts/validate_collateral.py
node scripts/test_locale_match.cjs
node scripts/test_website_review_gate.cjs
node scripts/test_static_export.cjs
npm run build --prefix website
python scripts/check_website.py
# Serve website/out on localhost:3000, then:
node scripts/check_polished_website.cjs
```

For regeneration, run `polish_translations.py` after the older model/editorial seeds; model inference is not needed for the authored pass. CI's `--check` prevents restoration of the known rough wording. Keep authored files and generated catalogues aligned during native review, then record real source/target hashes, reviewer identity and date. The apply command refuses to overwrite approved copy; check mode writes no review approvals.

Evidence: `deliverables/localization/polish-changes.json` contains exact before/after values and baseline commit; `native-review-queue.csv` and `collateral-native-review-queue.csv` contain the refreshed review work. Current APK hashes are in `deliverables/android/localization-artifacts.json`. Build logs are `translation-polish-verified-build.log`, `translation-polish-final-website.log` and `translation-polish-checks.log`; physical evidence is `instrumentation.log`, `device-test-run.json` and `device-evidence/localization/`. Browser evidence is `deliverables/reports/website-localization-polish/`.

All translations remain editorial drafts. Native/dialect and legal review, larger-font and broader device checks, billing verification, transcription integration and the other release gates remain incomplete. Release languages remain English; draft app languages remain debug-only and website drafts remain preview-only. No Amazon listing was edited or submitted and no production site was deployed.
