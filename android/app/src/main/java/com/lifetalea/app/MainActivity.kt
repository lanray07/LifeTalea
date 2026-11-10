package com.lifetalea.app
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.lifetalea.app.ui.*
import android.app.KeyguardManager
import android.content.Context
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
    private val lockPreferences by lazy { getSharedPreferences("app_lock", Context.MODE_PRIVATE) }
    private val credential = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        authenticating = false
        val requested = requestedLock
        requestedLock = null
        if (result.resultCode == RESULT_OK) {
            if (requested != null) {
                if (lockPreferences.edit().putBoolean("enabled", requested).commit()) {
                    appLockEnabled = requested
                    secureWindow()
                } else { model.error.value = "operation_failed"; return@registerForActivityResult }
            }
            unlocked = true
        }
    }
    private fun secureWindow() {
        if (appLockEnabled) window.addFlags(WindowManager.LayoutParams.FLAG_SECURE)
        else window.clearFlags(WindowManager.LayoutParams.FLAG_SECURE)
    }
    @Suppress("DEPRECATION") // Available on every supported Fire API; credentials stay in the OS UI.
    fun authenticateLock(enable: Boolean? = null) {
        if (authenticating) return
        val manager = getSystemService(KeyguardManager::class.java)
        val intent = if (manager.isDeviceSecure) manager.createConfirmDeviceCredentialIntent(getString(R.string.app_lock), getString(R.string.app_lock_notice)) else null
        if (intent == null) { model.error.value = "app_lock_notice"; return }
        requestedLock = enable
        authenticating = true
        runCatching { credential.launch(intent) }.onFailure {
            authenticating = false; requestedLock = null; model.error.value = "app_lock_notice"
        }
    }
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        appLockEnabled = lockPreferences.getBoolean("enabled", false)
        secureWindow()
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
    override fun onResume() { super.onResume(); model.billing.refresh() }
    override fun onStop() {
        // Backgrounding during a credential prompt must not preserve an old unlock.
        // Only a fresh successful OS result may open the journal again.
        if (appLockEnabled) unlocked = false
        model.stopRecording(); super.onStop()
    }
}
