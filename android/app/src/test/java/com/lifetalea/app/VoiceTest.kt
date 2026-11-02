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
}
