package com.lifetalea.app
import com.lifetalea.app.features.StoryReminders
import java.time.ZonedDateTime
import org.junit.Assert.*
import org.junit.Test

class ReminderTimeTest {
    @Test fun schedulesFutureLocalEveningAcrossDayAndDstBoundaries() {
        for (input in listOf("2026-03-28T21:00:00Z[Europe/London]", "2026-10-24T21:00:00+01:00[Europe/London]", "2026-11-10T19:59:59Z[Europe/London]", "2026-11-10T20:00:00Z[Europe/London]")) {
            val now = ZonedDateTime.parse(input); val next = StoryReminders.nextTime(now)
            assertTrue(next.isAfter(now)); assertEquals(20,next.hour); assertEquals(0,next.minute)
        }
    }
}
