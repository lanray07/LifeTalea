# Master prompt release review

**Blocked under section 30 of the master prompt.** Public submission requires all mandatory acceptance criteria to pass. The public Amazon draft still has the previously tested version 3. The current product changes have separate development-build evidence and have not replaced the Amazon-distributed candidate. See `AMAZON_RELEASE_REVIEW_2026-11-07.md`.

This pass connected the onboarding purpose to the localized story prompt and made the full option row selectable. The choice is stored on device with onboarding completion. Skipping or opening an older installation preserves the generic prompt. English album and year commands now carry explicit targets. The app gives an exact album title priority, avoids arbitrary matches for duplicate titles, and clears unrelated filters when opening an album or year. The changes do not enable additional speech-recognition languages.

Debug, unsigned release and instrumentation APKs built successfully. All 21 Android unit tests passed, including the new structured command cases. The strict locale validator reported 191 keys across 22 complete draft locales and zero release approvals. The website review gate and static export regression passed. The physical walkthrough verified purpose selection, prompt prefill and the typed year-command fallback. It also found draft text leaking into search; that defect has a real failing UI regression and a separate-state fix. Dated device results and artifact hashes are in `deliverables/reports/release-2026-11-07/checks.json`. Lint reports zero errors and 258 warnings.

| Acceptance scope | Remaining work |
| --- | --- |
| AC-01–03, AC-06–09 | Changed-build evidence is recorded separately. Complete recording interruption, low-storage, restart and full offline tests, plus scrapbook layout and PDF visual checks. |
| AC-04–05 | Implement and verify additional language dictionaries and speech capabilities. Recorded-file transcription still needs a working engine, tested language support and a processing workflow. |
| AC-10–12, AC-14–16 | Obtain native locale approvals. Validate store assets against actual release screens and complete visual and accessibility review. Validate translation-provider configuration and the public website. |
| AC-13 | Version 3 passed the Test 1 update, prompt, cancellation and reset-account restore checks. Public Premium is still marked TEST. Reboot recovery and account switching remain open. |
| AC-17–21 | Complete independent security and publisher privacy review, large backup and interruption tests, accessibility and performance measurements, and representative Fire model coverage. |
| AC-22 | Build, identify and test the final candidate after product work. Verify the release listing and public billing configuration before submission. |

The changed debug build passed all 18 physical Fire tests and retained 189 evidence files. The 258-row acceptance matrix remains a historical baseline. A current overall pass rate requires rechecking each item against current evidence. The separate version 3 review ZIP retains its original APK and test provenance.
