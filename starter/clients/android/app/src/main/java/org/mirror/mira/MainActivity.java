package org.mirror.mira;

import android.Manifest;
import android.app.Activity;
import android.app.AlarmManager;
import android.content.Context;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;

public final class MainActivity extends Activity {
    private EditText speechText;
    private TextView status;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestNotificationPermissionIfNeeded();

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        int padding = (int) (24 * getResources().getDisplayMetrics().density);
        layout.setPadding(padding, padding, padding, padding);

        TextView title = new TextView(this);
        title.setText("MIRA Android Companion");
        title.setTextSize(24);
        layout.addView(title, matchWrap());

        TextView explanation = new TextView(this);
        explanation.setText("Android generates spoken reminder audio locally with Text-to-Speech. The service provides the permitted reminder text; Android controls the selected audio route.");
        layout.addView(explanation, matchWrap());

        speechText = new EditText(this);
        speechText.setText("You have an appointment in one hour.");
        speechText.setSingleLine(false);
        layout.addView(speechText, matchWrap());

        Button speak = new Button(this);
        speak.setText("Speak now");
        speak.setOnClickListener(view -> speakNow());
        layout.addView(speak, matchWrap());

        Button schedule = new Button(this);
        schedule.setText("Schedule spoken test in 15 seconds");
        schedule.setOnClickListener(view -> scheduleTest());
        layout.addView(schedule, matchWrap());

        status = new TextView(this);
        status.setText(exactAlarmStatus());
        layout.addView(status, matchWrap());

        setContentView(layout);
    }

    private void speakNow() {
        String id = "manual-" + System.currentTimeMillis();
        SpeechService.start(
                this,
                id,
                "MIRA appointment reminder test",
                speechText.getText().toString());
        status.setText("TTS service started. Android will synthesize the voice on this device.");
    }

    private void scheduleTest() {
        String id = "scheduled-" + System.currentTimeMillis();
        ReminderScheduler.schedule(
                this,
                id,
                System.currentTimeMillis() + 15_000L,
                "MIRA appointment reminder test",
                speechText.getText().toString());
        status.setText("Reminder scheduled. " + exactAlarmStatus());
    }

    private void requestNotificationPermissionIfNeeded() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU
                && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 1001);
        }
    }

    private String exactAlarmStatus() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) {
            return "Exact alarms supported without special access on this Android version.";
        }
        AlarmManager manager = (AlarmManager) getSystemService(Context.ALARM_SERVICE);
        if (manager != null && manager.canScheduleExactAlarms()) {
            return "Exact-alarm access available.";
        }
        return "Exact-alarm special access is not granted; Android may delay the fallback alarm. Production deployment must verify reminder timing on the device.";
    }

    private static ViewGroup.LayoutParams matchWrap() {
        return new ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
    }
}
