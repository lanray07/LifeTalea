Product/privacy update (10 November 2026): 51 PASS, 152 NOT TESTED, 55 BLOCKED out of 258. Mixed historical inventory; not a full version 5 retest. See product-privacy-2026-11-10/acceptance-update.json.

Current update (10 November 2026): Amazon version 4 processing and unavailable-audio UI checks passed. Inventory: 55 BLOCKED, 153 NOT TESTED, 50 PASS out of 258. This mixes historical evidence and is not a full v4 retest. See release-2026-11-10/acceptance-update.json.

Current transcription update (7 November 2026): the CSV inventory now records 48 PASS, 155 NOT TESTED and 55 BLOCKED out of 258 mandatory criteria (18.60%). This mixes historical build dates and is not a complete version 4 retest. Nine of eleven transcription criteria have new evidence; processing/error-state UI coverage remains open. See transcription-2026-11-07/acceptance-update.json.

The original report below is historical.

> Historical snapshot. Use docs/RELEASE_READINESS.md, docs/TEST_REPORT.md and deliverables/amazon-submission/audit.json for the current audit. The original acceptance statements remain in scope; this snapshot is not a refreshed readiness score.

# Acceptance criteria and evidence

Statements are preserved from the supplied release gates. PASS requires current evidence; BLOCKED and NOT TESTED remain incomplete. The release has 22 groups; individual checklist statements form the denominator below.


## AC-01 — Android build

Group: INCOMPLETE

- [x] AC-01.01 Debug build succeeds. — **PASS**
- [x] AC-01.02 Release build succeeds when signing and build configuration permit. — **PASS**
- [x] AC-01.03 No critical compilation errors remain. — **PASS**
- [x] AC-01.04 Required project files exist. — **PASS**
- [ ] AC-01.05 No secrets are embedded in the application. — **NOT TESTED**

## AC-02 — Memory management

Group: INCOMPLETE

- [x] AC-02.01 Users can create, edit, delete, and retrieve memories. — **PASS**
- [x] AC-02.02 Records survive application restart. — **PASS**
- [x] AC-02.03 Album relationships remain valid. — **PASS**
- [x] AC-02.04 Search returns appropriate results. — **PASS**
- [ ] AC-02.05 Database migrations preserve data. — **NOT TESTED**

## AC-03 — Audio Recording and Playback

Group: INCOMPLETE

- [x] AC-03.01 Recording starts successfully. — **PASS**
- [x] AC-03.02 Pause and resume work. — **PASS**
- [x] AC-03.03 Recordings can be stopped and saved. — **PASS**
- [x] AC-03.04 Saved recordings play correctly. — **PASS**
- [ ] AC-03.05 Recordings are saved in private application storage. — **NOT TESTED**
- [ ] AC-03.06 Recordings remain available after application restart. — **NOT TESTED**
- [ ] AC-03.07 Playback, pause, resume, and seek controls work. — **NOT TESTED**
- [ ] AC-03.08 Recording interruptions are handled safely. — **NOT TESTED**
- [ ] AC-03.09 Microphone permission denial does not crash the application. — **NOT TESTED**
- [ ] AC-03.10 Low-storage conditions produce clear error messages. — **NOT TESTED**
- [ ] AC-03.11 Recording deletion removes the associated stored audio after confirmation. — **NOT TESTED**
- [ ] AC-03.12 No recording begins without an explicit user action. — **NOT TESTED**
- [ ] AC-03.13 No recording is silently uploaded. — **NOT TESTED**
- [ ] AC-03.14 Recording duration and playback position are accurate within the supported audio implementation. — **NOT TESTED**

## AC-04 — Multilingual Voice Commands

Group: INCOMPLETE

