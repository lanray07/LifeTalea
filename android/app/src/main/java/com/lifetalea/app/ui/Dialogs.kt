package com.lifetalea.app.ui
import android.Manifest
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.lifetalea.app.LibraryViewModel
import com.lifetalea.app.voice.VoiceAssistant
import java.util.Locale

@Composable fun Onboarding(onDone: () -> Unit) {
    var purpose by rememberSaveable { mutableStateOf("family") }
    Surface(Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
        Column(Modifier.fillMaxSize().statusBarsPadding().navigationBarsPadding().verticalScroll(rememberScrollState()).padding(32.dp), verticalArrangement = Arrangement.spacedBy(20.dp)) {
            Text("LifeTalea", style = MaterialTheme.typography.headlineMedium)
            HeroArtwork(); Heading(tr("welcome"), tr("welcome_body"))
            Text(tr("language"), style = MaterialTheme.typography.titleLarge); Text(tr("language_note"))
            LanguagePicker()
            Text(tr("purpose"), style = MaterialTheme.typography.titleLarge)
            listOf("family", "personal", "childhood", "history", "travel", "legacy").forEach { key -> Row(verticalAlignment = Alignment.CenterVertically) { RadioButton(purpose == key, { purpose = key }); Text(tr(key)) } }
            Button(onClick = onDone) { Text(tr("get_started")) }; TextButton(onClick = onDone) { Text(tr("skip")) }
        }
    }
}
@Composable fun VoiceDialog(assistant: VoiceAssistant, onDismiss: () -> Unit, onCommand: (String) -> Unit, onError: (String) -> Unit) {
    var command by rememberSaveable { mutableStateOf("") }; var listening by remember { mutableStateOf(false) }
    var recognised by remember { mutableStateOf("") }
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { allowed ->
        if (!allowed) { listening = false; onError("microphone_denied") } else { listening = true; assistant.listen(Locale.ENGLISH, { recognised = it; command = it; listening = false }, { listening = false; onError("voice_error") }) }
    }
    AlertDialog(onDismissRequest = onDismiss, title = { Text(tr("voice_commands")) }, text = {
        Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            Text(tr("voice_notice")); Text(tr("unknown_command"))
            if (!assistant.available()) Text(tr("voice_unavailable"))
            Button(enabled = assistant.available() && !listening, onClick = { launcher.launch(Manifest.permission.RECORD_AUDIO) }) { Text(tr(if (listening) "listening" else "listen")) }
            if (recognised.isNotBlank()) Text(recognised)
            Field("command", command, { command = it })
        }
    }, confirmButton = { TextButton(enabled = command.isNotBlank(), onClick = { onCommand(command) }) { Text(tr("run_command")) } }, dismissButton = { TextButton(onClick = onDismiss) { Text(tr("close")) } })
}
@Composable fun PremiumDialog(vm: LibraryViewModel, onClose: () -> Unit) {
    val state by vm.billing.state.collectAsStateWithLifecycle()
    AlertDialog(onDismissRequest = onClose, title = { Text(tr("premium")) }, text = {
        Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            Text(tr("premium_body")); Text(tr("free_limits")); Text(tr(state.message))
            state.price?.let { Text(it + " · " + tr("one_time"), style = MaterialTheme.typography.titleLarge) }
            Button(enabled = state.available && !state.premium, onClick = { vm.billing.purchase() }) { Text(tr("upgrade")) }
            TextButton(onClick = { vm.billing.restore() }) { Text(tr("restore_purchases")) }; TextButton(onClick = { vm.billing.refresh() }) { Text(tr("refresh")) }
        }
    }, confirmButton = { TextButton(onClick = onClose) { Text(tr("close")) } })
}
