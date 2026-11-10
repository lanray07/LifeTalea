# Localisation

Updated 10 November 2026 for candidate version 6. All 22 app catalogues contain 212 keys. The owner explicitly authorised Codex to review and approve the language. Complete app and website catalogues, regional differences, store copy and eight screenshot headlines per locale have been reviewed and corrected. Records identify AI editorial review, source and target hashes, reviewer and date. No native-speaker certification is claimed.

Supported locales: en-GB, en-US, en-AU, es-ES, es-419, fr-FR, fr-CA, de-DE, it-IT, pt-BR, pt-PT, nl-NL, pl-PL, sv-SE, ja-JP, hi-IN, ar, tr-TR, id-ID, ko-KR, zh-Hans and zh-Hant.

App approvals are in localization/reviews.json; website approvals are in website/localization/reviews.json; store approvals are in localization/store-reviews.json. Changes to either source or target invalidate approval. Structural checks alone never approve language. Heuristic flags are suggestions, not automatic rejection or certification. Historical queue filenames containing native-review are retained for compatibility; their status fields describe the actual current review.

Run:

```powershell
python -m unittest discover -s tests
python scripts/localize.py validate --strict
python scripts/localize.py check-release
python scripts/polish_translations.py --check
python scripts/validate_collateral.py
python scripts/localization_review_queue.py
node scripts/test_website_review_gate.cjs
```

The source is Android strings.xml. The optional translation adapters and legacy editorial seeds are development tools. They must not overwrite hash-bound reviewed copy. Debug overlays are checked against current catalogues so stale English resources cannot shadow reviewed release strings. All 22 locales are now included in the candidate's release language picker and Android locale configuration. Unsupported languages fall back to English; users may select a language manually or follow the device setting. Arabic mirrors navigation. Dates, numbers, recording times and plurals follow the selected locale. Family content is never translated automatically.

The first version 6 physical suite passed 26 cases on KFTRWI / API 28, including all 22 locales and 176 captures of real screens with fictional fixtures. It checked string resolution, plural examples, picker recreation, English fallback, story preservation, heading bounds and Arabic navigation. A later debug-only stale English note was removed; the rebuilt QA APK subsequently passed its own full 26-test device run. Its 176 fresh captures now back the separately validated localized-v6 asset set. Complete visual approval and other device sizes remain separate. Consult deliverables/reports/release-v6-2026-11-10/ for the exact APK hashes and scope. Earlier November captures and bundles remain historical evidence and must not be relabelled as version 6 assets.

Website structure/export checks cover 352 content pages across all 22 locales, locale metadata, links and preview indexing. Editorial approval and browser layout review are separate. Site publication remains distinct from generating the static export.

Voice commands explicitly support English only and depend on an installed recognition service. TTS depends on installed voices for the selected locale. Saved-recording transcription runs locally; short English-fixture checks do not qualify accuracy across languages or accents. All notices state the relevant limitations. Do not market unsupported multilingual recognition.

Store copy and screenshot headlines have AI editorial approval. All 176 current screenshot exports now pass byte/dimension, nonblank, headline and capture/build provenance checks. Complete clipping/readability review, marketplace mapping and Amazon's actual saved metadata are separate gates. Existing draft assets are not automatically approved by a copy review. Other tablet sizes, portrait/large-text layouts and screen-reader pronunciation still need the applicable current-build evidence.

See RELEASE_V6_REVIEW_2026-11-10.md for current release status; older dated reports retain their original scope. AI language approval does not waive privacy, security, billing, preservation or device gates.
