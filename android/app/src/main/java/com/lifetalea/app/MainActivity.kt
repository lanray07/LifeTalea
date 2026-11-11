package com.lifetalea.app
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.lifetalea.app.ui.*
import android.app.KeyguardManager
import android.content.Context
import android.content.SharedPreferences
import android.view.WindowManager
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveableStateHolder
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
import androidx.compose.ui.unit.dp
class MainActivity : AppCompatActivity() {
    private val model: LibraryViewModel by viewModels()
    var appLockEnabled by mutableStateOf(false)
        private set
    private var unlocked by mutableStateOf(false)
    private var authenticating = false
    private var requestedLock: Boolean? = null
    private var credentialRevision: Long? = null
    private var lockRevision = 0L
    private val lockPreferences by lazy { getSharedPreferences("app_lock", Context.MODE_PRIVATE) }
    private val lockListener = SharedPreferences.OnSharedPreferenceChangeListener { _, key ->
        if (key == "enabled" || key == "revision" || key == null) syncLock()
    }
    private val backupDestination = registerForActivityResult(ActivityResultContracts.CreateDocument("application/octet-stream")) {
        model.finishBackup(it)
    }

    fun requestBackup(photos: Boolean, audio: Boolean, password: String): Boolean {
        if (!model.prepareBackup(photos, audio, password)) return false
        return runCatching { backupDestination.launch("LifeTalea-backup.lta") }.fold(
            onSuccess = { true },
            onFailure = { model.finishBackup(null); false }
        )
    }
    private val credential = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        authenticating = false
        val requested = requestedLock
        requestedLock = null
        val revision = credentialRevision
        credentialRevision = null
        syncLock()
        if (result.resultCode == RESULT_OK && revision == lockRevision) {
            if (requested != null) {
                if (lockPreferences.edit().putBoolean("enabled", requested).putLong("revision", lockRevision + 1).commit()) {
                    syncLock()
                } else { model.error.value = "operation_failed"; return@registerForActivityResult }
            }
            unlocked = true
        }
    }
    private fun secureWindow() {
        if (appLockEnabled) window.addFlags(WindowManager.LayoutParams.FLAG_SECURE)
        else window.clearFlags(WindowManager.LayoutParams.FLAG_SECURE)
    }
    private fun syncLock() {
        val enabled = lockPreferences.getBoolean("enabled", false)
        val revision = lockPreferences.getLong("revision", 0)
        if (enabled != appLockEnabled || revision != lockRevision) {
            unlocked = false
            appLockEnabled = enabled
            lockRevision = revision
        }
        secureWindow()
    }
    @Suppress("DEPRECATION") // Available on every supported Fire API; credentials stay in the OS UI.
    fun authenticateLock(enable: Boolean? = null) {
        if (authenticating) return
        val manager = getSystemService(KeyguardManager::class.java)
        val intent = if (manager.isDeviceSecure) manager.createConfirmDeviceCredentialIntent(getString(R.string.app_lock), getString(R.string.app_lock_notice)) else null
        if (intent == null) { model.error.value = "app_lock_notice"; return }
        requestedLock = enable
        syncLock()
        credentialRevision = lockRevision
        authenticating = true
        runCatching { credential.launch(intent) }.onFailure {
            authenticating = false; requestedLock = null; credentialRevision = null; model.error.value = "app_lock_notice"
        }
    }
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (savedInstanceState?.containsKey("credentialRevision") == true) {
            credentialRevision = savedInstanceState.getLong("credentialRevision")
            requestedLock = if (savedInstanceState.containsKey("requestedLock")) savedInstanceState.getBoolean("requestedLock") else null
            authenticating = true
        }
        lockPreferences.registerOnSharedPreferenceChangeListener(lockListener)
        syncLock()
        model.billing.initialize()
        com.lifetalea.app.features.StoryReminders(this).reschedule()
        setContent {
            val journalState = rememberSaveableStateHolder()
            val preferences = model.preferences.collectAsStateWithLifecycle().value
            val billing = model.billing.state.collectAsStateWithLifecycle().value
            LifeTheme(preferences.theme, if (billing.premium) preferences.palette else "forest") {
                if (appLockEnabled && !unlocked) Surface(Modifier.fillMaxSize()) {
                    Column(Modifier.fillMaxSize().padding(32.dp), verticalArrangement = Arrangement.spacedBy(20.dp, Alignment.CenterVertically), horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(getString(R.string.app_name), style = MaterialTheme.typography.headlineLarge)
                        Text(getString(R.string.app_lock_notice))
                        Button(onClick = { authenticateLock() }) { Text(getString(R.string.unlock)) }
                    }
                } else journalState.SaveableStateProvider("journal") { LifeApp(model) }
            }
        }
    }
    override fun onResume() { super.onResume(); syncLock(); model.billing.refresh() }
    override fun onSaveInstanceState(outState: Bundle) {
        credentialRevision?.let { revision ->
            outState.putLong("credentialRevision", revision)
            requestedLock?.let { outState.putBoolean("requestedLock", it) }
        }
        super.onSaveInstanceState(outState)
    }
    override fun onDestroy() {
        lockPreferences.unregisterOnSharedPreferenceChangeListener(lockListener)
        super.onDestroy()
    }
    override fun onStop() {
        // Backgrounding during a credential prompt must not preserve an old unlock.
        // Only a fresh successful OS result may open the journal again.
        if (appLockEnabled) unlocked = false
        model.stopRecording(); super.onStop()
    }
}
