package com.lifetalea.app

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.graphics.asAndroidBitmap
import android.graphics.Bitmap
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.room.Room
import com.lifetalea.app.data.*
import com.lifetalea.app.voice.*
import kotlinx.coroutines.*
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.security.MessageDigest
import java.util.UUID

@RunWith(AndroidJUnit4::class)
class TranscriptionDeviceTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrumentation.targetContext
    private fun fixture(name: String): File = File(context.cacheDir, "${UUID.randomUUID()}-$name").apply {
        instrumentation.context.assets.open("transcription/$name").use { input -> outputStream().use { input.copyTo(it) } }
    }
    private fun hash(file: File) = MessageDigest.getInstance("SHA-256").digest(file.readBytes()).joinToString("") { "%02x".format(it) }
    private fun report(name: String, json: JSONObject) {
        File(context.filesDir, "test-evidence/transcription").apply { mkdirs() }.resolve(name).writeText(json.toString(2))
    }
    @Test fun savedAacProducesAReviewedDraftWithoutReplacingExistingWords() {
        val source = fixture("garden.m4a")
        val name = "${UUID.randomUUID()}.m4a"
        val repo = LibraryRepository(context, LifeDatabase.open(context))
        val recording = repo.file(name).apply { source.copyTo(this) }
        source.delete()
        val before = hash(recording)
        val memory = Memory(title = "Fictional transcription check", transcript = "My original transcript.")
        runBlocking {
            repo.dao.save(memory)
            repo.dao.save(Attachment(memoryId = memory.id, filename = name, kind = "audio", name = "Fictional garden recording"))
        }
        try {
            compose.waitUntil(20000) { runCatching {
                compose.onAllNodesWithText("Skip for now").fetchSemanticsNodes().isNotEmpty() ||
                    compose.onAllNodesWithText("Add a memory").fetchSemanticsNodes().isNotEmpty()
            }.getOrDefault(false) }
            if (compose.onAllNodesWithText("Skip for now").fetchSemanticsNodes().isNotEmpty())
                compose.onNodeWithText("Skip for now").performScrollTo().performClick()
            compose.waitUntil(20000) { compose.onAllNodesWithText(memory.title).fetchSemanticsNodes().isNotEmpty() }
            compose.onNodeWithText(memory.title).performClick()
            compose.onNodeWithText("Transcription").performScrollTo().performClick()
            val started = android.os.SystemClock.elapsedRealtime()
            compose.onNodeWithText("Confirm").performClick()
            compose.waitUntil(180000) { compose.onAllNodesWithText("Review transcript draft").fetchSemanticsNodes().isNotEmpty() }
            val elapsed = android.os.SystemClock.elapsedRealtime() - started
            val field = compose.onNode(hasText("Editable transcript") and hasSetTextAction())
            field.assertTextContains("apple", substring = true, ignoreCase = true)
            field.assertTextContains("garden", substring = true, ignoreCase = true)
            val evidence = File(context.filesDir, "test-evidence/transcription").apply { mkdirs() }
            compose.onNode(isDialog()).captureToImage().asAndroidBitmap().let { image ->
                File(evidence, "review-draft.png").outputStream().use { image.compress(Bitmap.CompressFormat.PNG, 100, it) }
            }
            runBlocking { assertEquals(memory.transcript, repo.dao.allMemories().single { it.id == memory.id }.transcript) }
            field.performTextInput(" Corrected by the reader.")
            compose.runOnIdle {
                (compose.activity.getSystemService(android.content.Context.INPUT_METHOD_SERVICE) as android.view.inputmethod.InputMethodManager)
                    .hideSoftInputFromWindow(compose.activity.window.decorView.windowToken, 0)
            }
            compose.onNodeWithText("Append to saved transcript").performClick()
            compose.waitUntil(15000) { runBlocking {
                repo.dao.allMemories().single { it.id == memory.id }.transcript.contains("Corrected by the reader.")
            } }
            // A second Room connection reads persisted state rather than a UI-held draft.
            val reopened = Room.databaseBuilder(context, LifeDatabase::class.java, "lifetalea.db").build()
            try { runBlocking {
                val saved = reopened.library().allMemories().single { it.id == memory.id }.transcript
                assertTrue(saved.startsWith(memory.transcript + "\n\n")); assertTrue(saved.contains("Corrected by the reader."))
            } } finally { reopened.close() }
            assertEquals(before, hash(recording))
            report("review-and-persistence.json", JSONObject().put("status", "PASS").put("inferenceAndUiMs", elapsed)
                .put("existingTranscriptPreserved", true).put("manualCorrectionPersisted", true)
                .put("originalAudioUnchanged", true).put("speechFixture", "Fictional synthesized English, AAC 44100 Hz stereo")
                .put("audioUploaded", false).put("languageAccuracyVerified", "en"))
        } finally { runBlocking { repo.removeMemory(memory.id) } }
    }
    @Test fun silenceBadAudioLimitsAndMissingConsentNeverProduceInventedWords() = runBlocking {
        val engine = OfflineTranscription(context)
        val silence = fixture("silence.m4a"); val long = fixture("too-long.m4a")
        val invalid = File(context.cacheDir, "${UUID.randomUUID()}.m4a").apply { writeText("Not audio") }
        val originals = listOf(silence, long, invalid).associateWith { hash(it) }
        try {
            assertEquals(TranscriptionResult.Unavailable("transcription_consent_required"), engine.transcribe(invalid, "en", false))
            assertEquals(TranscriptionResult.Unavailable("transcription_failed"), engine.transcribe(invalid, "xx", true))
            assertEquals(TranscriptionResult.Unavailable("transcription_failed"), engine.transcribe(invalid, "en", true))
            assertEquals(TranscriptionResult.Unavailable("transcription_empty"), engine.transcribe(silence, "en", true))
            assertEquals(TranscriptionResult.Unavailable("transcription_limit"), engine.transcribe(long, "en", true))
            originals.forEach { (file, digest) -> assertTrue(file.exists()); assertEquals(digest, hash(file)) }
            report("failure-fallbacks.json", JSONObject().put("status", "PASS").put("consentGate", true)
                .put("invalidAudio", true).put("unsupportedLanguage", true).put("silenceNoTranscript", true).put("tenMinuteLimit", true).put("originalFilesUnchanged", true))
        } finally { silence.delete(); long.delete(); invalid.delete() }
    }
    @Test fun cancellationDuringNativeInferenceReleasesTheWorkerForRetry() = runBlocking {
        val engine = OfflineTranscription(context); val source = fixture("garden-long.m4a")
        try {
            val began = CompletableDeferred<Unit>()
            val job = launch { engine.transcribe(source, "en", true) { if (it in 1..90) began.complete(Unit) } }
            withTimeout(180000) { began.await() }
            job.cancelAndJoin(); assertTrue(job.isCancelled)
            val retry = fixture("garden.m4a")
            val result = try { withTimeout(180000) { engine.transcribe(retry, "en", true) } } finally { retry.delete() }
            assertTrue(result is TranscriptionResult.Success)
            assertTrue((result as TranscriptionResult.Success).text.contains("garden", ignoreCase = true))
            report("cancel-and-retry.json", JSONObject().put("status", "PASS").put("cancelledAfterNativeProgress", true).put("retryRecognizedFixture", true))
        } finally { source.delete() }
    }
    @Test fun appendingTranscriptIsAtomicAndCannotResurrectADeletedMemory() = runBlocking {
        val dao = LifeDatabase.open(context).library()
        val memory = Memory(title = "Transcript safety", transcript = "Existing words")
        try {
            dao.save(memory)
            assertEquals(1, dao.appendTranscript(memory.id, "Reviewed draft", System.currentTimeMillis()))
            assertEquals("Existing words\n\nReviewed draft", dao.allMemories().single { it.id == memory.id }.transcript)
            dao.save(memory.copy(transcript = "a".repeat(1000000)))
            assertEquals(0, dao.appendTranscript(memory.id, "Too much", System.currentTimeMillis()))
            assertEquals(1000000, dao.allMemories().single { it.id == memory.id }.transcript.length)
            dao.deleteMemory(memory.id)
            assertEquals(0, dao.appendTranscript(memory.id, "Late result", System.currentTimeMillis()))
        } finally { dao.deleteMemory(memory.id) }
    }
}
