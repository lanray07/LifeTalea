package com.lifetalea.app.ui
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.room.withTransaction
import coil.compose.AsyncImage
import com.lifetalea.app.LibraryViewModel
import com.lifetalea.app.data.*
import com.lifetalea.app.features.KeepsakePdf
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

@Composable fun BooksScreen(vm: LibraryViewModel, books: List<Scrapbook>, onOpen: (String) -> Unit) {
    var create by remember { mutableStateOf(false) }; var title by rememberSaveable { mutableStateOf("") }
    LazyColumn(Modifier.fillMaxSize().padding(horizontal = 24.dp), verticalArrangement = Arrangement.spacedBy(16.dp), contentPadding = PaddingValues(bottom = 24.dp)) {
        item { Heading(tr("keepsakes"), tr("no_books")); Button(onClick = { create = true }) { Icon(Icons.Outlined.Add, null); Text(tr("new_book")) } }
        if (books.isEmpty()) item { EmptyState(tr("no_books_body")) }
        items(books, key = { it.id }) { book -> OutlinedCard(onClick = { onOpen(book.id) }, modifier = Modifier.fillMaxWidth()) { Row(Modifier.padding(24.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(20.dp)) { Icon(Icons.Outlined.MenuBook, null, Modifier.size(48.dp)); Column { Text(book.title, style = MaterialTheme.typography.titleLarge); Text(tr("draft")) } } } }
    }
    if (create) AlertDialog(onDismissRequest = { create = false }, title = { Text(tr("new_book")) }, text = { Field("book_title", title, { title = it.take(200) }) }, confirmButton = { TextButton(enabled = title.isNotBlank(), onClick = { val book = Scrapbook(title = title.trim()); vm.run { vm.repo.dao.save(book); onOpen(book.id) }; create = false; title = "" }) { Text(tr("save")) } }, dismissButton = { TextButton(onClick = { create = false }) { Text(tr("cancel")) } })
}
@Composable fun BookEditor(vm: LibraryViewModel, book: Scrapbook, pages: List<BookPage>, memories: List<Memory>, media: List<Attachment>, onBack: () -> Unit, premium: () -> Unit, onDelete: (Scrapbook) -> Unit) {
    val context = LocalContext.current
    var add by remember { mutableStateOf(false) }; var options by remember { mutableStateOf(false) }
    var title by rememberSaveable(book.id) { mutableStateOf(book.title) }
    var includeLocation by rememberSaveable { mutableStateOf(false) }; var includeTranscript by rememberSaveable { mutableStateOf(false) }; var letter by rememberSaveable { mutableStateOf(false) }
    var preview by rememberSaveable { mutableStateOf(false) }
    val export = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("application/pdf")) { uri -> if (uri != null) vm.run {
        withContext(Dispatchers.IO) {
            val selections = pages.sortedBy { it.position }.mapNotNull { p -> memories.find { it.id == p.memoryId }?.let { it.copy(story = it.story + if (p.caption.isNotBlank()) "\n\n${p.caption}" else "") } }
            context.contentResolver.openOutputStream(uri)?.use { KeepsakePdf(vm.repo).write(title, selections, media, it, includeLocation, includeTranscript, letter) } ?: error("No output")
        }; vm.error.value = "pdf_saved"
    } }
    fun move(page: BookPage, offset: Int) { val ordered = pages.sortedBy { it.position }; val index = ordered.indexOf(page); val target = ordered.getOrNull(index + offset) ?: return; vm.run { vm.repo.db.withTransaction { vm.repo.dao.save(page.copy(position = target.position)); vm.repo.dao.save(target.copy(position = page.position)) } } }
    LazyColumn(Modifier.fillMaxSize().padding(horizontal = 24.dp), verticalArrangement = Arrangement.spacedBy(20.dp), contentPadding = PaddingValues(bottom = 32.dp)) {
        item {
            TextButton(onClick = onBack) { Icon(Icons.Outlined.ArrowBack, null); Text(tr("back")) }
            Heading(book.title)
            if (!preview) { Field("book_title", title, { title = it.take(200) }); TextButton(enabled = title.isNotBlank(), onClick = { vm.run { vm.repo.dao.save(book.copy(title = title.trim())) } }) { Text(tr("save")) }
                Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) { listOf("forest", "rose", "paper").forEach { t -> Choice(book.theme == t, tr(t)) { vm.run { vm.repo.dao.save(book.copy(theme = t)) } } } }
            }
            Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) { OutlinedButton(onClick = { preview = !preview }) { Text(tr(if (preview) "edit" else "preview")) }; Button(onClick = { add = true }) { Text(tr("add_page")) }; TextButton(enabled = pages.any { p -> memories.any { it.id == p.memoryId } }, onClick = { if (vm.billing.state.value.premium) options = true else premium() }) { Text(tr("export_pdf")) } }
        }
        if (pages.isEmpty()) item { EmptyState(tr("empty_book")) }
        items(pages.sortedBy { it.position }, key = { it.id }) { page ->
            val memory = memories.find { it.id == page.memoryId }
            val photo = media.firstOrNull { it.memoryId == page.memoryId && it.kind == "photo" }
            var caption by rememberSaveable(page.id) { mutableStateOf(page.caption) }
            OutlinedCard(Modifier.fillMaxWidth(), colors = CardDefaults.outlinedCardColors(containerColor = if (book.theme == "rose") MaterialTheme.colorScheme.tertiaryContainer else MaterialTheme.colorScheme.surface)) {
                Column(Modifier.padding(24.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                    if (memory == null) Text(tr("missing_memory")) else {
                        Text(memory.title, style = MaterialTheme.typography.headlineMedium)
                        photo?.let { AsyncImage(vm.repo.file(it.filename), tr("photos"), Modifier.fillMaxWidth().heightIn(max = 300.dp), contentScale = if (page.layout == "photo") ContentScale.Crop else ContentScale.Fit) }
                        Text(memory.story)
                    }
                    if (preview) { if (page.caption.isNotBlank()) Text(page.caption) }
                    else {
                        Field("caption", caption, { caption = it.take(4000) }, 2)
                        TextButton(onClick = { vm.run { vm.repo.dao.save(page.copy(caption = caption)) } }) { Text(tr("save")) }
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { listOf("story", "photo").forEach { layout -> Choice(page.layout == layout, tr(layout + "_layout")) { vm.run { vm.repo.dao.save(page.copy(layout = layout)) } } } }
                        Row { IconButton(onClick = { move(page, -1) }, enabled = page != pages.firstOrNull()) { Icon(Icons.Outlined.ArrowUpward, tr("move_up")) }; IconButton(onClick = { move(page, 1) }, enabled = page != pages.lastOrNull()) { Icon(Icons.Outlined.ArrowDownward, tr("move_down")) }; TextButton(onClick = { vm.run { vm.repo.dao.deletePage(page.id) } }) { Text(tr("remove_page")) } }
                    }
                }
            }
        }
        item { TextButton(onClick = { onDelete(book) }) { Text(tr("delete"), color = MaterialTheme.colorScheme.error) } }
    }
    if (add) AlertDialog(onDismissRequest = { add = false }, title = { Text(tr("new_page")) }, text = { Column(Modifier.verticalScroll(rememberScrollState())) { memories.forEach { m -> TextButton(onClick = { vm.run { vm.repo.dao.save(BookPage(bookId = book.id, memoryId = m.id, position = (pages.maxOfOrNull { it.position } ?: -1) + 1)) }; add = false }) { Text(m.title) } } } }, confirmButton = { TextButton(onClick = { add = false }) { Text(tr("close")) } })
    if (options) AlertDialog(onDismissRequest = { options = false }, title = { Text(tr("pdf_options")) }, text = { Column { Text(tr("pdf_note")); Toggle("include_location", includeLocation) { includeLocation = it }; Toggle("include_transcript", includeTranscript) { includeTranscript = it }; Row { Choice(!letter, "A4") { letter = false }; Spacer(Modifier.width(8.dp)); Choice(letter, "Letter") { letter = true } } } }, confirmButton = { TextButton(onClick = { options = false; export.launch("LifeTalea-keepsake.pdf") }) { Text(tr("export")) } }, dismissButton = { TextButton(onClick = { options = false }) { Text(tr("cancel")) } })
}
