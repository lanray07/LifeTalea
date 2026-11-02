package com.lifetalea.app.data
import android.content.Context
import androidx.datastore.preferences.core.*
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.map
private val Context.settings by preferencesDataStore("settings")
data class Preferences(val onboarded: Boolean = false, val theme: String = "system", val spoken: Boolean = false)
class Settings(private val context: Context) {
    val flow = context.settings.data.map { Preferences(it[booleanPreferencesKey("onboarded")] ?: false, it[stringPreferencesKey("theme")] ?: "system", it[booleanPreferencesKey("spoken")] ?: false) }
    suspend fun onboard() { context.settings.edit { it[booleanPreferencesKey("onboarded")] = true } }
    suspend fun theme(value: String) { context.settings.edit { it[stringPreferencesKey("theme")] = value } }
    suspend fun spoken(value: Boolean) { context.settings.edit { it[booleanPreferencesKey("spoken")] = value } }
}
