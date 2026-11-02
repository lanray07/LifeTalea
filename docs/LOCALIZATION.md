# Localisation

English is the current source language, not a worldwide launch claim. `localization/en-GB.json` and Android `values/strings.xml` contain 190 source keys. The generated coverage report records exact current counts. No target language is approved merely because a file exists.

The requested regional targets are en-GB, en-US, en-AU, es-ES, es-419, fr-FR, fr-CA, de-DE, it-IT, pt-BR, pt-PT, nl-NL, pl-PL, sv-SE, ja-JP, hi-IN, ar, tr-TR and id-ID. Standing requirements add ko-KR, zh-Hans and zh-Hant: 22 matrix rows in total.

```powershell
python scripts/localize.py extract
python scripts/localize.py translate --locale fr-FR
python scripts/localize.py validate
python scripts/localize.py generate --locale fr-FR
```

Translation uses the development-only DEEPL_AUTH_KEY environment variable and official free/paid DeepL endpoints. No key enters the APK. Provider execution is blocked while credentials are missing. Regional dialect quality must be reviewed separately even where the provider uses a broader target language. The glossary protects the brand and defines ambiguous terminology. Format placeholders and brand text are protected with ignored XML tags, cached by source/locale hash, and validated after translation. Provider errors stop the command rather than marking a locale complete.

Each native reviewer records APPROVED, reviewer identity, date and exact sourceHash in `localization/reviews.json`. Resource generation requires a matching approval. A changed source hash invalidates it. This review record is an attestation workflow, not an automated linguistic quality guarantee. Future plural resources are extracted and validated, including mandatory `other`; language-specific categories need native review.

Android follows the device locale, supports an explicit English override and reliable English fallback. RTL is declared in the manifest; physical RTL, expanded text, plural forms and multilingual accessibility still need testing. Only reviewed dictionaries should be added to command parsing. No user story is translated automatically.

`deliverables/localization/coverage.json` keeps app, website, store, distribution, speech recognition, TTS and transcription status separate. Amazon listing-locale variants need console confirmation; not every binary language has a store listing field. Website/store translation and screenshot composition remain blocked on approved copy; the current pipeline directly generates Android resources, and website/store translation adapters remain to be completed.
