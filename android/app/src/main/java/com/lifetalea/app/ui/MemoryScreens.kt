package com.lifetalea.app.ui
import android.media.MediaPlayer
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import coil.compose.AsyncImage
import com.lifetalea.app.LibraryViewModel
import com.lifetalea.app.data.*
import kotlinx.coroutines.delay
import java.time.*
import java.time.format.*
import java.util.Locale

@Composable fun dateLabel(memory: Memory): String {
    val locale = LocalConfiguration.current.locales[0]
    return if (memory.precision == "UNKNOWN") tr("unknown_date") else MemoryRules.formattedDate(memory,locale)
}
@Composable fun MemoryCard(memory: Memory, photo: Attachment?, vm: LibraryViewModel, onOpen: () -> Unit) {
    OutlinedCard(onClick = onOpen, modifier = Modifier.fillMaxWidth()) {
        Row(Modifier.padding(18.dp), horizontalArrangement = Arrangement.spacedBy(16.dp), verticalAlignment = Alignment.CenterVertically) {
            if (photo != null) AsyncImage(vm.repo.file(photo.filename), tr("photos"), Modifier.size(92.dp), contentScale = ContentScale.Crop)
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text(dateLabel(memory), style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.secondary)
                Text(memory.title, style = MaterialTheme.typography.titleLarge)
                if (memory.story.isNotBlank()) Text(memory.story, maxLines = 2, overflow = TextOverflow.Ellipsis)
                if (memory.tags.isNotBlank()) Text(memory.tags, style = MaterialTheme.typography.labelMedium)
            }
            IconButton(onClick = { vm.run { vm.repo.dao.save(memory.copy(favourite = !memory.favourite)) } }) { Icon(if (memory.favourite) Icons.Outlined.Star else Icons.Outlined.StarOutline, tr("favourite")) }
        }
    }
}
@Composable fun MemoryEditor(vm: LibraryViewModel, memory: Memory, albumIds: Set<String>, albums: List<Album>, onCancel: () -> Unit, onSaved: () -> Unit) {
    var title by rememberSaveable(memory.id) { mutableStateOf(memory.title) }
    var story by rememberSaveable(memory.id) { mutableStateOf(memory.story) }
    var date by rememberSaveable(memory.id) { mutableStateOf(memory.date) }
    var precision by rememberSaveable(memory.id) { mutableStateOf(memory.precision) }
    var location by rememberSaveable(memory.id) { mutableStateOf(memory.location) }
    var tags by rememberSaveable(memory.id) { mutableStateOf(memory.tags) }
    var transcript by rememberSaveable(memory.id) { mutableStateOf(memory.transcript) }
    var selected by rememberSaveable(memory.id) { mutableStateOf(albumIds.toList()) }
    val busy by vm.busy.collectAsStateWithLifecycle()
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Heading(tr("edit")); Text(tr("save_first"), style = MaterialTheme.typography.bodySmall)
        Field("title", title, { title = it.take(300) }); Field("story", story, { story = it.take(1000000) }, 5)
        Text(tr("precision")); Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf("UNKNOWN" to "unknown", "YEAR" to "year", "MONTH" to "month", "DAY" to "day").forEach { (value, label) -> Choice(precision == value, tr(label)) { precision = value; date = "" } }
        }
        if (precision != "UNKNOWN") { Field("date", date, { date = MemoryRules.normaliseDateDigits(it).take(10) }); Text(tr("date_hint"), style = MaterialTheme.typography.bodySmall) }
        Field("location", location, { location = it.take(300) }); Field("tags", tags, { tags = it.take(1000) })
        Field("transcript", transcript, { transcript = it.take(1000000) }, 3)
        if (albums.isNotEmpty()) { Text(tr("albums")); albums.forEach { a -> Row(verticalAlignment = Alignment.CenterVertically) { Checkbox(a.id in selected, { selected = if (it) selected + a.id else selected - a.id }); Text(a.title) } } }
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Button(enabled = !busy, onClick = {
                if (title.isBlank() || !MemoryRules.validDate(date, precision)) vm.error.value = "invalid_form"
                else vm.save(memory.copy(title = title.trim(), story = story, date = date, precision = precision, location = location, tags = tags, transcript = transcript), selected.toSet(), onSaved)
            }) { Text(tr("save")) }
            TextButton(onClick = onCancel) { Text(tr("cancel")) }
        }
        Spacer(Modifier.height(24.dp))
    }
}
@Composable fun MemoryDetail(vm: LibraryViewModel, memory: Memory, attachments: List<Attachment>, onBack: () -> Unit, onEdit: () -> Unit, onRecord: () -> Unit, onDelete: () -> Unit, onRead: () -> Unit, onStopRead: () -> Unit, onRemoveAttachment: (Attachment) -> Unit) {
    val photoPicker = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri -> uri?.let { vm.importPhoto(memory.id, it) } }
    val recording by vm.recorder.state.collectAsStateWithLifecycle()
    var elapsed by remember { mutableLongStateOf(0) }
    var transcription by remember { mutableStateOf<Attachment?>(null) }
    var rename by remember { mutableStateOf<Attachment?>(null) }
    var name by remember { mutableStateOf("") }
    LaunchedEffect(recording.active, recording.paused) { while(recording.active) { elapsed = vm.recorder.elapsed(); delay(250) } }
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Row { TextButton(onClick = onBack, enabled = !recording.active) { Icon(Icons.AutoMirrored.Outlined.ArrowBack, null); Text(tr("back")) }; Spacer(Modifier.weight(1f)); TextButton(onClick = onEdit, enabled = !recording.active) { Text(tr("edit")) } }
        Heading(memory.title, dateLabel(memory))
        if (memory.story.isNotBlank()) Text(memory.story, style = MaterialTheme.typography.bodyLarge)
        if (memory.location.isNotBlank()) Text(memory.location)
        if (memory.tags.isNotBlank()) Text(memory.tags, color = MaterialTheme.colorScheme.secondary)
        Row(Modifier.horizontalScroll(rememberScrollState())) { TextButton(onClick = onRead) { Text(tr("read_story")) }; TextButton(onClick = onStopRead) { Text(tr("stop_speaking")) } }
        Text(tr("photos"), style = MaterialTheme.typography.titleLarge)
        attachments.filter { it.kind == "photo" }.forEach { a ->
            AsyncImage(vm.repo.file(a.filename), tr("photos"), Modifier.fillMaxWidth().heightIn(max = 340.dp), contentScale = ContentScale.Fit)
            TextButton(onClick = { onRemoveAttachment(a) }) { Text(tr("remove")) }
        }
        OutlinedButton(onClick = { photoPicker.launch(arrayOf("image/*")) }, enabled = !recording.active) { Icon(Icons.Outlined.AddPhotoAlternate, null); Text(tr("add_photo")) }
        Text(tr("voice_story"), style = MaterialTheme.typography.titleLarge)
        Text(tr("recording_notice"), style = MaterialTheme.typography.bodySmall)
        if (recording.active) {
            Text(tr(if (recording.paused) "recording_paused" else "recording") + " · " + duration(elapsed, LocalConfiguration.current.locales[0]))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(onClick = { runCatching { if (recording.paused) vm.recorder.resume() else vm.recorder.pause() }.onFailure { vm.error.value = "recording_failed" } }) { Text(tr(if (recording.paused) "resume" else "pause")) }
                Button(onClick = { vm.stopRecording() }) { Text(tr("stop_save")) }
            }
        } else Button(onClick = onRecord) { Icon(Icons.Outlined.Mic, null); Text(tr("record")) }
        attachments.filter { it.kind == "audio" }.forEach { a ->
            AudioPlayer(vm.repo.file(a.filename).path, a.name)
            Row { TextButton(onClick = { rename = a; name = a.name }) { Text(tr("rename")) }; TextButton(onClick = { onRemoveAttachment(a) }) { Text(tr("delete")) }; TextButton(enabled = !recording.active, onClick = { transcription = a }) { Text(tr("transcription")) } }
        }
        if (memory.transcript.isNotBlank()) { Text(tr("transcript"), style = MaterialTheme.typography.titleLarge); Text(memory.transcript) }
        Row { TextButton(enabled = !recording.active, onClick = { vm.run { vm.repo.duplicate(memory.id); vm.error.value = "saved" } }) { Text(tr("duplicate")) }; TextButton(onClick = onDelete, enabled = !recording.active) { Text(tr("delete"), color = MaterialTheme.colorScheme.error) } }
    }
    transcription?.let { attachment -> TranscriptionDialog(vm, memory.id, attachment, onDismiss = { transcription = null }, onManualEdit = { transcription = null; onEdit() }) }
    rename?.let { a -> AlertDialog(onDismissRequest = { rename = null }, title = { Text(tr("rename")) }, text = { Field("title", name, { name = it.take(200) }) }, confirmButton = { TextButton(enabled = name.isNotBlank(), onClick = { vm.run { vm.repo.dao.save(a.copy(name = name)) }; rename = null }) { Text(tr("save")) } }) }
}
fun duration(ms: Long, locale: Locale = Locale.ROOT): String = "%02d:%02d".format(locale, ms / 60000, ms / 1000 % 60)
@Composable fun AudioPlayer(path: String, name: String) {
    var player by remember(path) { mutableStateOf<MediaPlayer?>(null) }
    var playing by remember(path) { mutableStateOf(false) }
    var position by remember(path) { mutableFloatStateOf(0f) }
    var length by remember(path) { mutableFloatStateOf(1f) }
    var failed by remember(path) { mutableStateOf(false) }
    val lifecycle = androidx.lifecycle.compose.LocalLifecycleOwner.current
    DisposableEffect(path, lifecycle) {
        val observer = androidx.lifecycle.LifecycleEventObserver { _, event -> if (event == androidx.lifecycle.Lifecycle.Event.ON_STOP) { player?.pause(); playing = false } }
        lifecycle.lifecycle.addObserver(observer)
        onDispose { lifecycle.lifecycle.removeObserver(observer); player?.release(); player = null }
    }
    LaunchedEffect(playing) { while (playing) { position = player?.currentPosition?.toFloat() ?: 0f; delay(250) } }
    OutlinedCard(Modifier.fillMaxWidth()) { Column(Modifier.padding(16.dp)) {
        Text(name, style = MaterialTheme.typography.titleMedium)
        if (failed) Text(tr("operation_failed"))
        Row(verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = {
                runCatching {
                    if (player == null) { player = MediaPlayer().apply { setDataSource(path); setOnPreparedListener { length = it.duration.toFloat().coerceAtLeast(1f); it.start(); playing = true }; setOnCompletionListener { playing = false; position = 0f }; setOnErrorListener { _, _, _ -> failed = true; playing = false; true }; prepareAsync() } }
                    else if (playing) { player?.pause(); playing = false } else { player?.start(); playing = true }
                }.onFailure { failed = true; playing = false }
            }) { Icon(if (playing) Icons.Outlined.Pause else Icons.Outlined.PlayArrow, tr(if (playing) "pause" else "play")) }
            Slider(position.coerceIn(0f, length), { position = it; player?.seekTo(it.toInt()) }, valueRange = 0f..length, modifier = Modifier.weight(1f))
            Text(duration(position.toLong(), LocalConfiguration.current.locales[0]))
        }
    } }
}
