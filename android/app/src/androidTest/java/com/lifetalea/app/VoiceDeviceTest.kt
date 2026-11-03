package com.lifetalea.app
import android.Manifest
import android.content.Intent
import android.media.MediaMetadataRetriever
import android.media.MediaPlayer
import android.speech.SpeechRecognizer
import android.speech.RecognitionService
import android.speech.tts.TextToSpeech
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.lifetalea.app.voice.StoryRecorder
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
@RunWith(AndroidJUnit4::class)
class VoiceDeviceTest {
    @Test fun foregroundRecordingPauseResumeAndPlayback() {
        val instrument = InstrumentationRegistry.getInstrumentation(); val context = instrument.targetContext
        instrument.uiAutomation.grantRuntimePermission(context.packageName, Manifest.permission.RECORD_AUDIO)
        val folder = File(context.filesDir, "test-evidence").apply { mkdirs() }; val audio = File(context.cacheDir, "mic-diagnostic.m4a")
        val recorder = StoryRecorder(context)
        ActivityScenario.launch(MainActivity::class.java).use {
            try {
                instrument.runOnMainSync { recorder.start(audio, 10000) }; Thread.sleep(1200)
                instrument.runOnMainSync { recorder.pause() }; assertTrue(recorder.state.value.paused); Thread.sleep(200)
                instrument.runOnMainSync { recorder.resume() }; Thread.sleep(1200)
                var duration = 0L; instrument.runOnMainSync { duration = recorder.stop()?.second ?: 0 }
                assertTrue(audio.length() > 0); assertTrue(duration >= 2000)
                val metadata = MediaMetadataRetriever(); metadata.setDataSource(audio.path)
                val encodedDuration = metadata.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)!!.toLong(); metadata.release()
                assertTrue(encodedDuration >= 1800)
                val complete = CountDownLatch(1); var failed = false
                val player = MediaPlayer()
                try {
                    player.setDataSource(audio.path); player.setOnCompletionListener { complete.countDown() }; player.setOnErrorListener { _, _, _ -> failed = true; complete.countDown(); true }; player.prepare()
                    val sought = CountDownLatch(1); player.setOnSeekCompleteListener { sought.countDown() }
                    player.seekTo(1000); assertTrue(sought.await(5, TimeUnit.SECONDS))
                    // AAC seeking may round to a sync frame; playback must still complete afterward.
                    assertTrue(player.currentPosition in 0..encodedDuration.toInt()); player.start()
                    Thread.sleep(100); player.pause(); assertFalse(player.isPlaying); player.start()
                    assertTrue(complete.await(8, TimeUnit.SECONDS)); assertFalse(failed)
                } finally { player.release() }
                val report = JSONObject().put("device", android.os.Build.MODEL).put("sdk", android.os.Build.VERSION.SDK_INT).put("recordedDurationMs", duration).put("encodedDurationMs", encodedDuration).put("playbackCompleted", true).put("rawAudioRetained", false).put("speechRecognitionAvailable", SpeechRecognizer.isRecognitionAvailable(context))
                report.put("seekCallbackCompleted", true).put("playbackPauseResume", true)
                report.put("recognitionServices", context.packageManager.queryIntentServices(Intent(RecognitionService.SERVICE_INTERFACE), 0).map { it.serviceInfo.packageName }.joinToString(","))
                report.put("ttsServices", context.packageManager.queryIntentServices(Intent(TextToSpeech.Engine.INTENT_ACTION_TTS_SERVICE), 0).map { it.serviceInfo.packageName }.joinToString(","))
                File(folder,"voice-device.json").writeText(report.toString(2))
            } finally { instrument.runOnMainSync { recorder.stop() }; audio.delete() }
        }
    }
}
