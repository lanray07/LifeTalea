package com.lifetalea.app.data
import android.content.Context
import androidx.datastore.preferences.core.*
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.map
private val Context.settings by preferencesDataStore("settings")
enum class StoryPurpose(val label: String, val prompt: String) {
    FAMILY("family", "prompt_tradition"),
    PERSONAL("personal", "prompt_lesson"),
    CHILDHOOD("childhood", "prompt_childhood"),
    HISTORY("history", "prompt_tradition"),
    TRAVEL("travel", "prompt_lesson"),
    LEGACY("legacy", "prompt_recipe");

    companion object {
        fun fromLabel(label: String?): StoryPurpose? = entries.firstOrNull { it.label == label }
    }
}

data class Preferences(
    val onboarded: Boolean = false,
    val theme: String = "system",
    val spoken: Boolean = false,
    val palette: String = "forest",
    val sort: String = "recent",
    val purpose: StoryPurpose? = null,
)
class Settings(private val context: Context) {
    private val purposeKey = stringPreferencesKey("story_purpose")
    val flow = context.settings.data.map {
        Preferences(
            onboarded = it[booleanPreferencesKey("onboarded")] ?: false,
            theme = it[stringPreferencesKey("theme")] ?: "system",
            spoken = it[booleanPreferencesKey("spoken")] ?: false,
            palette = it[stringPreferencesKey("palette")] ?: "forest",
            sort = it[stringPreferencesKey("sort")] ?: "recent",
            purpose = StoryPurpose.fromLabel(it[purposeKey]),
        )
    }
    suspend fun onboard(purpose: StoryPurpose?) {
        context.settings.edit {
            it[booleanPreferencesKey("onboarded")] = true
            if (purpose == null) it.remove(purposeKey) else it[purposeKey] = purpose.label
        }
    }
    suspend fun theme(value: String) { context.settings.edit { it[stringPreferencesKey("theme")] = value } }
    suspend fun spoken(value: Boolean) { context.settings.edit { it[booleanPreferencesKey("spoken")] = value } }
    suspend fun palette(value: String) { require(value in listOf("forest", "rose", "paper")); context.settings.edit { it[stringPreferencesKey("palette")] = value } }
    suspend fun sort(value: String) { require(value in listOf("recent", "date", "title")); context.settings.edit { it[stringPreferencesKey("sort")] = value } }
}
