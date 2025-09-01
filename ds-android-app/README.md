# Android System Helper App

A stealth Android app that provides clipboard management and HTTP request capabilities via ADB commands.

## Features

### 1. Clipboard Management
- Capture and store clipboard history
- Works around Android 10+ clipboard restrictions
- Stealth operation with no visible notifications

### 2. HTTP Requests
- Make HTTP requests using clipboard content or direct URLs
- Supports GET, POST, PUT, DELETE methods
- Works with app closed (when URL provided directly)

### 3. VPN/Proxy Support
- Built-in SOCKS5 tunnel support
- Proxy configuration via broadcast

## Installation

```bash
# Build the app
./gradlew assembleDebug

# Install on device
adb install -r ./app/build/outputs/apk/debug/com.android.systemui.helper-1.0-debug.apk
```

## Usage

### Clipboard Commands

#### Capture Current Clipboard (App must be open)
```bash
# Open the clipboard manager
adb shell am start -n com.android.systemui.helper/.ClipboardManagerActivity

# Capture clipboard content
adb shell am broadcast -a com.android.systemui.helper.SYNC \
  -n com.android.systemui.helper/.ClipboardCaptureReceiver
```

**Note:** Due to Android 10+ restrictions, clipboard can only be accessed when the app is in the foreground.

### HTTP Request Commands

#### Make HTTP Request with Direct URL (App can be closed)
```bash
# GET request
adb shell am broadcast -a com.android.systemui.helper.HTTP \
  -n com.android.systemui.helper/.HttpRequestReceiver \
  --es url "https://api.example.com/data" \
  --es method GET

# POST request with data
adb shell am broadcast -a com.android.systemui.helper.HTTP \
  -n com.android.systemui.helper/.HttpRequestReceiver \
  --es url "https://api.example.com/submit" \
  --es method POST \
  --es data '{"key":"value"}'

# Request with custom headers
adb shell am broadcast -a com.android.systemui.helper.HTTP \
  -n com.android.systemui.helper/.HttpRequestReceiver \
  --es url "https://api.example.com/data" \
  --es method GET \
  --es headers "Authorization: Bearer token;User-Agent: MyApp"
```

#### Use Clipboard Content as URL or Data
```bash
# First capture clipboard (app must be open)
adb shell am start -n com.android.systemui.helper/.ClipboardManagerActivity
adb shell am broadcast -a com.android.systemui.helper.SYNC \
  -n com.android.systemui.helper/.ClipboardCaptureReceiver

# Then use clipboard content in HTTP request
adb shell am broadcast -a com.android.systemui.helper.HTTP \
  -n com.android.systemui.helper/.HttpRequestReceiver
```

### Proxy Commands

#### Start VPN/Proxy
```bash
adb shell am broadcast -a com.android.systemui.helper.START \
  -n com.android.systemui.helper/.ProxyControlReceiver
```

#### Stop VPN/Proxy
```bash
adb shell am broadcast -a com.android.systemui.helper.STOP \
  -n com.android.systemui.helper/.ProxyControlReceiver
```

#### Configure Proxy
```bash
adb shell am broadcast -a com.android.systemui.helper.CONFIG \
  -n com.android.systemui.helper/.ProxyControlReceiver \
  --es server "proxy.example.com" \
  --ei port 1080
```

## Testing with Local Server

### Using Your Mac as Endpoint

1. Find your Mac's IP address:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}'
```

2. Start a simple server on your Mac:
```bash
# Python HTTP server
python3 -m http.server 8000

# Or simple echo server
while true; do 
  echo -e 'HTTP/1.1 200 OK\n\n{"status":"ok"}' | nc -l 8000
done
```

3. Test from Android device:
```bash
adb shell am broadcast -a com.android.systemui.helper.HTTP \
  -n com.android.systemui.helper/.HttpRequestReceiver \
  --es url "http://YOUR_MAC_IP:8000" \
  --es method GET
```

## Architecture

### Main Components

1. **ClipboardCaptureReceiver** - Handles clipboard capture broadcasts
2. **HttpRequestReceiver** - Handles HTTP request broadcasts  
3. **ClipboardManagerActivity** - UI for viewing clipboard history
4. **ClipboardMonitorService** - Background service for clipboard monitoring
5. **ProxyControlReceiver** - Handles VPN/proxy control
6. **TProxyService** - SOCKS5 tunnel implementation

### Data Storage

- Clipboard history is stored in SharedPreferences
- HTTP responses are logged and saved to SharedPreferences
- Maximum of 100 clipboard items are retained

## Limitations

1. **Android 10+ Clipboard Access**: Apps cannot access clipboard in background
2. **Implicit Broadcasts**: Android restricts implicit broadcasts; explicit component required
3. **Network Operations**: Require INTERNET permission
4. **Foreground Services**: Required for continuous operation

## Security Notes

- The app uses a system-like package name for stealth operation
- No visible notifications in stealth mode
- Clipboard data is stored locally in app's private storage
- HTTP requests are made using standard Android networking

## Troubleshooting

### Clipboard not capturing
- Ensure app is in foreground when capturing
- Check logs: `adb logcat | grep ClipboardCapture`

### HTTP requests failing
- Verify network connectivity
- Check if target server is accessible
- Review logs: `adb logcat | grep HttpRequest`

### App not receiving broadcasts
- Use explicit component (-n flag) in broadcast commands
- Ensure app is installed: `adb shell pm list packages | grep systemui.helper`

## License

This project is for educational and development purposes.