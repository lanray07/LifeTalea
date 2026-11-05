package com.lifetalea.app
import com.lifetalea.app.voice.*
import org.junit.Assert.*
import org.junit.Test
import java.util.Locale
class VoiceTest {
    @Test fun commandsHaveRealStructuredIntents() {
        assertEquals(VoiceIntent.NEW_MEMORY, CommandParser.parse("Create a new memory.", Locale.UK).intent)
        assertEquals(VoiceIntent.STOP_RECORDING, CommandParser.parse("Stop recording", Locale.US).intent)
        assertEquals("1994", CommandParser.parse("Show memories from 1994", Locale.UK).query)
        assertEquals(VoiceIntent.UNKNOWN, CommandParser.parse("Delete all memories", Locale.UK).intent)
        assertEquals(VoiceIntent.UNKNOWN, CommandParser.parse("Start recording", Locale.FRANCE).intent)
    }

    @Test fun namedAlbumAndYearCommandsCarryOnlyTheirTarget() {
        assertEquals(VoiceCommand(VoiceIntent.ALBUMS, "family album"), CommandParser.parse("Open family album.", Locale.UK))
        assertEquals(VoiceCommand(VoiceIntent.ALBUMS, "family history"), CommandParser.parse("Open album Family History!", Locale.UK))
        assertEquals(VoiceCommand(VoiceIntent.ALBUMS), CommandParser.parse("Open albums", Locale.UK))
        assertEquals(VoiceCommand(VoiceIntent.SEARCH, "last year"), CommandParser.parse("Show memories from last year", Locale.UK))
        assertEquals(VoiceIntent.UNKNOWN, CommandParser.parse("Show memories from yesterday", Locale.UK).intent)
    }
}
