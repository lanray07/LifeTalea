package com.lifetalea.app.voice

import android.content.Context
import android.content.Intent
import android.media.*
import android.os.Bundle
import android.os.StatFs
import android.speech.*
import android.speech.tts.TextToSpeech
import android.os.SystemClock
import java.io.File
import java.util.Locale
import kotlinx.coroutines.flow.MutableStateFlow

data class RecordingState(val active: Boolean = false, val paused: Boolean = false, val durationMs: Long = 0, val error: Boolean = false)
class StoryRecorder(private val context: Context) {
    var onAutomaticStop: (() -> Unit)? = null
    val state = MutableStateFlow(RecordingState())
    private var recorder: MediaRecorder? = null
    private var file: File? = null
    private var started = 0L
    private var accumulated = 0L
    private val audio = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
    private var focus: AudioFocusRequest? = null
    fun start(target: File, maxMs: Int) {
        check(recorder == null)
        check(StatFs(target.parent!!).availableBytes > 20 * 1024 * 1024)
        val request = AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT)
            .setAudioAttributes(AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build())
            .setOnAudioFocusChangeListener { change -> if (change < 0 && state.value.active && !state.value.paused) runCatching { pause() } }
            .build()
        check(audio.requestAudioFocus(request) == AudioManager.AUDIOFOCUS_REQUEST_GRANTED)
        focus = request; file = target; accumulated = 0
        try {
            @Suppress("DEPRECATION") val r = MediaRecorder()
            recorder = r
            r.setAudioSource(MediaRecorder.AudioSource.MIC); r.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
            r.setAudioEncoder(MediaRecorder.AudioEncoder.AAC); r.setAudioEncodingBitRate(96000); r.setAudioSamplingRate(44100)
            r.setOutputFile(target.path); r.setMaxDuration(maxMs); r.setMaxFileSize(200L * 1024 * 1024)
            r.setOnErrorListener { _, _, _ -> if (state.value.active && !state.value.paused) runCatching { pause() }; state.value = state.value.copy(error = true) }
            r.setOnInfoListener { _, what, _ -> if (what == MediaRecorder.MEDIA_RECORDER_INFO_MAX_DURATION_REACHED || what == MediaRecorder.MEDIA_RECORDER_INFO_MAX_FILESIZE_REACHED) onAutomaticStop?.invoke() }
            r.prepare(); r.start(); started = SystemClock.elapsedRealtime(); state.value = RecordingState(active = true)
        } catch (e: Exception) { recorder?.release(); recorder = null; target.delete(); releaseFocus(); throw e }
    }
    fun elapsed() = accumulated + if (state.value.active && !state.value.paused) SystemClock.elapsedRealtime() - started else 0
    fun pause() { recorder?.pause(); accumulated = elapsed(); state.value = state.value.copy(paused = true, durationMs = accumulated) }
    fun resume() { recorder?.resume(); started = SystemClock.elapsedRealtime(); state.value = state.value.copy(paused = false) }
    fun stop(): Pair<File, Long>? {
        val r = recorder ?: return null; val length = elapsed(); recorder = null
        return try { r.stop(); file?.takeIf { it.length() > 0 }?.let { it to length } }
        catch (e: RuntimeException) {
            // A platform auto-stop can precede this callback. Preserve valid completed audio.
            val valid = file?.let { f -> runCatching { val metadata = MediaMetadataRetriever(); try { metadata.setDataSource(f.path); metadata.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)?.toLongOrNull()?.let { f to it } } finally { metadata.release() } }.getOrNull() }
            if (valid == null) file?.delete()
            valid
        }
        finally { r.release(); releaseFocus(); state.value = RecordingState() }
    }
    private fun releaseFocus() { focus?.let { audio.abandonAudioFocusRequest(it) }; focus = null }
}

enum class VoiceIntent { NEW_MEMORY, START_RECORDING, STOP_RECORDING, TIMELINE, ALBUMS, KEEPSAKE, READ_STORY, SEARCH, UNKNOWN }
data class VoiceCommand(val intent: VoiceIntent, val query: String = "")
object CommandParser {
    private val namedAlbum = Regex("open (?:the )?(?:album (.+)|(.+ album))")
    private val memoriesFromYear = Regex("show memories from (last year|[0-9]{4})")

