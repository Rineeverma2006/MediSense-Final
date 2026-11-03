# Android build guide

The React app is packaged with Capacitor under `frontend/android/`. It uses the same backend/API account model as the web app. This checkout has an Android project scaffold, but no APK is included or claimed as built.

## Build a debug APK on Windows

1. Install Android Studio, its Android SDK, and a compatible JDK (use the version supported by the bundled Android Gradle Plugin).
2. Set `JAVA_HOME` and `ANDROID_HOME`, install the SDK platform/build-tools requested by Android Studio, and accept SDK licenses.
3. From `frontend`, run `npm ci`, `npm run build`, then `npx cap sync android`.
4. Open `frontend/android` in Android Studio and build the `app` debug variant, or run `gradlew.bat assembleDebug` from that directory.
5. The debug APK is generated under `frontend/android/app/build/outputs/apk/debug/`.

For release, configure a private signing key in a local untracked Gradle properties file, build a signed release bundle/APK through Android Studio, and protect backups of the key. Never commit signing credentials. A release needs an HTTPS backend URL configured for the deployed API; local `localhost` is not a public server.

This environment currently has no Java/JDK or Android SDK, so APK compilation and device verification have not been performed. The microphone permission is declared for browser voice features; push notifications and Health Connect require additional native plugins and runtime permission workflows.
