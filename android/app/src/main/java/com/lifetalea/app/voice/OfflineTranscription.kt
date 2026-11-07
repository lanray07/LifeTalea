package com.lifetalea.app.voice

import android.content.Context
import android.content.res.AssetManager
import kotlinx.coroutines.*
import java.io.File
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean
import kotlin.coroutines.resume
import kotlin.math.sqrt

internal object WhisperNative {
    init { System.loadLibrary("lifetalea_whisper") }
    external fun createTask(): Long
    external fun cancel(task: Long)
    external fun progress(task: Long): Int
    external fun release(task: Long)
    external fun transcribe(assets: AssetManager, samples: FloatArray, language: String, task: Long): ByteArray?
}

/** The single worker also serializes native model allocation across engine instances. */
class OfflineTranscription(context: Context) : TranscriptionEngine {
    private val assets = context.applicationContext.assets
    companion object {
        val languages = listOf("en", "fr", "es", "de", "it", "pt", "nl", "pl", "ar", "hi", "ja", "ko", "zh", "tr", "id", "sv")
        private val worker = Executors.newSingleThreadExecutor { runnable -> Thread(runnable, "LifeTalea transcription").apply { isDaemon = true } }
    }
    override suspend fun transcribe(file: File, language: String, consent: Boolean, progress: (Int) -> Unit): TranscriptionResult {
        if (!consent) return TranscriptionResult.Unavailable("transcription_consent_required")
        if (language !in languages) return TranscriptionResult.Unavailable("transcription_failed")
        return coroutineScope {
            val request = NativeRequest()
            val observer = launch { while (isActive) { progress(request.percent()); delay(200) } }
            try {
                suspendCancellableCoroutine { continuation ->
                    continuation.invokeOnCancellation { request.cancel() }
                    worker.execute {
                        val result = try {
                            if (request.cancelled.get()) throw CancellationException()
                            val samples = RecordedAudio.decode(file) { request.cancelled.get() }
                            val rms = sqrt(samples.fold(0.0) { sum, value -> sum + value.toDouble() * value } / samples.size)
                            if (rms < 0.0005) TranscriptionResult.Unavailable("transcription_empty") else {
                                val handle = request.start()
                                val bytes = WhisperNative.transcribe(assets, samples, language, handle)
                                if (request.cancelled.get()) throw CancellationException()
                                val text = bytes?.toString(Charsets.UTF_8)?.trim().orEmpty()
                                if (text.isBlank()) TranscriptionResult.Unavailable("transcription_empty") else TranscriptionResult.Success(text)
                            }
                        } catch (error: Exception) {
                            TranscriptionResult.Unavailable(if (error.message == "transcription_limit") "transcription_limit" else "transcription_failed")
                        } catch (_: LinkageError) { TranscriptionResult.Unavailable("transcription_failed") }
                        finally { request.close() }
                        if (continuation.isActive) continuation.resume(result)
                    }
                }
            } finally { observer.cancel(); request.cancel() }
        }
    }
    // Cancellation/progress cannot race a freed JNI task. Native inference never holds this monitor.
    private class NativeRequest {
        val cancelled = AtomicBoolean(false)
        private var handle = 0L
        @Synchronized fun start(): Long {
            handle = WhisperNative.createTask()
            if (cancelled.get()) WhisperNative.cancel(handle)
            return handle
        }
        @Synchronized fun cancel() { cancelled.set(true); if (handle != 0L) WhisperNative.cancel(handle) }
        @Synchronized fun percent(): Int = if (handle == 0L) 0 else WhisperNative.progress(handle).coerceIn(0, 100)
        @Synchronized fun close() { if (handle != 0L) { WhisperNative.release(handle); handle = 0L } }
    }
}
