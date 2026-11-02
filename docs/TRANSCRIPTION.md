# Recorded-file transcription

Status: BLOCKED — no configured and tested recorded-file engine.

`voice/Voice.kt` defines TranscriptionEngine and an explicit unavailable result. The app preserves recordings, exposes a manual editable transcript field and explains that automatic transcription is not configured. It never treats command recognition as recorded-file transcription. No model output is fabricated.

Before enabling a service: select a provider or licensed local model; verify M4A/AAC decoding, target languages, file size and duration limits; implement cancellable processing and persistent status; obtain explicit upload consent if a cloud provider is used; keep provider credentials on a backend; test errors/retries/corrections without deleting original audio. Establish sustainable unit economics before promising transcription in a one-time purchase. These integration tasks remain incomplete, beyond the adapter itself.
