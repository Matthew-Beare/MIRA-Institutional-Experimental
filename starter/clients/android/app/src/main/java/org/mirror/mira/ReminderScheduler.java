package org.mirror.mira;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

public final class ReminderScheduler {
    public static final String EXTRA_REMINDER_ID = "reminder_id";
    public static final String EXTRA_VISUAL_TEXT = "visual_text";
    public static final String EXTRA_SPEECH_TEXT = "speech_text";

    private ReminderScheduler() {}

    public static void schedule(
            Context context,
            String reminderId,
            long triggerAtMillis,
            String visualText,
            String speechText) {
        if (reminderId == null || reminderId.trim().isEmpty()) {
            throw new IllegalArgumentException("reminderId must be nonblank");
        }
        Intent intent = new Intent(context, ReminderReceiver.class)
                .setAction("org.mirror.mira.REMINDER." + reminderId)
                .putExtra(EXTRA_REMINDER_ID, reminderId)
                .putExtra(EXTRA_VISUAL_TEXT, visualText == null ? "Reminder" : visualText)
                .putExtra(EXTRA_SPEECH_TEXT, speechText == null ? "" : speechText);
        PendingIntent pendingIntent = PendingIntent.getBroadcast(
                context,
                reminderId.hashCode(),
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        AlarmManager alarmManager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (alarmManager == null) {
            throw new IllegalStateException("AlarmManager unavailable");
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && alarmManager.canScheduleExactAlarms()) {
            alarmManager.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, triggerAtMillis, pendingIntent);
        } else {
            alarmManager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, triggerAtMillis, pendingIntent);
        }
    }
}
