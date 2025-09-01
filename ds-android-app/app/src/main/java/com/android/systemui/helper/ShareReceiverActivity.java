package com.android.systemui.helper;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;
import android.widget.Toast;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class ShareReceiverActivity extends Activity {
    private static final String TAG = "ShareReceiverActivity";
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        // Get the intent that started this activity
        Intent intent = getIntent();
        String action = intent.getAction();
        String type = intent.getType();
        
        if (Intent.ACTION_SEND.equals(action) && type != null) {
            if (type.startsWith("text/")) {
                handleSendText(intent);
            }
        } else if (Intent.ACTION_VIEW.equals(action)) {
            handleViewAction(intent);
        } else {
            Log.e(TAG, "Unsupported action: " + action);
            Toast.makeText(this, "Unsupported share action", Toast.LENGTH_SHORT).show();
            finish();
        }
    }
    
    private void handleSendText(Intent intent) {
        // First check for file stream (higher priority)
        Uri uri = intent.getParcelableExtra(Intent.EXTRA_STREAM);
        if (uri != null) {
            Log.d(TAG, "Received file stream URI: " + uri);
            readFileAndProcess(uri);
            return;
        }
        
        // Then check for shared text
        String sharedText = intent.getStringExtra(Intent.EXTRA_TEXT);
        if (sharedText != null) {
            Log.d(TAG, "Received shared text: " + sharedText);
            
            // Check if this is just a title/header (Super Proxy often sends just "Super Proxy Export")
            if (sharedText.trim().equalsIgnoreCase("Super Proxy Export") || 
                sharedText.trim().length() < 30) {
                Log.e(TAG, "Received only title/header, not actual proxy data");
                Toast.makeText(this, "Please share the actual proxy file, not just the export title.\n\nTry using 'Share File' or 'Export' option in Super Proxy.", 
                              Toast.LENGTH_LONG).show();
                finish();
                return;
            }
            
            parseAndApplyProxyConfig(sharedText);
        } else {
            Toast.makeText(this, "No proxy configuration found.\nPlease share a proxy file or configuration text.", 
                          Toast.LENGTH_LONG).show();
            finish();
        }
    }
    
    private void handleViewAction(Intent intent) {
        Uri data = intent.getData();
        if (data != null) {
            readFileAndProcess(data);
        } else {
            Toast.makeText(this, "No file data found", Toast.LENGTH_SHORT).show();
            finish();
        }
    }
    
    private void readFileAndProcess(Uri uri) {
        try {
            InputStream inputStream = getContentResolver().openInputStream(uri);
            BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream));
            StringBuilder stringBuilder = new StringBuilder();
            String line;
            
            while ((line = reader.readLine()) != null) {
                stringBuilder.append(line).append("\n");
            }
            
            reader.close();
            inputStream.close();
            
            String fileContent = stringBuilder.toString();
            Log.d(TAG, "Read file content: " + fileContent);
            parseAndApplyProxyConfig(fileContent);
            
        } catch (Exception e) {
            Log.e(TAG, "Error reading file: " + e.getMessage());
            Toast.makeText(this, "Error reading proxy configuration", Toast.LENGTH_SHORT).show();
            finish();
        }
    }
    
    private void parseAndApplyProxyConfig(String content) {
        Log.d(TAG, "=== Starting proxy parsing ===");
        Log.d(TAG, "Content to parse:\n" + content);
        
        ProxyConfig config = parseProxyUrl(content);
        
        if (config != null) {
            // Show confirmation dialog
            showConfigurationDialog(config);
        } else {
            Toast.makeText(this, "Invalid proxy configuration format", Toast.LENGTH_LONG).show();
            finish();
        }
    }
    
    private ProxyConfig parseProxyUrl(String content) {
        // Remove comments and empty lines
        String[] lines = content.split("\n");
        String proxyLine = null;
        
        Log.d(TAG, "Total lines: " + lines.length);
        for (int i = 0; i < lines.length; i++) {
            String line = lines[i].trim();
            Log.d(TAG, "Line " + i + " (trimmed): [" + line + "]");
            
            // Skip comments and empty lines
            if (line.isEmpty() || line.startsWith("#")) {
                Log.d(TAG, "  -> Skipping (empty or comment)");
                continue;
            }
            // Look for socks5:// or http:// lines
            if (line.startsWith("socks5://") || line.startsWith("http://") || line.startsWith("https://")) {
                Log.d(TAG, "  -> Found proxy line!");
                proxyLine = line;
                break;
            }
        }
        
        if (proxyLine == null) {
            Log.e(TAG, "No proxy URL found in content");
            return null;
        }
        
        // Extract just the URL part (before any quotes or additional text)
        Pattern urlPattern = Pattern.compile("((?:socks5|http|https)://[^\\s\"]+)");
        Matcher urlMatcher = urlPattern.matcher(proxyLine);
        
        if (!urlMatcher.find()) {
            Log.e(TAG, "Could not extract proxy URL from line: " + proxyLine);
            return null;
        }
        
        String proxyUrl = urlMatcher.group(1);
        Log.d(TAG, "Extracted proxy URL: " + proxyUrl);
        
        try {
            // Parse the proxy URL
            // Format: protocol://username:password@host:port
            Pattern pattern = Pattern.compile("(socks5|http|https)://(?:([^:]+):([^@]+)@)?([^:]+):(\\d+)");
            Matcher matcher = pattern.matcher(proxyUrl);
            
            if (matcher.matches()) {
                ProxyConfig config = new ProxyConfig();
                config.protocol = matcher.group(1);
                config.username = matcher.group(2);
                config.password = matcher.group(3);
                config.host = matcher.group(4);
                config.port = Integer.parseInt(matcher.group(5));
                
                // Extract profile name if present
                Pattern profilePattern = Pattern.compile("\"([^\"]+)\"");
                Matcher profileMatcher = profilePattern.matcher(proxyLine);
                if (profileMatcher.find()) {
                    config.profileName = profileMatcher.group(1);
                } else {
                    config.profileName = "Imported Profile";
                }
                
                Log.d(TAG, "Parsed proxy config: " + config.toString());
                return config;
            } else {
                Log.e(TAG, "Proxy URL does not match expected pattern: " + proxyUrl);
            }
        } catch (Exception e) {
            Log.e(TAG, "Error parsing proxy URL: " + e.getMessage());
        }
        
        return null;
    }
    
    private void showConfigurationDialog(final ProxyConfig config) {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("Import Proxy Configuration");
        
        StringBuilder message = new StringBuilder();
        message.append("Profile: ").append(config.profileName).append("\n");
        message.append("Protocol: ").append(config.protocol.toUpperCase()).append("\n");
        message.append("Host: ").append(config.host).append("\n");
        message.append("Port: ").append(config.port).append("\n");
        if (config.username != null && !config.username.isEmpty()) {
            message.append("Username: ").append(config.username).append("\n");
            message.append("Password: ").append(config.password != null ? "***" : "None").append("\n");
        }
        message.append("\nDo you want to apply this configuration?");
        
        builder.setMessage(message.toString());
        
        builder.setPositiveButton("Apply", (dialog, which) -> {
            applyConfiguration(config);
        });
        
        builder.setNegativeButton("Cancel", (dialog, which) -> {
            finish();
        });
        
        builder.setOnCancelListener(dialog -> {
            finish();
        });
        
        builder.show();
    }
    
    private void applyConfiguration(ProxyConfig config) {
        try {
            // Save configuration using Preferences
            Preferences prefs = new Preferences(this);
            
            // First, stop any running proxy connection
            if (prefs.getEnable()) {
                Log.d(TAG, "Stopping existing proxy connection before importing new config");
                prefs.setEnable(false);
                
                // Send disconnect intent to stop the VPN service
                Intent stopIntent = new Intent(this, TProxyService.class);
                stopIntent.setAction(TProxyService.ACTION_DISCONNECT);
                startService(stopIntent);
                
                // Small delay to ensure service stops
                try {
                    Thread.sleep(500);
                } catch (InterruptedException e) {
                    // Ignore
                }
            }
            
            // Set proxy address and port ONLY
            // NOTE: We intentionally do NOT modify DNS settings, checkboxes, or any other configuration
            // Only the proxy server details are imported
            prefs.setSocksAddress(config.host);
            prefs.setSocksPort(config.port);
            
            // Set username and password if provided
            if (config.username != null && !config.username.isEmpty()) {
                prefs.setSocksUsername(config.username);
                prefs.setSocksPassword(config.password != null ? config.password : "");
            } else {
                // Clear authentication if not provided
                prefs.setSocksUsername("");
                prefs.setSocksPassword("");
            }
            
            // DNS settings remain unchanged:
            // - DNS servers (8.8.8.8, etc.) stay as configured
            // - Remote DNS checkbox stays as configured
            // - All other checkboxes stay as configured
            
            // Don't auto-enable, just save the configuration
            // User can enable it manually from the app
            
            // Show success message
            Toast.makeText(this, "Proxy configuration imported successfully!\nPrevious proxy stopped. Click Enable to start with new config.", 
                          Toast.LENGTH_LONG).show();
            
            // Send broadcast to update UI if MainActivity is open
            Intent updateIntent = new Intent("com.android.systemui.helper.UPDATE_UI");
            updateIntent.setPackage(getPackageName());
            sendBroadcast(updateIntent);
            
            // Open MainActivity to show the updated configuration
            Intent mainIntent = new Intent(this, MainActivity.class);
            mainIntent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(mainIntent);
            
            finish();
            
        } catch (Exception e) {
            Log.e(TAG, "Error applying configuration: " + e.getMessage());
            Toast.makeText(this, "Error applying configuration: " + e.getMessage(), 
                          Toast.LENGTH_LONG).show();
            finish();
        }
    }
    
    private static class ProxyConfig {
        String protocol;
        String host;
        int port;
        String username;
        String password;
        String profileName;
        
        @Override
        public String toString() {
            return "ProxyConfig{" +
                    "protocol='" + protocol + '\'' +
                    ", host='" + host + '\'' +
                    ", port=" + port +
                    ", username='" + username + '\'' +
                    ", password='" + (password != null ? "***" : "null") + '\'' +
                    ", profileName='" + profileName + '\'' +
                    '}';
        }
    }
}