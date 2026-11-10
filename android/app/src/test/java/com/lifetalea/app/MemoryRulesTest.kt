package com.lifetalea.app
import com.lifetalea.app.data.*
import org.junit.Assert.*
import org.junit.Test
class MemoryRulesTest {
    @Test fun compoundFiltersUseOnlyTheSelectedMemoryAttachmentsAndAlbum() {
        val a = Memory(id="a", title="Garden", date="1994", precision="YEAR", favourite=true, transcript="Apple tree")
        val b = Memory(id="b", title="Garden", date="1994", precision="YEAR", favourite=true, transcript="Apple tree")
        val c = Memory(id="c", title="Garden", date="2001", precision="YEAR")
        val media = listOf(Attachment(memoryId="a",filename="a.m4a",kind="audio",name="Voice"), Attachment(memoryId="b",filename="b.photo",kind="photo",name="Photo"))
        val links = listOf(AlbumMemory("family","a"), AlbumMemory("other","b"))
        assertEquals(listOf(a),MemoryRules.filtered(listOf(a,b,c),media,links,query="apple",year="١٩٩٤",favourites=true,album="family",attachment="audio",transcriptOnly=true))
        assertTrue(MemoryRules.filtered(listOf(a,b,c),media,links,album="family",attachment="photo").isEmpty())
        assertEquals(listOf(a,b,c),MemoryRules.filtered(listOf(a,b,c),media,links))
        assertEquals(listOf(a,b),MemoryRules.filtered(listOf(a,b,c),media,links,transcriptOnly=true))
    }
    @Test fun localizedDatesPreservePrecision() {
        val year=Memory(date="1994",precision="YEAR")
        assertEquals("١٩٩٤",MemoryRules.formattedDate(year,java.util.Locale.forLanguageTag("ar")))
        assertEquals("février 2024",MemoryRules.formattedDate(Memory(date="2024-02",precision="MONTH"),java.util.Locale.FRANCE))
        assertEquals("",MemoryRules.formattedDate(Memory(),java.util.Locale.FRANCE))
        val day=MemoryRules.formattedDate(Memory(date="2024-02-29",precision="DAY"),java.util.Locale.forLanguageTag("ar"))
        assertTrue(day.contains('٢'));assertFalse(day.contains('2'))
    }
    @Test fun localKeyboardDigitsBecomeCanonicalDates() {
        listOf("٢٠٢٤-٠٢-٢٩", "۲۰۲۴-۰۲-۲۹", "२०२४-०२-२९", "２０２４-０２-２９").forEach {
            val canonical = MemoryRules.normaliseDateDigits(it)
            assertEquals("2024-02-29", canonical)
            assertTrue(MemoryRules.validDate(canonical, "DAY"))
        }
        assertFalse(MemoryRules.validDate(MemoryRules.normaliseDateDigits("٢٠٢٣-٠٢-٢٩"), "DAY"))
    }
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
    @Test fun allPrecisionsUseCanonicalYears() {
        listOf("0000", "+10000", "-0001", "24").forEach { year ->
            assertFalse(MemoryRules.validDate("$year-02", "MONTH"))
            assertFalse(MemoryRules.validDate("$year-02-28", "DAY"))
        }
        assertTrue(MemoryRules.validDate("0001-01-01", "DAY"))
        assertTrue(MemoryRules.validDate("9999-12", "MONTH"))
    }
    @Test fun unknownDatesAppearLast() {
        val old = Memory(date = "1990", precision = "YEAR"); val recent = Memory(date = "2024-01-01", precision = "DAY"); val unknown = Memory()
        assertEquals(listOf(recent, old, unknown), MemoryRules.timeline(listOf(unknown, old, recent)))
    }
}
