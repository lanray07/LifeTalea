# Recorded-audio transcription

The new development implementation decodes an existing recording with Android MediaExtractor/MediaCodec, converts PCM to mono 16 kHz, and runs a bundled multilingual Whisper tiny model through whisper.cpp JNI. It does not call Android SpeechRecognizer for saved audio and has no audio-upload endpoint, provider credentials or paid hosting dependency.

The user selects the recording language and confirms local processing. The result remains an editable draft until the user explicitly appends it to the memory. The database update preserves existing text, checks the one-million-character bound atomically and cannot recreate a deleted memory. Cancellation, dismissal and backgrounding stop the task; the original recording is not modified. The initial transcription limit is ten minutes. Longer recordings remain playable and support manual transcripts. Model language availability does not establish recognition accuracy for every language, accent, speaker or device.

## Pinned dependencies

- whisper.cpp v1.9.5, commit `d1be6fde11ac6e0407606b4e42fe72d34add8037`. Build archive SHA-256 `645445da884df6dbd52b30f82d7be7c01d1767c938714e477e786b88d529e9f4`.
- Multilingual `ggml-tiny.bin`, 77,691,713 bytes, repository revision `5359861c739e955e79d9a303bcbc70fb988958b1`. SHA-256 `be07e048e1e599ad46341c8d2a135645097a538221678b7acdd1b1919c6e1b21`.
- NDK `28.2.13676358`, CMake `3.31.6`, Ninja `1.11.1.4`. Both ARM64 and ARMv7 are intended build targets. Actual compatibility must be verified per ABI/device.

The build downloads and verifies the pinned source and model. They are bundled in the APK; end users need no model download or account. The model binary stays in the ignored build directory. Upstream license notices ship in `assets/transcription`. No native-language approval is inferred from the model's language table.

For a new checkout, install CMake and Ninja from PyPI with the pinned versions, then run `python scripts/configure_native_tools.py`. The script writes only ignored local tool paths. Gradle resolves the NDK through the configured Android SDK. See the CI workflow for the complete build setup.

Sources: [official Android example](https://github.com/ggml-org/whisper.cpp/blob/d1be6fde11ac6e0407606b4e42fe72d34add8037/examples/whisper.android/README.md), [source release](https://github.com/ggml-org/whisper.cpp/releases/tag/v1.9.5), [model repository](https://huggingface.co/ggerganov/whisper.cpp/tree/5359861c739e955e79d9a303bcbc70fb988958b1), [Whisper license](https://github.com/openai/whisper/blob/main/LICENSE).

## Verification scope

The 22-test Fire suite passed with Wi-Fi disabled. Fictional English AAC, review before save, manual correction, existing words/audio, silence, malformed input, language/consent gates, length limits, native cancellation and retry passed. A separate force-stop/relaunch confirmed corrected-text persistence in a new app process. Error cases retained their source files. See AMAZON_TRANSCRIPTION_RELEASE_REVIEW_2026-11-07.md and its dated evidence.

The verified input is AAC in an M4A container, including the app's 44.1 kHz recording format and a stereo fixture. Other decoder paths are not format certification. Language choices are English, French, Spanish, German, Italian, Portuguese, Dutch, Polish, Arabic, Hindi, Japanese, Korean, Chinese, Turkish, Indonesian and Swedish. Regional locales share model language codes. Only the short synthesized English recording has recognition-accuracy evidence; other languages, accents, natural/noisy speech and long-recording performance remain unverified.
