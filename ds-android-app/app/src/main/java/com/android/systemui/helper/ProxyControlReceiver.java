package com.android.systemui.helper;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.net.VpnService;
import android.util.Log;

public class ProxyControlReceiver extends BroadcastReceiver {
    private static final String TAG = "ProxyControlReceiver";
    public static final String ACTION_PROXY_START = "com.android.systemui.helper.START";
    public static final String ACTION_PROXY_STOP = "com.android.systemui.helper.STOP";
    public static final String ACTION_PROXY_CONFIG = "com.android.systemui.helper.CONFIG";
    
    // Config extras keys
    public static final String EXTRA_PROXY_ADDRESS = "proxy_address";
    public static final String EXTRA_PROXY_PORT = "proxy_port";
    public static final String EXTRA_PROXY_USERNAME = "proxy_username";
    public static final String EXTRA_PROXY_PASSWORD = "proxy_password";
    
    @Override
    public void onReceive(Context context, Intent intent) {
        String action = intent.getAction();
        Log.d(TAG, "Received broadcast: " + action);
        
        if (ACTION_PROXY_START.equals(action)) {
            // Check VPN permission first
            Intent vpnIntent = VpnService.prepare(context);
            if (vpnIntent == null) {
                // Permission already granted, start service
                Intent serviceIntent = new Intent(context, TProxyService.class);
                serviceIntent.setAction(TProxyService.ACTION_CONNECT);
                context.startService(serviceIntent);
                
                // Update preferences
                Preferences prefs = new Preferences(context);
                prefs.setEnable(true);
                
                // Send broadcast to update UI
                Intent updateIntent = new Intent("com.android.systemui.helper.UPDATE_UI");
                updateIntent.setPackage(context.getPackageName());
                context.sendBroadcast(updateIntent);
            } else {
                // Need to request permission through UI
                Intent mainIntent = new Intent(context, MainActivity.class);
                mainIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                mainIntent.putExtra("auto_connect", true);
                context.startActivity(mainIntent);
            }
        } else if (ACTION_PROXY_STOP.equals(action)) {
            // Update preferences first
            Preferences prefs = new Preferences(context);
            prefs.setEnable(false);
            
            // Stop the service
            Intent serviceIntent = new Intent(context, TProxyService.class);
            serviceIntent.setAction(TProxyService.ACTION_DISCONNECT);
            context.startService(serviceIntent);
            
            // Also explicitly stop the service
            context.stopService(new Intent(context, TProxyService.class));
            
            // Send broadcast to update UI
            Intent updateIntent = new Intent("com.android.systemui.helper.UPDATE_UI");
            updateIntent.setPackage(context.getPackageName());
            context.sendBroadcast(updateIntent);
        } else if (ACTION_PROXY_CONFIG.equals(action)) {
            // Handle proxy configuration change
            Preferences prefs = new Preferences(context);
            boolean configChanged = false;
            
            // Update proxy address if provided
            if (intent.hasExtra(EXTRA_PROXY_ADDRESS)) {
                String address = intent.getStringExtra(EXTRA_PROXY_ADDRESS);
                if (address != null && !address.isEmpty()) {
                    prefs.setSocksAddress(address);
                    configChanged = true;
                    Log.d(TAG, "Updated proxy address: " + address);
                }
            }
            
            // Update proxy port if provided
            if (intent.hasExtra(EXTRA_PROXY_PORT)) {
                int port = intent.getIntExtra(EXTRA_PROXY_PORT, -1);
                if (port > 0 && port <= 65535) {
                    prefs.setSocksPort(port);
                    configChanged = true;
                    Log.d(TAG, "Updated proxy port: " + port);
                }
            }
            
            // Update proxy username if provided
            if (intent.hasExtra(EXTRA_PROXY_USERNAME)) {
                String username = intent.getStringExtra(EXTRA_PROXY_USERNAME);
                if (username != null) {
                    prefs.setSocksUsername(username);
                    configChanged = true;
                    Log.d(TAG, "Updated proxy username: " + username);
                }
            }
            
            // Update proxy password if provided
            if (intent.hasExtra(EXTRA_PROXY_PASSWORD)) {
                String password = intent.getStringExtra(EXTRA_PROXY_PASSWORD);
                if (password != null) {
                    prefs.setSocksPassword(password);
                    configChanged = true;
                    Log.d(TAG, "Updated proxy password");
                }
            }
            
            if (configChanged) {
                // If proxy is currently running, restart it with new config
                if (prefs.getEnable()) {
                    // Stop current connection
                    Intent stopIntent = new Intent(context, TProxyService.class);
                    stopIntent.setAction(TProxyService.ACTION_DISCONNECT);
                    context.startService(stopIntent);
                    
                    // Small delay then reconnect with new settings
                    try {
                        Thread.sleep(500);
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    }
                    
                    // Reconnect with new settings
                    Intent startIntent = new Intent(context, TProxyService.class);
                    startIntent.setAction(TProxyService.ACTION_CONNECT);
                    context.startService(startIntent);
                    
                    Log.d(TAG, "Proxy restarted with new config");
                } else {
                    Log.d(TAG, "Proxy config updated");
                }
                
                // Send broadcast to update UI
                Intent updateIntent = new Intent("com.android.systemui.helper.UPDATE_UI");
                updateIntent.setPackage(context.getPackageName());
                context.sendBroadcast(updateIntent);
            } else {
                Log.w(TAG, "No valid config parameters provided");
            }
        }
    }
}