- [ ] AC-04.01 Push-to-talk activation works. — **NOT TESTED**
- [ ] AC-04.02 Microphone permission handling works. — **NOT TESTED**
- [ ] AC-04.03 Speech recognition availability is detected. — **NOT TESTED**
- [ ] AC-04.04 Recognised commands execute real application actions. — **NOT TESTED**
- [ ] AC-04.05 Transcribed commands are displayed where appropriate. — **NOT TESTED**
- [ ] AC-04.06 Spoken responses use a supported TextToSpeech engine. — **NOT TESTED**
- [ ] AC-04.07 Destructive commands require confirmation. — **NOT TESTED**
- [ ] AC-04.08 Unsupported commands produce understandable feedback. — **NOT TESTED**
- [ ] AC-04.09 Recognition errors do not crash the app. — **NOT TESTED**
- [ ] AC-04.10 All essential actions remain accessible through touch controls. — **NOT TESTED**
- [ ] AC-04.11 No continuous background listening occurs. — **NOT TESTED**
- [ ] AC-04.12 Raw voice-command recordings are not retained by default. — **NOT TESTED**

## AC-05 — Voice Transcription

Group: INCOMPLETE

- [ ] AC-05.01 A genuine transcription engine is integrated where available. — **BLOCKED**
- [ ] AC-05.02 Supported audio formats are documented. — **BLOCKED**
- [ ] AC-05.03 Supported languages are documented. — **BLOCKED**
- [ ] AC-05.04 Transcription produces editable text. — **BLOCKED**
- [ ] AC-05.05 Users can correct transcription errors. — **BLOCKED**
- [ ] AC-05.06 Corrected transcripts persist after restart. — **BLOCKED**
- [ ] AC-05.07 Transcription failures do not delete original recordings. — **BLOCKED**
- [ ] AC-05.08 Cloud transcription requires explicit consent before audio transmission. — **BLOCKED**
- [ ] AC-05.09 Transcription processing states are visible. — **BLOCKED**
- [ ] AC-05.10 Unavailable transcription is clearly explained. — **BLOCKED**
- [ ] AC-05.11 No fabricated transcripts are displayed as genuine results. — **BLOCKED**

## AC-06 — Family Albums and Timeline

Group: INCOMPLETE

- [ ] AC-06.01 Albums can be created, edited, and deleted. — **NOT TESTED**
- [ ] AC-06.02 Memories can be assigned to albums. — **NOT TESTED**
- [ ] AC-06.03 Memories can belong to multiple albums where supported. — **NOT TESTED**
- [ ] AC-06.04 Timeline entries appear in the correct chronological order. — **NOT TESTED**
- [ ] AC-06.05 Approximate and unknown dates are handled. — **NOT TESTED**
- [ ] AC-06.06 Year and album filters work. — **NOT TESTED**
- [ ] AC-06.07 Photographs and audio indicators display correctly. — **NOT TESTED**
- [ ] AC-06.08 Deleting an album does not unintentionally delete unrelated memories. — **NOT TESTED**
- [ ] AC-06.09 Timeline data persists offline. — **NOT TESTED**

## AC-07 — Digital Scrapbook

Group: INCOMPLETE

- [ ] AC-07.01 Users can create scrapbook projects. — **NOT TESTED**
- [ ] AC-07.02 Users can select layouts. — **NOT TESTED**
- [ ] AC-07.03 Photographs can be added and arranged. — **NOT TESTED**
- [ ] AC-07.04 Captions and story blocks can be edited. — **NOT TESTED**
- [ ] AC-07.05 Pages can be reordered. — **NOT TESTED**
- [ ] AC-07.06 Drafts can be saved. — **NOT TESTED**
- [ ] AC-07.07 Saved projects reopen correctly. — **NOT TESTED**
- [ ] AC-07.08 Layouts adapt to supported screen sizes. — **NOT TESTED**
- [ ] AC-07.09 Missing images are handled gracefully. — **NOT TESTED**
- [ ] AC-07.10 No private content is automatically published. — **NOT TESTED**

## AC-08 — Keepsake PDF Export

Group: INCOMPLETE

- [ ] AC-08.01 Users can select memories for export. — **NOT TESTED**
- [ ] AC-08.02 Users can configure a cover title. — **NOT TESTED**
- [ ] AC-08.03 Photographs render correctly. — **NOT TESTED**
- [ ] AC-08.04 Story text remains readable. — **NOT TESTED**
- [ ] AC-08.05 Page numbers are correct. — **NOT TESTED**
- [ ] AC-08.06 Selected print-friendly page sizes work. — **NOT TESTED**
- [ ] AC-08.07 Sensitive fields can be excluded. — **NOT TESTED**
- [ ] AC-08.08 Exported PDF files open successfully. — **NOT TESTED**
- [ ] AC-08.09 Unicode and approved localised text render correctly. — **NOT TESTED**
- [ ] AC-08.10 Export failures are handled without corrupting original memories. — **NOT TESTED**
- [ ] AC-08.11 PDF generation does not require uploading private memories. — **NOT TESTED**

