package com.lifetalea.app
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.lifetalea.app.ui.*
class MainActivity : AppCompatActivity() {
    private val model: LibraryViewModel by viewModels()
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        model.billing.initialize()
        setContent {
            val preferences = model.preferences.collectAsStateWithLifecycle().value
            LifeTheme(preferences.theme) { LifeApp(model) }
        }
    }
    override fun onResume() { super.onResume(); model.billing.refresh() }
    override fun onStop() { model.stopRecording(); super.onStop() }
}
