package org.mirror.mira;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

public final class ReminderReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        Intent service = new Intent(context, SpeechService.class)
                .putExtra(ReminderScheduler.EXTRA_REMINDER_ID,
                        intent.getStringExtra(ReminderScheduler.EXTRA_REMINDER_ID))
                .putExtra(ReminderScheduler.EXTRA_VISUAL_TEXT,
                        intent.getStringExtra(ReminderScheduler.EXTRA_VISUAL_TEXT))
                .putExtra(ReminderScheduler.EXTRA_SPEECH_TEXT,
                        intent.getStringExtra(ReminderScheduler.EXTRA_SPEECH_TEXT));
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            context.startForegroundService(service);
        } else {
            context.startService(service);
        }
    }
}