## AC-09 — Offline Functionality

Group: INCOMPLETE

- [ ] AC-09.01 Users can create memories offline. — **NOT TESTED**
- [ ] AC-09.02 Users can edit memories offline. — **NOT TESTED**
- [ ] AC-09.03 Users can view saved albums offline. — **NOT TESTED**
- [ ] AC-09.04 Users can record audio offline. — **NOT TESTED**
- [ ] AC-09.05 Users can play saved audio offline. — **NOT TESTED**
- [ ] AC-09.06 Users can add photographs offline. — **NOT TESTED**
- [ ] AC-09.07 Users can use the timeline offline. — **NOT TESTED**
- [ ] AC-09.08 Users can edit scrapbooks offline. — **NOT TESTED**
- [ ] AC-09.09 Users can export keepsake PDFs offline. — **NOT TESTED**
- [ ] AC-09.10 Local data persists after restart. — **NOT TESTED**
- [ ] AC-09.11 Network-dependent transcription is clearly identified as unavailable offline. — **NOT TESTED**

## AC-10 — Worldwide Application Localisation

Group: INCOMPLETE

- [ ] AC-10.01 All required interface strings are translated. — **BLOCKED**
- [ ] AC-10.02 No unexpected English fallback appears. — **BLOCKED**
- [ ] AC-10.03 Navigation is localised. — **BLOCKED**
- [ ] AC-10.04 Onboarding is localised. — **BLOCKED**
- [ ] AC-10.05 Memory prompts are localised. — **BLOCKED**
- [ ] AC-10.06 Notifications are localised. — **BLOCKED**
- [ ] AC-10.07 Paywall content is localised. — **BLOCKED**
- [ ] AC-10.08 Error messages are localised. — **BLOCKED**
- [ ] AC-10.09 Accessibility labels are localised. — **BLOCKED**
- [ ] AC-10.10 Placeholders are preserved. — **BLOCKED**
- [ ] AC-10.11 Plural rules work. — **BLOCKED**
- [ ] AC-10.12 Date formats are appropriate. — **BLOCKED**
- [ ] AC-10.13 Right-to-left layouts work where applicable. — **BLOCKED**
- [ ] AC-10.14 Long translated text does not break layouts. — **BLOCKED**
- [ ] AC-10.15 Required human review is recorded. — **BLOCKED**
- [ ] AC-10.16 Voice capability information is accurate for that locale. — **BLOCKED**

## AC-11 — Fully Localised Amazon Screenshots

Group: INCOMPLETE

- [ ] AC-11.01 All eight required screenshot compositions exist. — **BLOCKED**
- [ ] AC-11.02 Screenshots display the actual implemented application. — **BLOCKED**
- [ ] AC-11.03 Visible interface text matches the target locale. — **BLOCKED**
- [ ] AC-11.04 Marketing headlines are translated naturally. — **BLOCKED**
- [ ] AC-11.05 Supporting captions are translated. — **BLOCKED**
- [ ] AC-11.06 Search terms reflect local terminology. — **BLOCKED**
- [ ] AC-11.07 Fire tablet variants exist. — **BLOCKED**
- [ ] AC-11.08 Phone variants exist where required. — **BLOCKED**
- [ ] AC-11.09 Current Amazon dimensions are satisfied. — **BLOCKED**
- [ ] AC-11.10 Images are readable. — **BLOCKED**
- [ ] AC-11.11 No important content is cropped. — **BLOCKED**
- [ ] AC-11.12 Screenshots contain no fabricated testimonials or ratings. — **BLOCKED**
- [ ] AC-11.13 Screenshots do not advertise unavailable features. — **BLOCKED**
- [ ] AC-11.14 Screenshot manifest is complete. — **BLOCKED**
- [ ] AC-11.15 Exported files pass image validation. — **BLOCKED**

