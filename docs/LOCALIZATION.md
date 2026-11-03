# Localisation

The English source contains 191 keys: 190 strings and one plural resource. Structural coverage and linguistic approval are separate. No target language is approved merely because a file exists.

The requested regional targets are en-GB, en-US, en-AU, es-ES, es-419, fr-FR, fr-CA, de-DE, it-IT, pt-BR, pt-PT, nl-NL, pl-PL, sv-SE, ja-JP, hi-IN, ar, tr-TR and id-ID. Standing requirements add ko-KR, zh-Hans and zh-Hant: 22 matrix rows in total.

```powershell
python scripts/localize.py extract
python scripts/localize.py translate --locale fr-FR
python scripts/localize.py validate
python scripts/localize.py validate --strict
python scripts/localize.py generate --locale fr-FR --draft
python scripts/localize.py generate --locale fr-FR
python scripts/localize.py check-release
```

The optional DeepL adapter uses development-only credentials. The default draft workflow now uses a local model without paid services or API keys:

```powershell
python -m venv .translation-venv
.\.translation-venv\Scripts\python.exe -m pip install -r scripts/translation-requirements.txt
.\.translation-venv\Scripts\python.exe scripts/local_translation.py --prepare
python -m venv .translation-runtime
.\.translation-runtime\Scripts\python.exe -m pip install -r scripts/translation-runtime-requirements.txt
.\.translation-runtime\Scripts\python.exe scripts/local_translation.py
.\.translation-runtime\Scripts\python.exe scripts/translate_collateral.py
.\.translation-runtime\Scripts\python.exe scripts/apply_collateral_editorial.py
.\.translation-runtime\Scripts\python.exe scripts/polish_translations.py
.\.translation-runtime\Scripts\python.exe scripts/polish_translations.py --check
```

Inference uses the official [MIT-licensed M2M100 model](https://huggingface.co/facebook/m2m100_418M) at revision `55c2e61bbf05dfb8d7abccdc3fae6fc8512fd636`, converted to int8 using [CTranslate2](https://opennmt.net/CTranslate2/guides/transformers.html). Preparation checks the published weight SHA-256. Setup downloads tools and weights; inference then uses local files. No family content is translated or transmitted. Tools, weights and the segment cache are ignored by Git and never included in the app.

Numbers, format placeholders, identifiers, brand names and supported English command examples are protected outside model inference. The terminology catalogue supplies explicit UI labels and plural forms. OpenCC converts Chinese drafts to the requested script. English US/Australia are source adaptations; other regional variants share initial drafts and require separate dialect review. Machine text can be awkward or inaccurate despite full structural coverage.

Native reviewers record APPROVED, identity, date, sourceHash and targetHash in `localization/reviews.json`. Changing either catalogue invalidates approval. Do not invent reviewers or approve drafts automatically. The validator checks missing/extra keys, types, empty text, brand names, duplicate placeholders and every plural form, including target-specific categories.

The authored final pass is stored in `localization/polish/`. It corrects app messages and rewrites every article in each non-English language, including sensitive availability/privacy copy. Store descriptions are composed from those edited sections and reviewed-draft app notices. Regional adaptations retain separate native review requirements. Run this pass after older model/editorial seeds: CI's `--check` catches regeneration that would restore the earlier rough wording. These are Codex-authored drafts, not native or legal approval. The compact files preserve article structure and are validated before any catalogue is written. `scripts/qa-requirements.txt` supplies the small validation dependencies; model tools are not required for this authored pass.

`generate --draft` writes debug-only Android resources. The normal generation command requires current approval and writes release resources. Build-specific language arrays and Android locale configurations keep unreviewed drafts out of the release picker. `check-release` rejects stale, altered, undeclared or unreviewed release catalogues. CI also runs strict structural validation.

Onboarding and Settings provide a scrollable language picker with native language names and a device-language option. AppCompat stores explicit choices and recreates the activity. Unsupported device languages fall back to English. Arabic uses RTL layout; back arrows and book icons mirror. Dates, years, recording/playback times and album counts follow the active locale. Album counts use Android plural resources, including Arabic and Polish categories. User stories and attachments are unchanged.

The physical LocalizationTest checks all 22 declared debug locales, all string lookups, eight integer plural counts, a manual picker change, English fallback, stored-story preservation, home-heading bounds and Arabic navigation mirroring. The full physical suite passed 9 tests on 2026-11-02. It saved 176 real captures under `deliverables/reports/device-evidence/localization`: home, albums, timeline, keepsakes, settings, editor, voice and transcript for each locale. Test fixtures are explicitly fictional. Personal story text is preserved when changing UI languages. See retained instrumentation.log and result.json for scope.

The captures also back 176 draft store compositions. Other device sizes, portrait orientation, large text, TalkBack pronunciation and native review remain required. Privacy, deletion, consent, purchasing, archive limits and error copy need especially careful semantic review. Some machine-translated copy remains visibly awkward; structural coverage is not translation quality certification.

Voice commands remain explicitly English-only. Recognition and parsing both request English regardless of UI language; the localized notice states this limit and examples preserve supported English phrases. Story TTS requests the selected locale when an installed engine supports it. Multilingual command dictionaries, recorded-file transcription and multilingual speech-device validation remain separate work.

`deliverables/localization/coverage.json` separates app, website, store, distribution and speech status. Website dictionaries contain 163 strings per locale; store drafts contain 23 strings per locale, plus eight screenshot headlines. The local preview exports 352 content pages. Manual selection preserves article paths; browser-language reset uses the validated locale matcher. HTML lang/dir, localized metadata and hreflang are checked. The es-419 URL uses generic es in Google hreflang because numeric region codes are unsupported; Open Graph uses documented territory conventions. See [Google guidance](https://developers.google.com/search/docs/specialty/international/localized-versions) and [Open Graph](https://ogp.me/).

Setting SITE_URL activates production locale isolation: only the English source and genuinely approved source/target hashes are exported. Website reviews live in `website/localization/reviews.json`; app reviews live in `localization/reviews.json`. Both require reviewer identity and date. Preview pages are noindex. Store drafts remain DRAFT_NOT_SUBMISSION_READY and need marketplace mapping, native review and actual release configuration before upload. Amazon's previously uploaded APK and English listings are unchanged.

To reproduce the actual-capture compositions after a passing physical run:

```powershell
python scripts/prepare_localized_screenshots.py
npm ci --prefix website
npx --prefix website playwright install chromium --only-shell
python -m http.server 3011 --bind 127.0.0.1 --directory deliverables
# In a second terminal:
node scripts/render_localized_screenshots.cjs
python scripts/validate_localized_screenshots.py # requires Pillow
```

Rendering uses Playwright with exact 1920 × 1200 output, then validates JPEG encoding, nonblank pixels, dimensions and hashes. It does not manufacture missing UI. The manifest and provenance remain explicitly unapproved. See LOCALIZATION_DELIVERY.md for the current QA evidence and limitations.
