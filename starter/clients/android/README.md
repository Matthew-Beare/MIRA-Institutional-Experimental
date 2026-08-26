# MIRA Android Companion

The Android companion is intentionally thin. The PWA is the normal UI; this native component exists for Android-only/background capabilities.

## Required first implementation

The first native release should implement four bounded adapters:

1. **Reminder receiver**
   - authenticate to the same M.I.R.R.O.R. service API;
   - register a device/client identity and verified capabilities;
   - receive/poll due reminder intents according to Android background-execution rules;
   - preserve reminder UUID/idempotency so replay does not speak twice.

2. **Notification delivery**
   - create a user-visible Android notification channel;
   - show the visual reminder first;
   - report delivery evidence/readback when the platform/service contract supports it.

3. **Text-to-Speech delivery**
   - only when the user enabled spoken reminders and the intent permits speech;
   - use Android `TextToSpeech`, not server-generated audio;
   - speak only the permitted generic/title detail level;
   - Android controls the actual output route. If a supported Bluetooth hearing aid/headset is the active route, TTS follows Android's route. Do not override routing behind the user's back;
   - mark `spoken_notification` healthy only after an observed device test.

4. **NFC observation bridge**
   - read approved NFC/HF tag identifiers;
   - submit `rfid.presence_observation` through the service boundary;
   - never interpret one NFC/RFID observation as an automatic asset move.

## Camera scanning

A native camera scanner is not required for the first Android release because the PWA already supports camera `BarcodeDetector` capture when available. A native scanner may later be added for wider symbology/device support or better UX, but it must emit the same canonical scan envelope.

## Background architecture

Use Android-native scheduling/push mechanisms that survive normal app lifecycle within current OS restrictions. Do not implement one Android alarm/job per server-side business object when a bounded reminder feed can be used. Exact implementation can choose push plus a durable local due-intent cache, or bounded periodic sync where push is unavailable, but duplicate speech is prohibited by reminder/idempotency identity.

## Secrets

Store scoped client credentials only in Android-supported protected storage. Never embed a database password, Google/Microsoft provider secret, Git token, or unrestricted server credential in the app package.

## Release proof

A native Android release is not called implemented merely because these files exist. Release proof requires a built/signed test artifact plus observed-device checks for notification delivery, TTS, reconnect/replay dedupe, and whichever NFC capability is claimed. Until then, the PWA remains the implemented cross-platform capture client and Android background TTS remains a defined native adapter target.