## AC-12 — Translation Automation Pipeline

Group: INCOMPLETE

- [x] AC-12.01 Source strings can be extracted. — **PASS**
- [x] AC-12.02 New and changed strings are detected. — **PASS**
- [ ] AC-12.03 Translation provider integration works when configured. — **NOT TESTED**
- [ ] AC-12.04 Translation caching works. — **NOT TESTED**
- [ ] AC-12.05 Protected terminology is preserved. — **NOT TESTED**
- [ ] AC-12.06 Placeholders are validated. — **NOT TESTED**
- [x] AC-12.07 Missing translations are reported. — **PASS**
- [ ] AC-12.08 Resource generation succeeds. — **NOT TESTED**
- [ ] AC-12.09 Right-to-left validation is included. — **NOT TESTED**
- [x] AC-12.10 Translation review status is tracked. — **PASS**
- [x] AC-12.11 API keys are excluded from release artifacts. — **PASS**
- [ ] AC-12.12 Translation reports can be regenerated. — **NOT TESTED**

## AC-13 — Amazon In-App Purchasing

Group: INCOMPLETE

- [ ] AC-13.01 Amazon-compatible billing integration exists. — **BLOCKED**
- [ ] AC-13.02 Premium product details can be retrieved. — **BLOCKED**
- [ ] AC-13.03 The paywall displays store-provided localised prices. — **BLOCKED**
- [ ] AC-13.04 Successful verified purchases grant Premium. — **BLOCKED**
- [ ] AC-13.05 Cancelled purchases do not grant Premium. — **BLOCKED**
- [ ] AC-13.06 Failed purchases are handled. — **BLOCKED**
- [ ] AC-13.07 Purchase restoration works. — **BLOCKED**
- [ ] AC-13.08 Entitlements persist appropriately. — **BLOCKED**
- [ ] AC-13.09 Offline entitlement handling is defined and tested. — **BLOCKED**
- [ ] AC-13.10 Free-tier limits are enforced. — **BLOCKED**
- [ ] AC-13.11 Premium features unlock correctly. — **BLOCKED**
- [ ] AC-13.12 Test billing cannot grant production entitlements. — **BLOCKED**
- [ ] AC-13.13 No Google Play Billing dependency exists in the Amazon build. — **BLOCKED**

## AC-14 — Premium Brand Assets

Group: INCOMPLETE

- [ ] AC-14.01 Master app icon exists. — **NOT TESTED**
- [ ] AC-14.02 Adaptive icon layers exist. — **NOT TESTED**
- [ ] AC-14.03 Monochrome icon exists. — **NOT TESTED**
- [ ] AC-14.04 Splash artwork exists. — **NOT TESTED**
- [ ] AC-14.05 Onboarding illustrations exist. — **NOT TESTED**
- [ ] AC-14.06 Album templates exist. — **NOT TESTED**
- [ ] AC-14.07 Voice recording graphics exist. — **NOT TESTED**
- [ ] AC-14.08 Scrapbook templates exist. — **NOT TESTED**
- [ ] AC-14.09 Keepsake book templates exist. — **NOT TESTED**
- [ ] AC-14.10 Premium upgrade graphics exist. — **NOT TESTED**
- [ ] AC-14.11 Marketing templates exist. — **NOT TESTED**
- [ ] AC-14.12 Assets are visually consistent. — **NOT TESTED**
- [ ] AC-14.13 Usage rights are documented. — **NOT TESTED**
- [ ] AC-14.14 No copied competitor assets remain. — **NOT TESTED**

## AC-15 — Amazon Appstore SEO / ASO

Group: INCOMPLETE

- [ ] AC-15.01 App title is prepared. — **BLOCKED**
- [ ] AC-15.02 Product summary is prepared. — **BLOCKED**
- [ ] AC-15.03 Full description is prepared. — **BLOCKED**
- [ ] AC-15.04 Relevant search terminology is researched. — **BLOCKED**
- [ ] AC-15.05 Feature descriptions match implemented functionality. — **BLOCKED**
- [ ] AC-15.06 Screenshot captions are localised. — **BLOCKED**
- [ ] AC-15.07 Release notes are prepared. — **BLOCKED**
- [ ] AC-15.08 Metadata meets verified Amazon requirements. — **BLOCKED**
- [ ] AC-15.09 No unsupported keyword fields are invented. — **BLOCKED**
- [ ] AC-15.10 No keyword stuffing is present. — **BLOCKED**
- [ ] AC-15.11 No fabricated reviews, awards, or ratings appear. — **BLOCKED**

