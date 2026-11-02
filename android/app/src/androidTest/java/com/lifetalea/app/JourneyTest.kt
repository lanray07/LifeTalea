package com.lifetalea.app

import android.graphics.Bitmap
import androidx.compose.ui.graphics.asAndroidBitmap
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Rule
import org.junit.Test
import org.junit.After
import org.junit.runner.RunWith
import java.io.File

@RunWith(AndroidJUnit4::class)
class JourneyTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private fun capture(name: String) {
        compose.waitForIdle()
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val folder = File(context.filesDir, "test-evidence/screenshots/en-GB").apply { mkdirs() }
        compose.onRoot().captureToImage().asAndroidBitmap().let { image -> File(folder, "$name.png").outputStream().use { image.compress(Bitmap.CompressFormat.PNG, 100, it) } }
    }
    @After fun captureFinalState() { runCatching { capture("qa-last-state") } }
    @Test fun writeFindEditAndOrganiseAFictionalStory() {
        compose.waitUntil(20000) { runCatching { compose.onRoot().fetchSemanticsNode() }.isSuccess }
        compose.waitUntil(20000) { runCatching { compose.onAllNodesWithText("Skip for now").fetchSemanticsNodes().isNotEmpty() || compose.onAllNodesWithText("Add a memory").fetchSemanticsNodes().isNotEmpty() }.getOrDefault(false) }
        if (runCatching { compose.onAllNodesWithText("Skip for now").fetchSemanticsNodes().isNotEmpty() }.getOrDefault(false)) compose.onNodeWithText("Skip for now").performScrollTo().performClick()
        compose.waitUntil(15000) { runCatching { compose.onAllNodesWithText("Add a memory").fetchSemanticsNodes().isNotEmpty() }.getOrDefault(false) }
        val fullHeight=compose.onRoot().fetchSemanticsNode().boundsInRoot.height
        capture("01-home")
        compose.onNodeWithText("Add a memory").performClick()
        compose.onNodeWithText("Title").performTextInput("The orchard picnic — fictional demo")
        compose.onNodeWithText("Your story").performTextInput("We spread a blanket beneath the apple tree. Everyone brought a favourite recipe. Fictional demonstration story for development testing.")
        compose.runOnIdle {
            val input = compose.activity.getSystemService(android.content.Context.INPUT_METHOD_SERVICE) as android.view.inputmethod.InputMethodManager
            input.hideSoftInputFromWindow(compose.activity.window.decorView.windowToken, 0)
        }
        compose.waitUntil(15000) { runCatching { compose.onRoot().fetchSemanticsNode().boundsInRoot.height >= fullHeight-1 }.getOrDefault(false) }
        compose.onNodeWithText("Year").performScrollTo().performClick()
        compose.onNodeWithText("Year").assertIsSelected()
        compose.onNodeWithText("Event date").performScrollTo().performTextInput("1994")
        compose.onNodeWithText("Tags (comma separated)").performScrollTo().performTextInput("family, summer")
        compose.onNodeWithText("Editable transcript").performScrollTo().performTextInput("Manually entered fictional transcript. No automatic transcription has been performed.")
        compose.onNodeWithText("Save", useUnmergedTree = true).performScrollTo().performClick()
        compose.waitUntil(15000) { compose.onAllNodesWithText("The orchard picnic — fictional demo").fetchSemanticsNodes().isNotEmpty() }
        capture("03-story")
        compose.onNodeWithText("Edit", useUnmergedTree = true).performScrollTo().performClick()
        compose.onNodeWithText("Editable transcript").performScrollTo().assertExists()
        capture("04-manual-transcript")
        compose.onNodeWithText("Save", useUnmergedTree = true).performScrollTo().performClick()
        compose.waitForIdle()
        compose.onNodeWithText("Back", useUnmergedTree = true).performScrollTo().performClick()
        compose.onNodeWithText("Search stories, tags, transcripts…").performTextInput("orchard")
        compose.onNodeWithText("The orchard picnic — fictional demo").assertExists()
        compose.onNodeWithText("Search stories, tags, transcripts…").performTextClearance()
        compose.onNodeWithText("Timeline", useUnmergedTree = true).performClick()
        compose.onNodeWithText("The orchard picnic — fictional demo").assertExists()
        capture("05-timeline")
        compose.onNodeWithText("Albums", useUnmergedTree = true).performClick()
        compose.onNodeWithText("New album").performClick()
        compose.onNodeWithText("Title").performTextInput("Summer stories — fictional demo")
        compose.onNodeWithText("Save").performClick()
        compose.waitUntil(15000) { compose.onAllNodesWithText("Summer stories — fictional demo").fetchSemanticsNodes().isNotEmpty() }
        capture("02-albums")
        compose.onNodeWithText("Keepsakes", useUnmergedTree = true).performClick()
        compose.onNodeWithText("Create a scrapbook").performClick()
        compose.onNodeWithText("Cover title").performTextInput("Little family moments — fictional demo")
        compose.onNodeWithText("Save").performClick()
        compose.waitUntil(15000) { compose.onAllNodesWithText("Add page").fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithText("Add page").performClick()
        compose.onNodeWithText("The orchard picnic — fictional demo").performClick()
        compose.waitForIdle()
        capture("06-scrapbook")
    }
}
