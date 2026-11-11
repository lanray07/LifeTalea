package com.lifetalea.app

import android.app.Application
import android.net.Uri
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.lifetalea.app.data.*
import com.lifetalea.app.voice.*
import com.lifetalea.app.billing.*
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import java.util.UUID

class LibraryViewModel(app: Application) : AndroidViewModel(app) {
    val repo = LibraryRepository(app, LifeDatabase.open(app))
    val settings = Settings(app)
    val preferences = settings.flow.stateIn(viewModelScope, SharingStarted.Eagerly, Preferences())
    val memories = repo.dao.memories().stateIn(viewModelScope, SharingStarted.Eagerly, emptyList())
    val albums = repo.dao.albums().stateIn(viewModelScope, SharingStarted.Eagerly, emptyList())
    val links = repo.dao.links().stateIn(viewModelScope, SharingStarted.Eagerly, emptyList())
    val media = repo.dao.media().stateIn(viewModelScope, SharingStarted.Eagerly, emptyList())
    val books = repo.dao.books().stateIn(viewModelScope, SharingStarted.Eagerly, emptyList())
    val pages = repo.dao.pages().stateIn(viewModelScope, SharingStarted.Eagerly, emptyList())
    val error = MutableStateFlow<String?>(null)
    val busy = MutableStateFlow(false)
    val recorder = StoryRecorder(app)
    val transcriptionEngine: TranscriptionEngine by lazy { OfflineTranscription(app) }
    val billing = AmazonBilling(app)
    private class BackupRequest(val photos: Boolean, val audio: Boolean, val password: CharArray)
    private var pendingBackup: BackupRequest? = null

    fun prepareBackup(photos: Boolean, audio: Boolean, password: String): Boolean {
        if (pendingBackup != null) return false
        if (password.isNotEmpty() && (password.length < 10 || !billing.state.value.premium)) return false
        pendingBackup = BackupRequest(photos, audio, password.toCharArray())
        return true
    }

    fun finishBackup(uri: Uri?) {
        val request = pendingBackup
        pendingBackup = null
        if (uri == null) {
            request?.password?.fill('\u0000')
            return
        }
        if (request == null) {
            error.value = "operation_failed"
            return
        }
        run {
            try {
                withContext(Dispatchers.IO) {
                    val bytes = BackupService(repo).create(request.photos, request.audio, request.password)
                    getApplication<Application>().contentResolver.openOutputStream(uri)?.use { it.write(bytes) }
                        ?: error("No output")
                }
                error.value = "backup_saved"
            } finally {
                request.password.fill('\u0000')
            }
        }
    }
    private var recordingMemoryId: String? = null
    init { recorder.onAutomaticStop = { stopRecording() } }
    fun run(action: suspend () -> Unit) = viewModelScope.launch {
        busy.value = true
        try { action() } catch (e: Exception) { if (e is CancellationException) throw e; error.value = "operation_failed" }
        finally { busy.value = false }
    }
    fun save(memory: Memory, albumIds: Set<String>, done: () -> Unit) = run { repo.save(memory, albumIds); done() }
    fun startRecording(memoryId: String) {
        try { recorder.start(repo.file(UUID.randomUUID().toString() + ".m4a"), if (billing.state.value.premium) 3600000 else 180000); recordingMemoryId = memoryId }
        catch (e: Exception) { error.value = "recording_failed" }
    }
    fun stopRecording() {
        val recording = recorder.stop(); val id = recordingMemoryId; recordingMemoryId = null
        if (recording != null && id != null) run { repo.dao.save(Attachment(memoryId = id, filename = recording.first.name, kind = "audio", name = getApplication<Application>().getString(R.string.voice_story), durationMs = recording.second)) }
        else if (id != null) error.value = "recording_failed"
    }
    fun importPhoto(id: String, uri: Uri) = run { repo.importPhoto(id, uri) }
    override fun onCleared() { finishBackup(null); stopRecording(); billing.close(); super.onCleared() }
}
