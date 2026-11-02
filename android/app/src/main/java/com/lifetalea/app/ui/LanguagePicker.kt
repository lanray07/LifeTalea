package com.lifetalea.app.ui

import androidx.appcompat.app.AppCompatDelegate
import androidx.core.os.LocaleListCompat
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import com.lifetalea.app.R
import java.util.Locale

/** Uses only locales included in this build's resources. Release excludes unreviewed drafts. */
@Composable fun LanguagePicker() {
    val context = LocalContext.current
    val configuration = LocalConfiguration.current
    val languages = context.resources.getStringArray(R.array.supported_locale_tags).toList()
    var open by remember { mutableStateOf(false) }
    val explicit = AppCompatDelegate.getApplicationLocales().toLanguageTags()
    val current = configuration.locales[0]
    fun choose(tag: String) {
        open = false
        AppCompatDelegate.setApplicationLocales(LocaleListCompat.forLanguageTags(tag))
    }
    OutlinedButton(onClick = { open = true }, modifier = Modifier.fillMaxWidth().testTag("language_picker")) {
        Text(if (explicit.isEmpty()) tr("device_language") else current.getDisplayName(current))
    }
    if (open) AlertDialog(
        onDismissRequest = { open = false },
        title = { Text(tr("language")) },
        text = {
            LazyColumn(Modifier.fillMaxWidth().heightIn(max = 400.dp).testTag("language_options")) {
                item {
                    TextButton(onClick = { choose("") }, modifier = Modifier.fillMaxWidth()) {
                        Text(tr("device_language"))
                    }
                }
                items(languages, key = { it }) { tag ->
                    val locale = Locale.forLanguageTag(tag)
                    TextButton(onClick = { choose(tag) }, modifier = Modifier.fillMaxWidth().testTag("language_$tag")) {
                        Text(locale.getDisplayName(locale))
                    }
                }
            }
        },
        confirmButton = { TextButton(onClick = { open = false }) { Text(tr("close")) } }
    )
}
