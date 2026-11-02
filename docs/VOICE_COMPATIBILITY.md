# Voice capabilities

Local recording uses MediaRecorder: AAC in M4A, 44.1 kHz, 96 kbps. It checks free storage, acquires transient audio focus, supports pause/resume and saves on stop. Free recordings are capped at three minutes; Premium at one hour and 200 MiB, still subject to storage. These are implementation limits, not device certification.

Push-to-talk uses Android SpeechRecognizer only when the device reports a recognition service. It discloses possible service-side processing before activation. Commands are not retained as audio. The English parser supports new memory, start/stop recording, albums, selected year, timeline, keepsakes and reading a story. There are no destructive voice commands. Text command and touch alternatives remain available. Specific album-name routing and multilingual dictionaries are still incomplete.

Spoken stories use Android TextToSpeech with runtime language availability checks. Spoken command feedback is off by default and can be disabled. Lifecycle stop cancels listening and speech. No continuous listening exists.

The debug interface has 22 locale drafts. Recognition and command parsing explicitly request English regardless of interface language; localized notices disclose this. Story speech requests the selected locale and checks device availability. Locale selection does not certify multilingual recognition or TTS. Recorded-file transcription remains unavailable.

A recognition service being installed does not prove recognition accuracy, language/accents support or offline availability. TTS service detection does not establish every locale works. The physical diagnostic report records the actual KFTRWI/Fire OS 7 environment and service availability when executed. See deliverables/reports/VOICE_TEST_REPORT.md; no untested language/device is certified.
