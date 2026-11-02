package com.lifetalea.app

import android.content.res.Configuration
import android.graphics.Bitmap
import android.os.LocaleList
import android.view.View
import androidx.appcompat.app.AppCompatDelegate
import androidx.core.os.LocaleListCompat
import androidx.compose.ui.graphics.asAndroidBitmap
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.util.Locale
import com.lifetalea.app.data.LifeDatabase
import com.lifetalea.app.data.Memory
import kotlinx.coroutines.runBlocking
import android.content.Context
import android.view.inputmethod.InputMethodManager

@RunWith(AndroidJUnit4::class)
class LocalizationTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private fun capture(folder:File, tag:String, name:String) {
        compose.runOnIdle {
            (compose.activity.getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager)
                .hideSoftInputFromWindow(compose.activity.window.decorView.windowToken,0)
        }
        compose.waitForIdle()
        compose.onRoot().captureToImage().asAndroidBitmap().let { image ->
            File(folder,"$tag-$name.png").outputStream().use { image.compress(Bitmap.CompressFormat.PNG,100,it) }
        }
    }

    @Test fun everyDraftLocaleResolvesAndRendersWithMirroredNavigation() {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val base = instrumentation.targetContext
        val tags = base.resources.getStringArray(R.array.supported_locale_tags)
        assertEquals("This test expects the full debug language matrix", 22, tags.size)
        val selected=InstrumentationRegistry.getArguments().getString("localizationLocales")?.split(',') ?: tags.toList()
        require(selected.all { it in tags })
        val original = AppCompatDelegate.getApplicationLocales()
        val dao = LifeDatabase.open(base).library()
        val storiesBefore = runBlocking { dao.allMemories().associateBy { it.id } }
        val fixture = Memory(title="A family moment — fictional localization QA",story="A fictional demonstration story. Personal stories are never translated automatically.",transcript="Manually entered fictional transcript. No automatic transcription was performed.",date="1994",precision="YEAR")
        runBlocking { dao.save(fixture) }
        val evidence = File(base.filesDir, "test-evidence/localization").apply { mkdirs() }
        var primaryFailure:Throwable?=null
        try {
            compose.waitUntil(20000) { runCatching { compose.onRoot().fetchSemanticsNode(); true }.getOrDefault(false) }
            val skip = base.getString(R.string.skip)
            val add = base.getString(R.string.add_memory)
            compose.waitUntil(20000) { runCatching { compose.onAllNodesWithText(skip).fetchSemanticsNodes().isNotEmpty() || compose.onAllNodesWithText(add).fetchSemanticsNodes().isNotEmpty() }.getOrDefault(false) }
            if (runCatching { compose.onAllNodesWithText(skip).fetchSemanticsNodes().isNotEmpty() }.getOrDefault(false)) {
                compose.onNodeWithText(skip).performScrollTo().performClick()
            }
            compose.waitUntil(20000) { runCatching { compose.onAllNodesWithText(add).fetchSemanticsNodes().isNotEmpty() }.getOrDefault(false) }
            compose.onAllNodesWithText(compose.activity.getString(R.string.settings)).onFirst().performClick()
            compose.onNodeWithTag("language_picker").performScrollTo().performClick()
            compose.onNodeWithTag("language_options").performScrollToNode(hasTestTag("language_fr-FR"))
            compose.onNodeWithTag("language_fr-FR").performClick()
            compose.waitUntil(20000) { runCatching { compose.activity.resources.configuration.locales[0].language == "fr" && compose.onAllNodesWithText("Souvenirs").fetchSemanticsNodes().isNotEmpty() }.getOrDefault(false) }
            compose.onAllNodesWithText("Souvenirs").onFirst().performClick()
            for (tag in selected) {
                val locale = Locale.forLanguageTag(tag)
                val configuration = Configuration(base.resources.configuration).apply {
                    setLocales(LocaleList(locale)); setLayoutDirection(locale)
                }
                val localized = base.createConfigurationContext(configuration)
                // Resolve every app string, not only the headings in the screenshot.
                for (field in R.string::class.java.fields) {
                    assertTrue("$tag/${field.name}", localized.getString(field.getInt(null)).isNotBlank())
                }
                for (count in listOf(0, 1, 2, 3, 5, 11, 21, 101)) {
                    val label = localized.resources.getQuantityString(R.plurals.memory_count, count, count)
                    assertTrue(label.isNotBlank()); assertFalse(label.contains("%1\$d"))
                }
                val previous=compose.activity
                val changes=AppCompatDelegate.getApplicationLocales().toLanguageTags()!=tag
                instrumentation.runOnMainSync {
                    AppCompatDelegate.setApplicationLocales(LocaleListCompat.forLanguageTags(tag))
                }
                val heading = localized.getString(R.string.hero_title)
                compose.waitUntil(20000) {
                    runCatching { (!changes || compose.activity !== previous) && compose.activity.resources.configuration.locales[0].toLanguageTag()==tag && compose.onAllNodesWithText(heading).fetchSemanticsNodes().isNotEmpty() }.getOrDefault(false)
                }
                compose.onNodeWithText(heading).assertIsDisplayed()
                assertEquals(locale.language, compose.activity.resources.configuration.locales[0].language)
                assertEquals(if (tag == "ar") View.LAYOUT_DIRECTION_RTL else View.LAYOUT_DIRECTION_LTR,
                    compose.activity.resources.configuration.layoutDirection)
                val root = compose.onRoot().fetchSemanticsNode().boundsInRoot
                val title = compose.onNodeWithText(heading).fetchSemanticsNode().boundsInRoot
                assertTrue("$tag heading fits horizontally", title.left >= root.left && title.right <= root.right)
                val navigation = compose.onAllNodesWithText(localized.getString(R.string.memories)).fetchSemanticsNodes().first().boundsInRoot
                if (root.width > 1500) {
                    assertTrue("$tag navigation mirrors with locale", if (tag == "ar") navigation.center.x > root.center.x else navigation.center.x < root.center.x)
                }
                capture(evidence,tag,"home")
                fun navigate(resource:Int) {
                    compose.onAllNodesWithText(localized.getString(resource)).onFirst().performClick()
                    compose.waitForIdle()
                }
                navigate(R.string.albums)
                compose.onNodeWithText(localized.getString(R.string.new_album)).assertIsDisplayed()
                capture(evidence,tag,"albums")
                navigate(R.string.timeline);capture(evidence,tag,"timeline")
                navigate(R.string.keepsakes);capture(evidence,tag,"keepsakes")
                navigate(R.string.settings)
                compose.onNodeWithText(localized.getString(R.string.create_backup)).performScrollTo()
                capture(evidence,tag,"settings")
                navigate(R.string.memories)
                compose.onNodeWithText(localized.getString(R.string.add_memory)).performClick()
                capture(evidence,tag,"editor")
                compose.onNodeWithText(localized.getString(R.string.cancel)).performScrollTo().performClick()
                run {
                    compose.onNodeWithText(fixture.title).performScrollTo().performClick()
                    compose.onNodeWithText(localized.getString(R.string.record)).performScrollTo()
                    capture(evidence,tag,"voice")
                    compose.onNodeWithText(localized.getString(R.string.edit)).performScrollTo().performClick()
                    compose.onNodeWithText(localized.getString(R.string.transcript)).performScrollTo()
                    capture(evidence,tag,"transcript")
                    compose.onNodeWithText(localized.getString(R.string.cancel)).performScrollTo().performClick()
                    compose.onNodeWithText(localized.getString(R.string.back)).performScrollTo().performClick()
                }
            }
            // Unavailable languages fall back to complete English resources.
            val fallback = base.createConfigurationContext(Configuration(base.resources.configuration).apply { setLocale(Locale.forLanguageTag("zu-ZA")) })
            assertEquals("Every story deserves a place.", fallback.getString(R.string.hero_title))
            assertEquals("Changing interface language must preserve stored stories", storiesBefore,
                runBlocking { dao.allMemories().filter { it.id!=fixture.id }.associateBy { it.id } })
            File(evidence,if(selected.size==tags.size) "result.json" else "subset-result.json").writeText("""{"status":"PASS","localeCount":${selected.size},"screensPerLocale":8,"scope":"All string resolution, eight integer plural counts per locale, manual language picker, English fallback, stored-story preservation, home headings, mirrored navigation and eight real screen captures with a fictional fixture; not native linguistic approval or full accessibility certification"}""")
        } catch(error:Throwable) {
            primaryFailure=error
            throw error
        } finally {
            runCatching { capture(evidence,"diagnostic","last-state") }
            runBlocking { dao.deleteMemory(fixture.id) }
            try { instrumentation.runOnMainSync { AppCompatDelegate.setApplicationLocales(original) } }
            catch(cleanup:Throwable) { if(primaryFailure!=null) primaryFailure.addSuppressed(cleanup) else throw cleanup }
        }
    }
}
