# Voice capabilities

Local recording uses MediaRecorder: AAC in M4A, 44.1 kHz, 96 kbps. It checks free storage, acquires transient audio focus, supports pause/resume and saves on stop. Free recordings are capped at three minutes; Premium at one hour and 200 MiB, still subject to storage. These are implementation limits, not device certification.

Push-to-talk uses Android SpeechRecognizer only when the device reports a recognition service. It discloses possible service-side processing before activation. Commands are not retained as audio. The English parser supports new memory, start/stop recording, albums, selected year, timeline, keepsakes and reading a story. There are no destructive voice commands. Text command and touch alternatives remain available. Named-album and year routing are implemented; multilingual command dictionaries remain incomplete.

Spoken stories use Android TextToSpeech with runtime language availability checks. Spoken command feedback is off by default and can be disabled. Lifecycle stop cancels listening and speech. No continuous listening exists.

The debug interface has 22 locale drafts. Command recognition and parsing explicitly request English regardless of interface language; localized notices disclose this. Story speech requests the selected locale and checks device availability. Locale selection does not certify multilingual command recognition or TTS.

The newer development build implements recorded-file transcription separately through bundled Whisper tiny / whisper.cpp. It works from saved audio, without an installed Android recognition service or an audio upload. Users choose among the model language codes exposed in the dialog and review an editable draft before saving. The initial duration guard is ten minutes. A real English synthetic AAC fixture was recognized on the Fire tablet; language options do not establish accuracy in all languages. See ON_DEVICE_TRANSCRIPTION.md and the dated device reports for the exact tested build and scope. Amazon's existing version 3 does not contain this implementation.

A recognition service being installed does not prove recognition accuracy, language/accents support or offline availability. TTS service detection does not establish every locale works. The physical diagnostic report records the actual KFTRWI/Fire OS 7 environment and service availability when executed. See deliverables/reports/VOICE_TEST_REPORT.md; no untested language/device is certified.
