package com.lifetalea.app

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.graphics.asAndroidBitmap
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.lifetalea.app.data.*
import kotlinx.coroutines.runBlocking
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import android.graphics.Bitmap

@RunWith(AndroidJUnit4::class)
class ReleaseGapsTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private val context get() = InstrumentationRegistry.getInstrumentation().targetContext
    private fun ready() {
        compose.waitUntil(20000) { compose.onAllNodesWithText("Skip for now").fetchSemanticsNodes().isNotEmpty() || compose.onAllNodesWithText("Add a memory").fetchSemanticsNodes().isNotEmpty() }
        if (compose.onAllNodesWithText("Skip for now").fetchSemanticsNodes().isNotEmpty()) compose.onNodeWithText("Skip for now").performScrollTo().performClick()
        compose.waitUntil(15000) { compose.onAllNodesWithText("Add a memory").fetchSemanticsNodes().isNotEmpty() }
    }
    private fun capture(name: String) {
        val out = File(context.filesDir,"test-evidence/release-gaps").apply { mkdirs() }
        compose.onRoot().captureToImage().asAndroidBitmap().let { b -> out.resolve("$name.png").outputStream().use { b.compress(Bitmap.CompressFormat.PNG,100,it) } }
    }
    private fun reveal(text: String) {
        compose.onNode(hasScrollToIndexAction()).performScrollToNode(hasText(text))
        compose.onNodeWithText(text).assertIsDisplayed()
    }
    @Test fun mediaTranscriptYearFiltersAndClearWorkTogether() {
        val repo = LibraryRepository(context,LifeDatabase.open(context))
        val audio = Memory(title="QA audio orchard",date="1994",precision="YEAR",transcript="Apple tree")
        val plain = Memory(title="QA written orchard",date="2001",precision="YEAR")
        runBlocking {
            repo.dao.save(audio); repo.dao.save(plain)
            repo.dao.save(Attachment(memoryId=audio.id,filename="qa-empty.m4a",kind="audio",name="Fictional metadata only"))
        }
        try {
            ready()
            compose.onNodeWithText("Search filters").performScrollTo().performClick()
            compose.onNodeWithText("With audio").performScrollTo().performClick()
            compose.onNodeWithText("QA written orchard").assertDoesNotExist()
            reveal("QA audio orchard")
            compose.onNodeWithText("Filter by year").performScrollTo().performTextInput("2001")
            compose.onNodeWithText("QA audio orchard").assertDoesNotExist()
            reveal("No memories found. Try another search or filter.")
            compose.onNodeWithText("Clear filters").performScrollTo().performClick()
            compose.onNodeWithText("With a transcript").performScrollTo().performClick()
            compose.onNodeWithText("QA written orchard").assertDoesNotExist()
            reveal("QA audio orchard")
            capture("transcript-filter")
            compose.onNodeWithText("Clear filters").performScrollTo().performClick()
            reveal("QA written orchard")
        } finally { runBlocking { repo.removeMemory(audio.id); repo.removeMemory(plain.id) } }
    }
    @Test fun settingsDisclosesHostedVerifierAndLocalTranscription() {
        ready()
        compose.onNodeWithText("Settings",useUnmergedTree=true).performClick()
        compose.onNodeWithText("Amazon purchases send",substring=true).performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("Saved-recording transcription runs on this device.",substring=true).assertExists()
        compose.onNodeWithText("Full privacy notice").performScrollTo().assertIsDisplayed()
        capture("privacy-disclosure")
    }
    @androidx.test.filters.SdkSuppress(maxSdkVersion = 32)
    @Test fun remindersRequireOptInDeliverGenericContentAndCancel() {
        val reminders = com.lifetalea.app.features.StoryReminders(context)
        val before = reminders.enabled
        val manager = context.getSystemService(android.app.NotificationManager::class.java)
        try {
            reminders.setEnabled(false)
            reminders.deliver()
            org.junit.Assert.assertTrue(manager.activeNotifications.none { it.id == com.lifetalea.app.features.StoryReminders.ID })
            ready()
            compose.onNodeWithText("Settings",useUnmergedTree=true).performClick()
            compose.onNodeWithText("Optional reminders").performScrollTo().performClick()
            compose.waitUntil(10000) { reminders.enabled }
            reminders.deliver()
            compose.waitUntil(10000) { manager.activeNotifications.any { it.id == com.lifetalea.app.features.StoryReminders.ID } }
            val notification = manager.activeNotifications.single { it.id == com.lifetalea.app.features.StoryReminders.ID }.notification
            org.junit.Assert.assertEquals(context.getString(R.string.hero_body),notification.extras.getCharSequence(android.app.Notification.EXTRA_TEXT).toString())
            org.junit.Assert.assertEquals(android.app.Notification.VISIBILITY_PRIVATE,notification.visibility)
            capture("reminder-enabled")
            compose.onNodeWithText("Optional reminders").performClick()
            compose.waitUntil(10000) { !reminders.enabled }
            compose.waitUntil(10000) { manager.activeNotifications.none { it.id == com.lifetalea.app.features.StoryReminders.ID } }
            org.junit.Assert.assertTrue(manager.activeNotifications.none { it.id == com.lifetalea.app.features.StoryReminders.ID })
        } finally { reminders.setEnabled(before) }
    }
}

