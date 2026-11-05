package com.lifetalea.app.ui

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.lifetalea.app.*
import com.lifetalea.app.R
import com.lifetalea.app.data.*
import com.lifetalea.app.voice.*
import java.util.Locale

private val destinations = listOf("memories" to Icons.Outlined.AutoStories, "albums" to Icons.Outlined.PhotoLibrary, "timeline" to Icons.Outlined.Timeline, "keepsakes" to Icons.Outlined.Book, "settings" to Icons.Outlined.Settings)
@Composable fun LifeApp(vm: LibraryViewModel) {
    val context = LocalContext.current
    val preferences by vm.preferences.collectAsStateWithLifecycle()
    val memories by vm.memories.collectAsStateWithLifecycle()
    val albums by vm.albums.collectAsStateWithLifecycle()
    val media by vm.media.collectAsStateWithLifecycle()
    val links by vm.links.collectAsStateWithLifecycle()
    val books by vm.books.collectAsStateWithLifecycle()
    val pages by vm.pages.collectAsStateWithLifecycle()
    val busy by vm.busy.collectAsStateWithLifecycle()
    val error by vm.error.collectAsStateWithLifecycle()
    val recording by vm.recorder.state.collectAsStateWithLifecycle()
    var screen by rememberSaveable { mutableStateOf("memories") }
    var selected by rememberSaveable { mutableStateOf<String?>(null) }
    var bookId by rememberSaveable { mutableStateOf<String?>(null) }
    var showVoice by remember { mutableStateOf(false) }
    var showPremium by remember { mutableStateOf(false) }
    var deletion by remember { mutableStateOf<Pair<String, () -> Unit>?>(null) }
    var albumDialog by remember { mutableStateOf<Album?>(null) }
    var albumName by rememberSaveable { mutableStateOf("") }
    var query by rememberSaveable { mutableStateOf("") }
    var year by rememberSaveable { mutableStateOf("") }
    var albumFilter by rememberSaveable { mutableStateOf<String?>(null) }
    var favourites by rememberSaveable { mutableStateOf(false) }
    val assistant = remember { VoiceAssistant(context) }
    DisposableEffect(Unit) { onDispose { assistant.close() } }
    val lifecycle = androidx.lifecycle.compose.LocalLifecycleOwner.current
    DisposableEffect(lifecycle) {
        val observer = androidx.lifecycle.LifecycleEventObserver { _, event -> if (event == androidx.lifecycle.Lifecycle.Event.ON_STOP) assistant.stop() }
        lifecycle.lifecycle.addObserver(observer); onDispose { lifecycle.lifecycle.removeObserver(observer) }
    }
    val locale = LocalConfiguration.current.locales[0] ?: Locale.getDefault()
    fun message(key: String) { vm.error.value = key }
    fun newMemory(story: String = "") {
        if (recording.active) { message("finish_recording"); return }
        selected = java.util.UUID.randomUUID().toString(); query = story; screen = "editor"
    }
    fun openMemory(id: String) { if (recording.active) { message("finish_recording"); return }; selected = id; screen = "detail" }
    fun navigate(next: String) { if (recording.active) { message("finish_recording"); return }; selected = null; bookId = null; screen = next }
    var microphoneNotice by remember { mutableStateOf(false) }
    val microphone = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) selected?.takeIf { id -> memories.any { it.id == id } }?.let { vm.startRecording(it) }
        else message("microphone_denied")
    }
    fun record() {
        val id = selected
        if (id == null || memories.none { it.id == id }) { message("record_first"); return }
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) vm.startRecording(id)
        else microphoneNotice = true
    }
    fun command(text: String) {
        // The consent/help copy explicitly limits commands to English. Keep that
        // command language available when the interface uses another locale.
        val result = CommandParser.parse(text, Locale.ENGLISH)
        when (result.intent) {
            VoiceIntent.NEW_MEMORY -> newMemory()
            VoiceIntent.START_RECORDING -> record()
            VoiceIntent.STOP_RECORDING -> vm.stopRecording()
            VoiceIntent.TIMELINE -> navigate("timeline")
            VoiceIntent.ALBUMS -> {
                if (recording.active) { message("finish_recording"); return }
                val name = result.query
                val exact = albums.filter { it.title.trim().lowercase(Locale.ENGLISH) == name }
                val found = when {
                    name.isEmpty() -> null
                    exact.isNotEmpty() -> exact.singleOrNull()
                    name.endsWith(" album") -> albums.singleOrNull {
                        it.title.trim().lowercase(Locale.ENGLISH) == name.removeSuffix(" album")
                    }
                    else -> null
                }
                if (found == null) navigate("albums") else {
                    navigate("memories")
                    query = ""
                    year = ""
                    favourites = false
                    albumFilter = found.id
                }
            }
            VoiceIntent.KEEPSAKE -> navigate("keepsakes")
            VoiceIntent.SEARCH -> {
                if (recording.active) { message("finish_recording"); return }
                navigate("timeline")
                query = ""
                albumFilter = null
                favourites = false
                year = if (result.query == "last year") (java.time.Year.now().value - 1).toString() else result.query
            }
            VoiceIntent.READ_STORY -> {
                val memory = memories.find { it.id == selected } ?: memories.firstOrNull()
                if (memory == null) message("no_story") else assistant.speak(memory.story, locale) { message("tts_unavailable") }
            }
            VoiceIntent.UNKNOWN -> message("unknown_command")
        }
        if (preferences.spoken && result.intent != VoiceIntent.UNKNOWN && result.intent != VoiceIntent.READ_STORY) assistant.speak(context.getString(R.string.done), locale) { message("tts_unavailable") }
    }
    if (!preferences.onboarded) {
        Onboarding { purpose -> vm.run { vm.settings.onboard(purpose) } }
        return
    }
    Surface(Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
        BoxWithConstraints {
            val wide = maxWidth >= 760.dp
            Row(Modifier.fillMaxSize().statusBarsPadding().navigationBarsPadding()) {
                if (wide) Column(Modifier.width(208.dp).fillMaxHeight().background(Forest).padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Image(painterResource(R.drawable.ic_book), null, Modifier.size(64.dp))
                    Text("LifeTalea", color = Ivory, style = MaterialTheme.typography.headlineMedium)
                    Spacer(Modifier.height(28.dp))
                    destinations.forEach { (key, icon) ->
                        Surface(onClick = { navigate(key) }, color = if (screen == key) Color(0xFF765A2E) else Color.Transparent, shape = RoundedCornerShape(12.dp)) {
                            Row(Modifier.fillMaxWidth().padding(12.dp).heightIn(min = 32.dp), horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) { Icon(icon, null, tint = Ivory); Text(tr(key), color = Ivory) }
                        }
                    }
                    Spacer(Modifier.weight(1f)); Text(tr("saved_locally"), color = Ivory, style = MaterialTheme.typography.bodySmall)
                }
                Column(Modifier.weight(1f)) {
                    Row(Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 8.dp), verticalAlignment = Alignment.CenterVertically) {
                        if (!wide) Text("LifeTalea", fontFamily = FontFamily.Serif, style = MaterialTheme.typography.titleLarge, modifier = Modifier.weight(1f)) else Spacer(Modifier.weight(1f))
                        IconButton(onClick = { showVoice = true }) { Icon(Icons.Outlined.Mic, tr("voice_commands")) }
                        TextButton(onClick = { showPremium = true }) { Text(tr("premium")) }
                    }
                    if (busy) LinearProgressIndicator(Modifier.fillMaxWidth())
                    Box(Modifier.weight(1f).fillMaxWidth()) {
                        val memory = memories.find { it.id == selected }
                        when (screen) {
                            "editor" -> MemoryEditor(vm, memory ?: Memory(id = selected ?: java.util.UUID.randomUUID().toString(), story = query), links.filter { it.memoryId == selected }.map { it.albumId }.toSet(), albums, onCancel = { screen = if (memory == null) "memories" else "detail" }, onSaved = { query = ""; screen = "detail" })
                            "detail" -> memory?.let { m -> MemoryDetail(vm, m, media.filter { it.memoryId == m.id }, onBack = { navigate("memories") }, onEdit = { screen = "editor" }, onRecord = { record() }, onDelete = { deletion = "delete_memory" to { vm.run { vm.repo.removeMemory(m.id); navigate("memories") } } }, onRead = { assistant.speak(m.story, locale) { message("tts_unavailable") } }, onStopRead = { assistant.stop() }, onRemoveAttachment = { a -> deletion = "delete_attachment" to { vm.run { vm.repo.removeMedia(a) } } }) }
                            "albums" -> LazyColumn(Modifier.fillMaxSize().padding(horizontal = 24.dp), verticalArrangement = Arrangement.spacedBy(16.dp), contentPadding = PaddingValues(bottom = 32.dp)) {
                                item { Heading(tr("albums"), tr("no_albums")); Button(onClick = { if (albums.size >= 3 && !vm.billing.state.value.premium) { showPremium = true; message("album_limit") } else { albumDialog = Album(title = ""); albumName = "" } }) { Icon(Icons.Outlined.Add, null); Text(tr("new_album")) } }
                                if (albums.isEmpty()) item { EmptyState(tr("no_albums_body")) }
                                items(albums, key = { it.id }) { album -> OutlinedCard(onClick = { albumFilter = album.id; navigate("memories") }, modifier = Modifier.fillMaxWidth()) {
                                    Row(Modifier.padding(20.dp), verticalAlignment = Alignment.CenterVertically) {
                                        Icon(Icons.Outlined.CollectionsBookmark, null, Modifier.size(44.dp), tint = MaterialTheme.colorScheme.primary)
                                        Column(Modifier.weight(1f).padding(horizontal = 16.dp)) { Text(album.title, style = MaterialTheme.typography.titleLarge); val count = links.count { it.albumId == album.id }; Text(context.resources.getQuantityString(R.plurals.memory_count, count, count)) }
                                        IconButton(onClick = { albumDialog = album; albumName = album.title }) { Icon(Icons.Outlined.Edit, tr("edit")) }
                                        IconButton(onClick = { deletion = "delete_album" to { vm.run { vm.repo.dao.deleteAlbum(album.id) } } }) { Icon(Icons.Outlined.DeleteOutline, tr("delete")) }
                                    }
                                } }
                            }
                            "keepsakes" -> if (bookId != null && books.any { it.id == bookId }) BookEditor(vm, books.first { it.id == bookId }, pages.filter { it.bookId == bookId }, memories, media, onBack = { bookId = null }, premium = { showPremium = true }, onDelete = { b -> deletion = "delete_book" to { vm.run { vm.repo.dao.deleteBook(b.id); bookId = null } } }) else BooksScreen(vm, books, onOpen = { bookId = it })
                            "settings" -> SettingsScreen(vm, onPremium = { showPremium = true }, onDelete = { deletion = "delete_all" to { vm.run { vm.repo.clearAll() } } })
                            else -> {
                                val isTimeline = screen == "timeline"
                                var filtered = memories.filter { MemoryRules.matches(it, query) && (!favourites || it.favourite) && (year.isBlank() || it.date.startsWith(year)) && (albumFilter == null || links.any { link -> link.memoryId == it.id && link.albumId == albumFilter }) }
                                if (isTimeline) filtered = MemoryRules.timeline(filtered)
                                LazyColumn(Modifier.fillMaxSize().padding(horizontal = if (wide) 32.dp else 20.dp), verticalArrangement = Arrangement.spacedBy(16.dp), contentPadding = PaddingValues(bottom = 32.dp)) {
                                    item { if (isTimeline) Heading(tr("timeline")) else { Heading(tr("hero_title"), tr("hero_body")); Button(onClick = { newMemory() }, contentPadding = PaddingValues(horizontal = 24.dp, vertical = 14.dp)) { Icon(Icons.Outlined.Add, null); Spacer(Modifier.width(8.dp)); Text(tr("add_memory")) }; if (memories.isEmpty()) HeroArtwork() } }
                                    item { OutlinedTextField(query, { query = it }, label = { Text(tr("search")) }, leadingIcon = { Icon(Icons.Outlined.Search, null) }, modifier = Modifier.fillMaxWidth(), singleLine = true)
                                        Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                            Choice(!favourites, tr("all")) { favourites = false }; Choice(favourites, tr("favourites")) { favourites = true }; Choice(albumFilter == null, tr("album_filter") + ": " + tr("all")) { albumFilter = null }; albums.forEach { a -> Choice(albumFilter == a.id, a.title) { albumFilter = a.id } }
                                        }; if (isTimeline) Field("year_filter", year, { input -> val digits = MemoryRules.normaliseDateDigits(input); if (digits.length <= 4 && digits.all(Char::isDigit)) year = digits })
                                    }
                                    if (filtered.isEmpty()) item { EmptyState(if (memories.isEmpty()) tr("empty_title") else tr("no_results"), if (memories.isEmpty()) tr("empty_body") else null) }
                                    items(filtered, key = { it.id }) { m -> MemoryCard(m, media.firstOrNull { it.memoryId == m.id && it.kind == "photo" }, vm, { openMemory(m.id) }) }
                                    item {
                                        OutlinedCard(Modifier.fillMaxWidth()) {
                                            Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                                                Text(tr("prompt"), style = MaterialTheme.typography.titleLarge)
                                                val prompt = tr(preferences.purpose?.prompt ?: "prompt_childhood")
                                                Text(prompt)
                                                TextButton(onClick = { newMemory(prompt + "\n\n") }) { Text(tr("answer_prompt")) }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    if (!wide) ScrollableTabRow(selectedTabIndex = destinations.indexOfFirst { it.first == screen }.coerceAtLeast(0), edgePadding = 0.dp) { destinations.forEach { (key, icon) -> Tab(selected = screen == key, onClick = { navigate(key) }, text = { Text(tr(key)) }, icon = { Icon(icon, null) }) } }
                }
            }
        }
    }
    error?.let { key -> AlertDialog(onDismissRequest = { vm.error.value = null }, title = { Text(tr("app_name")) }, text = { Text(tr(key)) }, confirmButton = { TextButton(onClick = { vm.error.value = null }) { Text(tr("close")) } }) }
    deletion?.let { (key, action) -> AlertDialog(onDismissRequest = { deletion = null }, title = { Text(tr("delete")) }, text = { Text(tr(key)) }, confirmButton = { TextButton(onClick = { deletion = null; action() }) { Text(tr("delete"), color = MaterialTheme.colorScheme.error) } }, dismissButton = { TextButton(onClick = { deletion = null }) { Text(tr("cancel")) } }) }
    albumDialog?.let { album -> AlertDialog(onDismissRequest = { albumDialog = null }, title = { Text(tr("album_title")) }, text = { Field("title", albumName, { albumName = it.take(200) }) }, confirmButton = { TextButton(enabled = albumName.isNotBlank(), onClick = { vm.run { vm.repo.dao.save(album.copy(title = albumName.trim())) }; albumDialog = null }) { Text(tr("save")) } }, dismissButton = { TextButton(onClick = { albumDialog = null }) { Text(tr("cancel")) } }) }
    if (microphoneNotice) AlertDialog(onDismissRequest = { microphoneNotice = false }, title = { Text(tr("permission")) }, text = { Text(tr("microphone_notice")) }, confirmButton = { TextButton(onClick = { microphoneNotice = false; microphone.launch(Manifest.permission.RECORD_AUDIO) }) { Text(tr("confirm")) } }, dismissButton = { TextButton(onClick = { microphoneNotice = false }) { Text(tr("cancel")) } })
    if (showVoice) VoiceDialog(assistant, onDismiss = { assistant.stop(); showVoice = false }, onCommand = { showVoice = false; command(it) }, onError = { message(it) })
    if (showPremium) PremiumDialog(vm) { showPremium = false }
}
@Composable fun HeroArtwork() {
    val context = LocalContext.current; val id = context.resources.getIdentifier("hero_book", "drawable", context.packageName)
    if (id != 0) Image(painterResource(id), null, Modifier.fillMaxWidth().heightIn(max = 230.dp).padding(vertical = 16.dp))
    else Image(painterResource(R.drawable.ic_book), null, Modifier.fillMaxWidth().height(140.dp).padding(24.dp))
}
@Composable fun EmptyState(title: String, body: String? = null) {
    OutlinedCard(Modifier.fillMaxWidth()) { Column(Modifier.fillMaxWidth().padding(28.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(12.dp)) { Icon(Icons.Outlined.AutoStories, null, Modifier.size(48.dp), tint = MaterialTheme.colorScheme.secondary); Text(title, style = MaterialTheme.typography.titleLarge); body?.let { Text(it) } } }
}
