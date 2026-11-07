package com.lifetalea.app.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.unit.dp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.lifetalea.app.LibraryViewModel
import com.lifetalea.app.data.Attachment
import com.lifetalea.app.voice.OfflineTranscription
import com.lifetalea.app.voice.TranscriptionResult
import kotlinx.coroutines.*
import java.util.Locale

@Composable fun TranscriptionDialog(vm: LibraryViewModel, memoryId: String, attachment: Attachment,
                                    onDismiss: () -> Unit, onManualEdit: () -> Unit) {
    val locale = LocalConfiguration.current.locales[0]
    var language by remember { mutableStateOf(locale.language.takeIf { it in OfflineTranscription.languages } ?: "en") }
    var choosing by remember { mutableStateOf(false) }
    var running by remember { mutableStateOf(false) }
    var saving by remember { mutableStateOf(false) }
    var percent by remember { mutableIntStateOf(0) }
    var draft by remember { mutableStateOf<String?>(null) }
    var failure by remember { mutableStateOf<String?>(null) }
    var task by remember { mutableStateOf<Job?>(null) }
    val scope = rememberCoroutineScope()
    val lifecycle = LocalLifecycleOwner.current.lifecycle
    DisposableEffect(lifecycle) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_STOP) { task?.cancel(); running = false }
        }
        lifecycle.addObserver(observer)
        onDispose { lifecycle.removeObserver(observer); task?.cancel() }
    }
    fun start() {
        task = scope.launch {
            running = true; percent = 0; failure = null
            try {
                when (val result = vm.transcriptionEngine.transcribe(vm.repo.file(attachment.filename), language, true) { percent = it }) {
                    is TranscriptionResult.Success -> draft = result.text
                    is TranscriptionResult.Unavailable -> failure = result.reason
                }
            } finally { running = false }
        }
    }
    AlertDialog(onDismissRequest = { if (!saving) onDismiss() }, title = { Text(tr(if (draft == null) "transcription" else "transcription_review")) },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text(attachment.name)
                Text(tr("transcription_notice"))
                if (draft == null) {
                    Text(tr("language"))
                    Box {
                        OutlinedButton(enabled = !running, onClick = { choosing = true }) { Text(Locale.forLanguageTag(language).getDisplayLanguage(locale)) }
                        DropdownMenu(expanded = choosing, onDismissRequest = { choosing = false }, modifier = Modifier.heightIn(max = 300.dp)) {
                            OfflineTranscription.languages.forEach { code -> DropdownMenuItem(
                                text = { Text(Locale.forLanguageTag(code).getDisplayLanguage(locale)) },
                                onClick = { language = code; choosing = false }) }
                        }
                    }
                    if (running) {
                        Text(tr("transcription_working"))
                        if (percent == 0) LinearProgressIndicator(Modifier.fillMaxWidth())
                        else LinearProgressIndicator(progress = { percent / 100f }, modifier = Modifier.fillMaxWidth())
                    }
                    failure?.let { Text(tr(it), color = MaterialTheme.colorScheme.error) }
                    TextButton(enabled = !running, onClick = onManualEdit) { Text(tr("edit")) }
                } else OutlinedTextField(value = draft.orEmpty(), onValueChange = { draft = it.take(1000000) },
                    label = { Text(tr("transcript")) }, minLines = 4, modifier = Modifier.fillMaxWidth().heightIn(max = 280.dp), enabled = !saving)
            }
        },
        confirmButton = {
            if (draft == null) TextButton(enabled = !running, onClick = { start() }) { Text(tr("confirm")) }
            else TextButton(enabled = !saving && !draft.isNullOrBlank(), onClick = {
                saving = true
                scope.launch {
                    try {
                        check(vm.repo.dao.appendTranscript(memoryId, draft!!.trim(), System.currentTimeMillis()) == 1)
                        onDismiss()
                    } catch (error: Exception) {
                        if (error is CancellationException) throw error
                        vm.error.value = "operation_failed"
                    } finally { saving = false }
                }
            }) { Text(tr("transcription_apply")) }
        },
        dismissButton = { TextButton(enabled = !saving, onClick = onDismiss) { Text(tr("cancel")) } })
}