## AC-16 — AI Search Optimisation

Group: INCOMPLETE

- [x] AC-16.01 Marketing website builds successfully. — **PASS**
- [x] AC-16.02 Required pages exist. — **PASS**
- [x] AC-16.03 Pages contain crawlable HTML. — **PASS**
- [x] AC-16.04 Titles and descriptions are meaningful. — **PASS**
- [ ] AC-16.05 Canonical URLs are configured. — **NOT TESTED**
- [x] AC-16.06 XML sitemap exists. — **PASS**
- [x] AC-16.07 Robots.txt exists. — **PASS**
- [x] AC-16.08 Structured data is valid. — **PASS**
- [x] AC-16.09 Structured data matches visible content. — **PASS**
- [ ] AC-16.10 Localised pages use appropriate hreflang annotations. — **NOT TESTED**
- [ ] AC-16.11 Product facts are accurate. — **NOT TESTED**
- [ ] AC-16.12 FAQ content is useful and original. — **NOT TESTED**
- [x] AC-16.13 Privacy and support pages exist. — **PASS**
- [x] AC-16.14 Internal links work. — **PASS**
- [ ] AC-16.15 No fabricated testimonials or ratings appear. — **NOT TESTED**

## AC-17 — Privacy and Security

Group: INCOMPLETE

- [ ] AC-17.01 No account is required for core features. — **NOT TESTED**
- [ ] AC-17.02 Memories remain local by default. — **NOT TESTED**
- [ ] AC-17.03 Audio is not uploaded without consent. — **NOT TESTED**
- [ ] AC-17.04 Photographs are not uploaded without consent. — **NOT TESTED**
- [ ] AC-17.05 Microphone permissions are requested contextually. — **NOT TESTED**
- [ ] AC-17.06 Private media uses appropriate storage. — **NOT TESTED**
- [ ] AC-17.07 No API secrets are embedded in release builds. — **NOT TESTED**
- [ ] AC-17.08 Data deletion works. — **NOT TESTED**
- [ ] AC-17.09 Export permissions are appropriate. — **NOT TESTED**
- [ ] AC-17.10 Backup files are handled securely. — **NOT TESTED**
- [ ] AC-17.11 Privacy disclosures match implemented behaviour. — **NOT TESTED**
- [ ] AC-17.12 No unnecessary tracking SDKs are included. — **NOT TESTED**
- [ ] AC-17.13 No unresolved critical security findings remain. — **NOT TESTED**

## AC-18 — Backup and Restore

Group: INCOMPLETE

- [x] AC-18.01 Local backup can be created. — **PASS**
- [x] AC-18.02 Backup manifest is generated. — **PASS**
- [ ] AC-18.03 Selected photographs are included correctly. — **NOT TESTED**
- [ ] AC-18.04 Selected audio recordings are included correctly. — **NOT TESTED**
- [ ] AC-18.05 Selected transcripts are included correctly. — **NOT TESTED**
- [x] AC-18.06 Scrapbook projects are preserved. — **PASS**
- [x] AC-18.07 Backup integrity is validated. — **PASS**
- [x] AC-18.08 Restore preview works. — **PASS**
- [x] AC-18.09 Duplicate handling works. — **PASS**
- [x] AC-18.10 Corrupt backups are rejected safely. — **PASS**
- [x] AC-18.11 Encrypted backup works where implemented. — **PASS**
- [ ] AC-18.12 Restored data remains accessible after restart. — **NOT TESTED**

## AC-19 — Accessibility

Group: INCOMPLETE

