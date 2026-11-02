# Actual test report

Updated 2026-11-02. Final results must be interpreted with their scope.

- Kotlin/JUnit: 9/9 passing, copied XML in deliverables/reports/junit.
- Android/Fire instrumentation: PASS; final retained evidence is deliverables/android/build-logs/instrumentation.log. Test fixtures are fictional. The microphone diagnostic removes its raw audio.
- Android build/lint: PASS; current localization build evidence is localization-debug-final.log and localization-build.log (0 lint errors; 280 warnings).
- Python validator tests: see python-tests.log for the actual executed count.
- Website: 352 localized pages structurally checked; French desktop and Arabic mobile browser evidence is in deliverables/reports/website-localization. The current localization device suite passed 9 tests and captured eight screens in each of 22 locales. See LOCALIZATION_DELIVERY.md for precise scope and draft language limitations.
- Static source checks: static-checks.json, a narrow pattern review rather than an independent audit.

Earlier failed build/test attempts are retained with their logs. Initial errors included incomplete UI references, test method return type, keyboard/date-field automation and Windows compiler file contention. Final logs supersede earlier attempts only for rerun checks. No provider transcription, live billing, native-language review, broad Fire compatibility or legal assessment is inferred from local test success.