    // Locale dictionaries are separate from content. Only reviewed dictionaries are enabled.
    fun parse(input: String, locale: Locale): VoiceCommand {
        if (locale.language != "en") return VoiceCommand(VoiceIntent.UNKNOWN)
        val s = input.lowercase(locale).trim().trimEnd('.', '!', '?')
        namedAlbum.matchEntire(s)?.let { match ->
            return VoiceCommand(VoiceIntent.ALBUMS, match.groupValues[1].ifEmpty { match.groupValues[2] })
        }
        memoriesFromYear.matchEntire(s)?.let { match ->
            return VoiceCommand(VoiceIntent.SEARCH, match.groupValues[1])
        }
        val intent = when {
            s.matches(Regex("(create|add)( a)? new memory|new memory")) -> VoiceIntent.NEW_MEMORY
            s.matches(Regex("(start|begin) recording")) -> VoiceIntent.START_RECORDING
            s.matches(Regex("(stop|finish) recording")) -> VoiceIntent.STOP_RECORDING
            s.contains("timeline") -> VoiceIntent.TIMELINE
            s.contains("keepsake") -> VoiceIntent.KEEPSAKE
            s.startsWith("read ") -> VoiceIntent.READ_STORY
            s in setOf("open album", "open albums", "open the albums") -> VoiceIntent.ALBUMS
            else -> VoiceIntent.UNKNOWN
        }
        return VoiceCommand(intent)
    }
}

class VoiceAssistant(private val context: Context) {
    private var recognizer: SpeechRecognizer? = null
    private var tts: TextToSpeech? = null
    private var ttsReady = false
    private var pendingSpeech: (() -> Unit)? = null
    private var speechEngineGeneration = 0L
    private val speechHandler = android.os.Handler(android.os.Looper.getMainLooper())
    fun available() = SpeechRecognizer.isRecognitionAvailable(context)
    fun listen(locale: Locale, onText: (String) -> Unit, onError: (Int) -> Unit) {
        if (!available()) { onError(SpeechRecognizer.ERROR_CLIENT); return }
        recognizer?.destroy()
        recognizer = SpeechRecognizer.createSpeechRecognizer(context).also { r ->
            r.setRecognitionListener(object : RecognitionListener {
                override fun onResults(results: Bundle?) { results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)?.firstOrNull()?.let(onText) ?: onError(SpeechRecognizer.ERROR_NO_MATCH) }
                override fun onError(error: Int) { onError(error) }
                override fun onReadyForSpeech(params: Bundle?) {}
                override fun onBeginningOfSpeech() {}
                override fun onRmsChanged(rmsdB: Float) {}
                override fun onBufferReceived(buffer: ByteArray?) {}
                override fun onEndOfSpeech() {}
                override fun onPartialResults(partialResults: Bundle?) {}
                override fun onEvent(eventType: Int, params: Bundle?) {}
            })
            r.startListening(Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM).putExtra(RecognizerIntent.EXTRA_LANGUAGE, locale.toLanguageTag()).putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1))
        }
    }
    fun speak(text: String, locale: Locale, unavailable: () -> Unit) {
        fun utter() {
            val engine = tts ?: return unavailable()
            val voice = engine.voices.orEmpty().asSequence()
                .filter { !it.isNetworkConnectionRequired && it.locale.language == locale.language && "notInstalled" !in it.features.orEmpty() }
                .sortedWith(compareByDescending<android.speech.tts.Voice> { it.locale == locale }.thenByDescending { it.quality })
                .firstOrNull() ?: return unavailable()
            if (engine.setVoice(voice) != TextToSpeech.SUCCESS ||
                engine.voice?.let { it.name != voice.name || it.isNetworkConnectionRequired } != false ||
                engine.speak(text, TextToSpeech.QUEUE_FLUSH, null, "lifetalea-story") != TextToSpeech.SUCCESS
            ) unavailable()
        }
        if (ttsReady) {
            utter()
            return
        }
        pendingSpeech = { if (ttsReady) utter() else unavailable() }
        if (tts == null) {
            val generation = ++speechEngineGeneration
            tts = TextToSpeech(context) { status ->
                speechHandler.post {
                    if (generation != speechEngineGeneration) return@post
                    ttsReady = status == TextToSpeech.SUCCESS
                    if (!ttsReady) {
                        tts?.shutdown()
                        tts = null
                    }
                    val request = pendingSpeech
                    pendingSpeech = null
                    request?.invoke()
                }
            }
        }
    }
    fun stop() { pendingSpeech = null; recognizer?.cancel(); tts?.stop() }
    fun close() {
        pendingSpeech = null
        speechEngineGeneration++
        recognizer?.destroy()
        tts?.shutdown()
        tts = null
        ttsReady = false
    }
}

sealed interface TranscriptionResult {
    data class Success(val text: String) : TranscriptionResult
    data class Unavailable(val reason: String) : TranscriptionResult
}
interface TranscriptionEngine {
    suspend fun transcribe(file: File, language: String, consent: Boolean, progress: (Int) -> Unit = {}): TranscriptionResult
}
