package com.lifetalea.app

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.lifetalea.app.data.*
import com.lifetalea.app.voice.*
import kotlinx.coroutines.runBlocking
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.security.MessageDigest

/** The host runs prepare, force-stops only .debug, then runs verify in a new process. */
@RunWith(AndroidJUnit4::class)
class TranscriptionRestartTest {
    @Test fun reviewedTranscriptSurvivesRestart() = runBlocking {
        val instrument = InstrumentationRegistry.getInstrumentation()
        val context = instrument.targetContext
        val repo = LibraryRepository(context, LifeDatabase.open(context))
        val marker = File(context.noBackupFilesDir, "transcription-restart-fixture.json")
        fun hash(bytes: ByteArray) = MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it) }
        val phase = InstrumentationRegistry.getArguments().getString("transcriptionRestartPhase") ?: "inline"
        require(phase in listOf("prepare", "verify", "inline"))
        if (phase != "verify") {
            check(!marker.exists()) { "Finish or clear the previous dedicated QA fixture first" }
            val memory = Memory(title = "Fictional restart QA", transcript = "Existing reviewed words.")
            val name = "${memory.id}.m4a"
            val file = repo.file(name)
            instrument.context.assets.open("transcription/garden.m4a").use { input -> file.outputStream().use { input.copyTo(it) } }
            try {
                val result = OfflineTranscription(context).transcribe(file, "en", true)
                assertTrue(result is TranscriptionResult.Success)
                val corrected = (result as TranscriptionResult.Success).text + " Corrected by the reader."
                repo.dao.save(memory)
                repo.dao.save(Attachment(memoryId = memory.id, filename = name, kind = "audio", name = "Fictional restart QA"))
                assertEquals(1, repo.dao.appendTranscript(memory.id, corrected, System.currentTimeMillis()))
                val expected = memory.transcript + "\n\n" + corrected
                marker.writeText(JSONObject().put("memoryId", memory.id).put("filename", name)
                    .put("pid", android.os.Process.myPid()).put("textSha256", hash(expected.toByteArray()))
                    .put("audioSha256", hash(file.readBytes())).toString())
            } catch (error: Throwable) { repo.removeMemory(memory.id); file.delete(); marker.delete(); throw error }
        }
        if (phase != "prepare") {
            val saved = JSONObject(marker.readText())
            val id = saved.getString("memoryId")
            try {
                val changed = android.os.Process.myPid() != saved.getInt("pid")
                if (phase == "verify") assertTrue("The app must have a new process", changed)
                val memory = repo.dao.allMemories().single { it.id == id }
                assertEquals(saved.getString("textSha256"), hash(memory.transcript.toByteArray()))
                assertEquals(saved.getString("audioSha256"), hash(repo.file(saved.getString("filename")).readBytes()))
                val evidence = File(context.filesDir, "test-evidence/transcription").apply { mkdirs() }
                File(evidence, "process-restart.json").writeText(JSONObject().put("status", "PASS")
                    .put("processChanged", changed).put("correctedTranscriptPersisted", true)
                    .put("existingTranscriptPreserved", true).put("originalAudioUnchanged", true).toString(2))
            } finally { repo.removeMemory(id); marker.delete() }
        }
    }
}
