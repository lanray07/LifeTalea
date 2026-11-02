package com.lifetalea.app.ui
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.lifetalea.app.R

val Forest = Color(0xFF38584A)
val Gold = Color(0xFF9B7438)
val Ivory = Color(0xFFFAF7F1)
@Composable fun tr(key: String): String {
    val context = LocalContext.current
    val id = context.resources.getIdentifier(key, "string", context.packageName)
    return context.getString(if (id == 0) R.string.operation_failed else id)
}
@Composable fun LifeTheme(theme: String, content: @Composable () -> Unit) {
    val dark = theme == "dark" || (theme == "system" && isSystemInDarkTheme())
    val colors = if (dark) darkColorScheme(primary = Color(0xFFAFD0BC), background = Color(0xFF1D2621), surface = Color(0xFF26322C), secondary = Color(0xFFE3C28E), primaryContainer = Color(0xFF304C3C), onPrimaryContainer = Color(0xFFE0EADF), secondaryContainer = Color(0xFF514029), tertiaryContainer = Color(0xFF5D3439))
        else lightColorScheme(primary = Forest, background = Ivory, surface = Color(0xFFFFFCF7), secondary = Gold, surfaceVariant = Color(0xFFEEE8DE), onBackground = Color(0xFF302F2D), onSurface = Color(0xFF302F2D), primaryContainer = Color(0xFFDDE7DD), onPrimaryContainer = Forest, secondaryContainer = Color(0xFFF1E3CA), onSecondaryContainer = Color(0xFF4B3820), tertiaryContainer = Color(0xFFF0DDDA), onTertiaryContainer = Color(0xFF573336), outline = Color(0xFF7C8277), outlineVariant = Color(0xFFC9C4B9))
    MaterialTheme(colorScheme = colors, typography = Typography(
        displaySmall = MaterialTheme.typography.displaySmall.copy(fontFamily = FontFamily.Serif, fontSize = 36.sp),
        headlineLarge = MaterialTheme.typography.headlineLarge.copy(fontFamily = FontFamily.Serif),
        headlineMedium = MaterialTheme.typography.headlineMedium.copy(fontFamily = FontFamily.Serif),
        titleLarge = MaterialTheme.typography.titleLarge.copy(fontFamily = FontFamily.Serif)
    ), shapes = Shapes(medium = RoundedCornerShape(16.dp), large = RoundedCornerShape(24.dp)), content = content)
}
@Composable fun Heading(title: String, subtitle: String? = null) {
    Column(Modifier.fillMaxWidth().padding(vertical = 12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(title, style = MaterialTheme.typography.headlineLarge)
        subtitle?.let { Text(it, style = MaterialTheme.typography.bodyLarge, color = MaterialTheme.colorScheme.onSurfaceVariant) }
    }
}
@Composable fun Field(key: String, value: String, change: (String) -> Unit, lines: Int = 1) {
    OutlinedTextField(value, change, label = { Text(tr(key)) }, modifier = Modifier.fillMaxWidth(), minLines = lines, singleLine = lines == 1)
}
@Composable fun Choice(selected: Boolean, text: String, click: () -> Unit) { FilterChip(selected, click, label = { Text(text) }, modifier = Modifier.heightIn(min = 48.dp)) }
