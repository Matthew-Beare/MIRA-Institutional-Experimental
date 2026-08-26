package org.mirror.mira;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.media.AudioAttributes;
import android.os.IBinder;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;

import java.util.Collections;
import java.util.HashSet;
import java.util.Set;

public final class SpeechService extends Service {
    private static final String CHANNEL_ID = "mira_appointment_reminders";
    private static final String PREFS = "mira_spoken_reminder_state";
    private static final Set<String> IN_FLIGHT = Collections.synchronizedSet(new HashSet<>());
    private TextToSpeech tts;

    public static void start(Context context, String reminderId, String visualText, String speechText) {
        Intent intent = new Intent(context, SpeechService.class)
                .putExtra(ReminderScheduler.EXTRA_REMINDER_ID, reminderId)
                .putExtra(ReminderScheduler.EXTRA_VISUAL_TEXT, visualText)
                .putExtra(ReminderScheduler.EXTRA_SPEECH_TEXT, speechText);
        context.startForegroundService(intent);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        String reminderId = safe(intent == null ? null : intent.getStringExtra(ReminderScheduler.EXTRA_REMINDER_ID));
        String visualText = safe(intent == null ? null : intent.getStringExtra(ReminderScheduler.EXTRA_VISUAL_TEXT));
        String speechText = safe(intent == null ? null : intent.getStringExtra(ReminderScheduler.EXTRA_SPEECH_TEXT));
        if (reminderId.isEmpty()) {
            stopSelf(startId);
            return START_NOT_STICKY;
        }

        ensureChannel();
        Notification notification = new Notification.Builder(this, CHANNEL_ID)
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentTitle("MIRA reminder")
                .setContentText(visualText.isEmpty() ? "Appointment reminder" : visualText)
                .setAutoCancel(true)
                .build();
        startForeground(notificationId(reminderId), notification);

        SharedPreferences prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        if (prefs.getBoolean("spoken:" + reminderId, false) || !IN_FLIGHT.add(reminderId)) {
            stopForeground(STOP_FOREGROUND_DETACH);
            stopSelf(startId);
            return START_NOT_STICKY;
        }
        if (speechText.isEmpty()) {
            IN_FLIGHT.remove(reminderId);
            stopForeground(STOP_FOREGROUND_DETACH);
            stopSelf(startId);
            return START_NOT_STICKY;
        }

        tts = new TextToSpeech(this, status -> {
            if (status != TextToSpeech.SUCCESS || tts == null) {
                finish(reminderId, startId, false);
                return;
            }
            tts.setAudioAttributes(new AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_ASSISTANCE_ACCESSIBILITY)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                    .build());
            tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
                @Override public void onStart(String utteranceId) {}
                @Override public void onDone(String utteranceId) { finish(reminderId, startId, true); }
                @Override public void onError(String utteranceId) { finish(reminderId, startId, false); }
            });
            int result = tts.speak(speechText, TextToSpeech.QUEUE_FLUSH, null, reminderId);
            if (result == TextToSpeech.ERROR) {
                finish(reminderId, startId, false);
            }
        });
        return START_NOT_STICKY;
    }

    private void finish(String reminderId, int startId, boolean spoken) {
        if (spoken) {
            getSharedPreferences(PREFS, MODE_PRIVATE)
                    .edit()
                    .putBoolean("spoken:" + reminderId, true)
                    .apply();
        }
        IN_FLIGHT.remove(reminderId);
        if (tts != null) {
            tts.stop();
            tts.shutdown();
            tts = null;
        }
        stopForeground(STOP_FOREGROUND_DETACH);
        stopSelf(startId);
    }

    private void ensureChannel() {
        NotificationManager manager = getSystemService(NotificationManager.class);
        if (manager != null) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID,
                    "Appointment reminders",
                    NotificationManager.IMPORTANCE_HIGH);
            channel.setDescription("Visual and user-approved spoken MIRA appointment reminders");
            manager.createNotificationChannel(channel);
        }
    }

    private static String safe(String value) {
        return value == null ? "" : value.trim();
    }

    private static int notificationId(String reminderId) {
        return 1000 + Math.abs(reminderId.hashCode() % 1000000);
    }

    @Override
    public void onDestroy() {
        if (tts != null) {
            tts.stop();
            tts.shutdown();
            tts = null;
        }
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
