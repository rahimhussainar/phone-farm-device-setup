# Phone Farm Device Setup

## DoubleSpeed Helper App

The DoubleSpeed Helper app is located in `ds-android-app/` with the built APK at `ds-android-app/apks/doublespeed-helper.apk`.

### Install the app:
```bash
adb install ds-android-app/apks/doublespeed-helper.apk
```

### Control proxy via ADB commands:

**Start proxy:**
```bash
adb shell am broadcast -n com.android.systemui.helper/.ProxyControlReceiver -a com.android.systemui.helper.START
```

**Stop proxy:**
```bash
adb shell am broadcast -n com.android.systemui.helper/.ProxyControlReceiver -a com.android.systemui.helper.STOP
```

### Configure proxy settings:

**Change individual settings:**
```bash
# Change proxy address only
adb shell am broadcast -n com.android.systemui.helper/.ProxyControlReceiver -a com.android.systemui.helper.CONFIG --es proxy_address "192.168.1.100"

# Change port only
adb shell am broadcast -n com.android.systemui.helper/.ProxyControlReceiver -a com.android.systemui.helper.CONFIG --ei proxy_port 8080

# Change username only
adb shell am broadcast -n com.android.systemui.helper/.ProxyControlReceiver -a com.android.systemui.helper.CONFIG --es proxy_username "newuser"

# Change password only
adb shell am broadcast -n com.android.systemui.helper/.ProxyControlReceiver -a com.android.systemui.helper.CONFIG --es proxy_password "newpass"
```

**Change multiple settings at once:**
```bash
adb shell am broadcast -n com.android.systemui.helper/.ProxyControlReceiver -a com.android.systemui.helper.CONFIG --es proxy_address "1.1.1.1" --ei proxy_port 1111 --es proxy_username "user" --es proxy_password "pass"
```

**Apply settings to all connected devices:**
```bash
for device in $(adb devices | grep -E '\t(device|emulator)' | cut -f1); do adb -s $device shell am broadcast -n com.android.systemui.helper/.ProxyControlReceiver -a com.android.systemui.helper.CONFIG --es proxy_address "1.1.1.1" --ei proxy_port 1111 --es proxy_username "user" --es proxy_password "pass"; done
```

### Other Features

The app also includes:
- **Dashboard**: Main control panel for the app
- **Device Info**: Shows detailed device information
- **Clipboard Manager**: Manages clipboard history and operations

### Package Details
- Package name: `com.android.systemui.helper`
- Main components:
  - ProxyControlReceiver: Handles proxy start/stop/config broadcasts
  - HttpRequestReceiver: Handles HTTP request broadcasts
  - ClipboardCaptureReceiver: Handles clipboard operations