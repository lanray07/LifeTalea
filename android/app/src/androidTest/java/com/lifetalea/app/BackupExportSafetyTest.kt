package com.lifetalea.app

import android.app.Application
import android.net.Uri
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.ViewModelStore
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.lifetalea.app.data.ArchiveCrypto
import java.io.File
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class BackupExportSafetyTest {
    @Test fun returnedDestinationRequiresAnExplicitPendingExport() {
        val instrument = InstrumentationRegistry.getInstrumentation()
        val app = instrument.targetContext.applicationContext as Application
        val store = ViewModelStore()
        val dir = File(app.cacheDir, "backup-result-${java.util.UUID.randomUUID()}").apply { mkdir() }
        val encrypted = File(dir, "encrypted.lta")
        val orphan = File(dir, "orphan.lta")
        val plain = File(dir, "plain.lta")
        try {
            lateinit var model: LibraryViewModel
            instrument.runOnMainSync {
                model = ViewModelProvider(store, ViewModelProvider.AndroidViewModelFactory.getInstance(app))[LibraryViewModel::class.java]
                model.finishBackup(Uri.fromFile(orphan))
                assertEquals("operation_failed", model.error.value)
                assertFalse(orphan.exists())
                model.error.value = null
                model.billing.state.value = model.billing.state.value.copy(premium = true)
                assertTrue(model.prepareBackup(false, false, "fictional-qa-passphrase"))
                assertFalse(model.prepareBackup(false, false, ""))
                model.finishBackup(Uri.fromFile(encrypted))
            }
            runBlocking { withTimeout(15_000) { model.error.first { it == "backup_saved" } } }
            assertTrue(ArchiveCrypto.encrypted(encrypted.readBytes()))

            instrument.runOnMainSync {
                model.error.value = null
                assertTrue(model.prepareBackup(false, false, ""))
                model.finishBackup(Uri.fromFile(plain))
            }
            runBlocking { withTimeout(15_000) { model.error.first { it == "backup_saved" } } }
            assertFalse(ArchiveCrypto.encrypted(plain.readBytes()))
        } finally {
            instrument.runOnMainSync { store.clear() }
            listOf(encrypted, orphan, plain).forEach { it.delete() }
            dir.delete()
        }
    }
}
