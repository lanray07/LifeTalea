# Actual test report

Updated 2026-11-02. Final results must be interpreted with their scope.

- Kotlin/JUnit: 7/7 passing, copied XML in deliverables/reports/junit.
- Android/Fire instrumentation: PASS; final retained evidence is deliverables/android/build-logs/instrumentation.log. Test fixtures are fictional. The microphone diagnostic removes its raw audio.
- Android build/lint: PASS; inspect build-tested.log, not earlier failed attempts.
- Python validator tests: see python-tests.log for the actual executed count.
- Website: sixteen English pages structurally checked; browser desktop/mobile captures and comparison are in DESIGN_REVIEW.md.
- Static source checks: static-checks.json, a narrow pattern review rather than an independent audit.

Earlier failed build/test attempts are retained with their logs. Initial errors included incomplete UI references, test method return type, keyboard/date-field automation and Windows compiler file contention. Final logs supersede earlier attempts only for rerun checks. No provider transcription, live billing, native-language review, broad Fire compatibility or legal assessment is inferred from local test success.
