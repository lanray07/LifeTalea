package com.lifetalea.app
import com.lifetalea.app.data.*
import org.junit.Assert.*
import org.junit.Test
class MemoryRulesTest {
    @Test fun datesDoNotInventPrecision() {
        assertTrue(MemoryRules.validDate("", "UNKNOWN"))
        assertFalse(MemoryRules.validDate("1994", "UNKNOWN"))
        assertTrue(MemoryRules.validDate("1994", "YEAR"))
        assertFalse(MemoryRules.validDate("0000", "YEAR"))
        assertTrue(MemoryRules.validDate("2024-02-29", "DAY"))
        assertFalse(MemoryRules.validDate("2023-02-29", "DAY"))
        assertTrue(MemoryRules.validDate("2000-12", "MONTH"))
    }
    @Test fun searchIncludesTranscriptAndTags() {
        val m = Memory(title = "Sunday", tags = "recipe", transcript = "Grandma's kitchen")
        assertTrue(MemoryRules.matches(m, "GRANDMA")); assertTrue(MemoryRules.matches(m, "recipe")); assertFalse(MemoryRules.matches(m, "holiday"))
    }
    @Test fun unknownDatesAppearLast() {
        val old = Memory(date = "1990", precision = "YEAR"); val recent = Memory(date = "2024-01-01", precision = "DAY"); val unknown = Memory()
        assertEquals(listOf(recent, old, unknown), MemoryRules.timeline(listOf(unknown, old, recent)))
    }
}
