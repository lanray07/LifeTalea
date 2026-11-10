package com.lifetalea.app.features

import android.Manifest
import android.app.*
import android.content.*
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import com.lifetalea.app.MainActivity
import com.lifetalea.app.R
import java.time.ZonedDateTime

/** Opt-in, generic local prompts. No library data is read and no network is used. */
class StoryReminders(private val context: Context) {
    private val preferences = context.getSharedPreferences("local_reminders", Context.MODE_PRIVATE)
    val enabled get() = preferences.getBoolean("enabled", false)
    fun permitted() = (Build.VERSION.SDK_INT < 33 || ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED) && NotificationManagerCompat.from(context).areNotificationsEnabled()
    private fun alarm(flags: Int = PendingIntent.FLAG_UPDATE_CURRENT): PendingIntent? = PendingIntent.getBroadcast(context, ID,
        Intent(context, StoryReminderReceiver::class.java).setAction(ACTION), flags or PendingIntent.FLAG_IMMUTABLE)
    fun setEnabled(value: Boolean): Boolean {
        if (value && !permitted()) return false
        if (!preferences.edit().putBoolean("enabled", value).commit()) return false
        reschedule()
        return true
    }
    fun reschedule() {
        val manager = context.getSystemService(AlarmManager::class.java)
        if (!enabled) {
            alarm(PendingIntent.FLAG_NO_CREATE)?.let { manager.cancel(it); it.cancel() }
            context.getSystemService(NotificationManager::class.java).cancel(ID)
            return
        }
        manager.setInexactRepeating(AlarmManager.RTC_WAKEUP, nextTime(ZonedDateTime.now()).toInstant().toEpochMilli(), AlarmManager.INTERVAL_DAY, alarm()!!)
    }
    @android.annotation.SuppressLint("MissingPermission") // permitted() checks runtime permission; notify also handles a concurrent revocation.
    fun deliver() {
        if (!enabled || !permitted()) return
        val manager = context.getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(NotificationChannel(CHANNEL, context.getString(R.string.reminders), NotificationManager.IMPORTANCE_DEFAULT))
        val channel = manager.getNotificationChannel(CHANNEL)
        if (channel?.importance == NotificationManager.IMPORTANCE_NONE) return
        val open = PendingIntent.getActivity(context, ID, Intent(context, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP), PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val notification = NotificationCompat.Builder(context, CHANNEL).setSmallIcon(R.drawable.ic_book)
            .setContentTitle(context.getString(R.string.app_name)).setContentText(context.getString(R.string.hero_body))
            .setContentIntent(open).setAutoCancel(true).setVisibility(NotificationCompat.VISIBILITY_PRIVATE).build()
        // Permission may be revoked between the check and delivery.
        runCatching { manager.notify(ID, notification) }
    }
    companion object {
        const val ID = 4817
        const val ACTION = "com.lifetalea.app.STORY_REMINDER"
        private const val CHANNEL = "story_reminders"
        fun nextTime(now: ZonedDateTime): ZonedDateTime = now.withHour(20).withMinute(0).withSecond(0).withNano(0).let { if (it.isAfter(now)) it else it.plusDays(1) }
    }
}

class StoryReminderReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val reminders = StoryReminders(context)
        when (intent.action) {
            StoryReminders.ACTION -> reminders.deliver()
            Intent.ACTION_BOOT_COMPLETED, Intent.ACTION_TIME_CHANGED, Intent.ACTION_TIMEZONE_CHANGED -> reminders.reschedule()
        }
    }
}
