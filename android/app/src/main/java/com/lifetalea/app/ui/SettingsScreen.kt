package com.lifetalea.app.ui
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatDelegate
import androidx.core.os.LocaleListCompat
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.lifetalea.app.LibraryViewModel
import com.lifetalea.app.data.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

@Composable fun Toggle(key: String, checked: Boolean, change: (Boolean) -> Unit) { Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) { Text(tr(key), Modifier.weight(1f)); Switch(checked, change) } }
@Composable fun SettingsScreen(vm: LibraryViewModel, onPremium: () -> Unit, onDelete: () -> Unit) {
    val context = LocalContext.current
    val preferences by vm.preferences.collectAsStateWithLifecycle()
    val busy by vm.busy.collectAsStateWithLifecycle()
    var includePhotos by rememberSaveable { mutableStateOf(false) }; var includeAudio by rememberSaveable { mutableStateOf(false) }
    var password by remember { mutableStateOf("") }
    var archive by remember { mutableStateOf<ValidatedArchive?>(null) }
    val backup = remember { BackupService(vm.repo) }
    val create = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("application/octet-stream")) { uri -> if (uri != null) vm.run {
        val bytes = backup.create(includePhotos, includeAudio, password.toCharArray())
        withContext(Dispatchers.IO) { context.contentResolver.openOutputStream(uri)?.use { it.write(bytes) } ?: error("No output") }; password = ""; vm.error.value = "backup_saved"
    } }
    val restore = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri -> if (uri != null) vm.run { archive = backup.validate(context.contentResolver.openInputStream(uri) ?: error("No input"), password.toCharArray()); password = "" } }
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp), verticalArrangement = Arrangement.spacedBy(20.dp)) {
        Heading(tr("settings"))
        Text(tr("appearance"), style = MaterialTheme.typography.titleLarge)
        Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) { listOf("system", "light", "dark").forEach { theme -> Choice(preferences.theme == theme, tr(theme)) { vm.run { vm.settings.theme(theme) } } } }
        Text(tr("language"), style = MaterialTheme.typography.titleLarge); Text(tr("language_note"))
        Row { TextButton(onClick = { AppCompatDelegate.setApplicationLocales(LocaleListCompat.getEmptyLocaleList()) }) { Text(tr("device_language")) }; TextButton(onClick = { AppCompatDelegate.setApplicationLocales(LocaleListCompat.forLanguageTags("en-GB")) }) { Text("English") } }
        Toggle("spoken_feedback", preferences.spoken) { vm.run { vm.settings.spoken(it) } }
        HorizontalDivider(); Text(tr("privacy"), style = MaterialTheme.typography.titleLarge); Text(tr("privacy_body"))
        HorizontalDivider(); Text(tr("backup"), style = MaterialTheme.typography.titleLarge); Text(tr("backup_notice"))
        Toggle("include_photos", includePhotos) { includePhotos = it }; Toggle("include_audio", includeAudio) { includeAudio = it }
        OutlinedTextField(password, { password = it.take(200) }, label = { Text(tr("password")) }, supportingText = { Text(tr("password_hint")) }, visualTransformation = PasswordVisualTransformation(), modifier = Modifier.fillMaxWidth(), singleLine = true)
        Button(enabled = !busy && (password.isEmpty() || password.length >= 10), onClick = { if (password.isNotEmpty() && !vm.billing.state.value.premium) onPremium() else create.launch("LifeTalea-backup.lta") }) { Text(tr("create_backup")) }
        Text(tr("restore_notice")); OutlinedButton(enabled = !busy, onClick = { restore.launch(arrayOf("*/*")) }) { Text(tr("restore_backup")) }
        HorizontalDivider(); TextButton(onClick = onPremium) { Text(tr("premium")) }; TextButton(onClick = { vm.billing.restore() }) { Text(tr("restore_purchases")) }
        Text(tr("support"), style = MaterialTheme.typography.titleLarge); Text(tr("support_body"))
        TextButton(enabled = !busy, onClick = onDelete) { Text(tr("delete_data"), color = MaterialTheme.colorScheme.error) }
    }
    archive?.let { a -> AlertDialog(onDismissRequest = { archive = null }, title = { Text(tr("restore_preview")) }, text = { val p = a.preview; Text(context.getString(com.lifetalea.app.R.string.restore_counts, p.memories, p.albums, p.media, p.books, p.duplicates)) }, confirmButton = { TextButton(enabled = !busy, onClick = { vm.run { backup.restore(a); archive = null; vm.error.value = "restore_complete" } }) { Text(tr("restore_now")) } }, dismissButton = { TextButton(onClick = { archive = null }) { Text(tr("cancel")) } }) }
}