- [ ] AC-19.01 Primary controls meet the defined touch-target minimum. — **NOT TESTED**
- [ ] AC-19.02 Screen reader labels are meaningful. — **NOT TESTED**
- [ ] AC-19.03 Text scales correctly. — **NOT TESTED**
- [ ] AC-19.04 Colour is not the only status indicator. — **NOT TESTED**
- [ ] AC-19.05 High-contrast layouts remain usable. — **NOT TESTED**
- [ ] AC-19.06 Reduced-motion settings are respected. — **NOT TESTED**
- [ ] AC-19.07 Voice controls are optional. — **NOT TESTED**
- [ ] AC-19.08 Touch alternatives exist. — **NOT TESTED**
- [ ] AC-19.09 Error messages are understandable. — **NOT TESTED**
- [ ] AC-19.10 Navigation works without precise gestures. — **NOT TESTED**

## AC-20 — Performance and Reliability

Group: INCOMPLETE

- [ ] AC-20.01 Core screens remain responsive. — **NOT TESTED**
- [ ] AC-20.02 Large photo albums do not cause avoidable crashes. — **NOT TESTED**
- [ ] AC-20.03 Audio recording does not unnecessarily block the UI. — **NOT TESTED**
- [ ] AC-20.04 Image loading is memory-conscious. — **NOT TESTED**
- [ ] AC-20.05 Database operations do not block the main thread. — **NOT TESTED**
- [ ] AC-20.06 Background work is appropriately scheduled. — **NOT TESTED**
- [ ] AC-20.07 No reproducible critical crashes remain. — **NOT TESTED**
- [ ] AC-20.08 Application restart preserves user data. — **NOT TESTED**
- [ ] AC-20.09 Storage errors are handled. — **NOT TESTED**
- [ ] AC-20.10 Performance measurements are recorded on available devices. — **NOT TESTED**

## AC-21 — Fire Tablet Compatibility

Group: INCOMPLETE

- [ ] AC-21.01 Supported Fire OS versions are documented. — **NOT TESTED**
- [ ] AC-21.02 Representative tablet screen sizes are tested. — **NOT TESTED**
- [ ] AC-21.03 Portrait layouts work. — **NOT TESTED**
- [ ] AC-21.04 Landscape layouts work. — **NOT TESTED**
- [ ] AC-21.05 Touch navigation works. — **NOT TESTED**
- [ ] AC-21.06 Microphone permission behaviour is tested. — **NOT TESTED**
- [ ] AC-21.07 Audio recording works on tested supported devices. — **NOT TESTED**
- [ ] AC-21.08 Audio playback works. — **NOT TESTED**
- [ ] AC-21.09 File import works. — **NOT TESTED**
- [ ] AC-21.10 PDF export works. — **NOT TESTED**
- [ ] AC-21.11 Offline persistence works. — **NOT TESTED**
- [ ] AC-21.12 Speech recognition limitations are documented. — **NOT TESTED**
- [ ] AC-21.13 TextToSpeech availability is documented. — **NOT TESTED**
- [ ] AC-21.14 Amazon billing compatibility is verified. — **NOT TESTED**

## AC-22 — Release Build and Submission Package

Group: INCOMPLETE

- [x] AC-22.01 Debug build succeeds. — **PASS**
- [x] AC-22.02 Release build succeeds. — **PASS**
- [ ] AC-22.03 Package identifier is confirmed. — **NOT TESTED**
- [x] AC-22.04 Version information is configured. — **PASS**
- [x] AC-22.05 Signing configuration is documented. — **PASS**
- [ ] AC-22.06 Required permissions are documented. — **NOT TESTED**
- [ ] AC-22.07 App icon is available. — **NOT TESTED**
- [ ] AC-22.08 Localised screenshots are complete. — **NOT TESTED**
- [ ] AC-22.09 Localised metadata is complete. — **NOT TESTED**
- [ ] AC-22.10 Privacy policy is prepared. — **NOT TESTED**
- [ ] AC-22.11 Amazon billing is verified. — **NOT TESTED**
- [ ] AC-22.12 Device compatibility report exists. — **NOT TESTED**
- [ ] AC-22.13 Submission checklist is complete. — **NOT TESTED**
- [ ] AC-22.14 No critical defects remain. — **NOT TESTED**
- [ ] AC-22.15 Outstanding blockers are documented. — **NOT TESTED**
