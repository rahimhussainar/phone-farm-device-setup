package com.android.systemui.helper;

import android.app.Activity;
import android.app.ActivityManager;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.net.wifi.WifiInfo;
import android.net.wifi.WifiManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.StatFs;
import android.util.DisplayMetrics;
import android.view.Display;
import android.view.View;
import android.view.WindowManager;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import java.io.BufferedReader;
import java.io.FileReader;
import java.net.NetworkInterface;
import java.text.DecimalFormat;
import java.util.Collections;
import java.util.List;

public class DashboardActivity extends Activity implements View.OnClickListener {
    
    private LinearLayout tool_proxy;
    private LinearLayout tool_clipboard;
    private LinearLayout tool_more;
    
    // Device Overview
    private TextView device_model, device_manufacturer, device_serial, android_version;
    
    // System Information
    private TextView sdk_version, security_patch, build_number, bootloader;
    
    // Hardware Information
    private TextView processor, cpu_cores, ram_info, storage_info;
    
    // Network Information
    private TextView ip_address, mac_address, network_status;
    
    // Proxy Information
    private TextView proxy_status, proxy_type, proxy_host;
    
    // Display Information
    private TextView screen_resolution, screen_density, screen_size;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_dashboard);
        
        // Initialize views
        tool_proxy = findViewById(R.id.tool_proxy);
        tool_clipboard = findViewById(R.id.tool_clipboard);
        tool_more = findViewById(R.id.tool_more);
        
        // Device Overview
        device_model = findViewById(R.id.device_model);
        device_manufacturer = findViewById(R.id.device_manufacturer);
        device_serial = findViewById(R.id.device_serial);
        android_version = findViewById(R.id.android_version);
        
        // System Information
        sdk_version = findViewById(R.id.sdk_version);
        security_patch = findViewById(R.id.security_patch);
        build_number = findViewById(R.id.build_number);
        bootloader = findViewById(R.id.bootloader);
        
        // Hardware Information
        processor = findViewById(R.id.processor);
        cpu_cores = findViewById(R.id.cpu_cores);
        ram_info = findViewById(R.id.ram_info);
        storage_info = findViewById(R.id.storage_info);
        
        // Network Information
        ip_address = findViewById(R.id.ip_address);
        mac_address = findViewById(R.id.mac_address);
        network_status = findViewById(R.id.network_status);
        
        // Proxy Information
        proxy_status = findViewById(R.id.proxy_status);
        proxy_type = findViewById(R.id.proxy_type);
        proxy_host = findViewById(R.id.proxy_host);
        
        // Display Information
        screen_resolution = findViewById(R.id.screen_resolution);
        screen_density = findViewById(R.id.screen_density);
        screen_size = findViewById(R.id.screen_size);
        
        // Set click listeners
        tool_proxy.setOnClickListener(this);
        tool_clipboard.setOnClickListener(this);
        tool_more.setOnClickListener(this);
        
        // Add click listeners for copyable fields
        if (device_serial != null) {
            device_serial.setOnClickListener(v -> copyToClipboard("Device Serial", device_serial.getText().toString()));
        }
        if (ip_address != null) {
            ip_address.setOnClickListener(v -> copyToClipboard("IP Address", ip_address.getText().toString()));
        }
        if (build_number != null) {
            build_number.setOnClickListener(v -> copyToClipboard("Build Number", build_number.getText().toString()));
        }
        
        // Update device info
        updateDeviceInfo();
        
        // Start clipboard monitoring service
        Intent serviceIntent = new Intent(this, ClipboardMonitorService.class);
        startService(serviceIntent);
    }
    
    @Override
    protected void onResume() {
        super.onResume();
        // Refresh device info when returning to dashboard
        updateDeviceInfo();
    }
    
    @Override
    public void onClick(View view) {
        if (view == tool_proxy) {
            // Launch proxy activity (current MainActivity)
            Intent intent = new Intent(this, MainActivity.class);
            startActivity(intent);
        } else if (view == tool_clipboard) {
            // Launch clipboard manager
            Intent intent = new Intent(this, ClipboardManagerActivity.class);
            startActivity(intent);
        } else if (view == tool_more) {
            Toast.makeText(this, "More tools coming soon", Toast.LENGTH_SHORT).show();
        }
    }
    
    private void updateDeviceInfo() {
        // Device Overview
        if (device_model != null) device_model.setText(Build.MODEL);
        if (device_manufacturer != null) device_manufacturer.setText(Build.MANUFACTURER);
        if (device_serial != null) device_serial.setText(getDeviceSerial());
        if (android_version != null) android_version.setText(Build.VERSION.RELEASE + " (" + getAndroidVersionName() + ")");
        
        // System Information
        if (sdk_version != null) sdk_version.setText("API " + Build.VERSION.SDK_INT);
        if (security_patch != null) security_patch.setText(Build.VERSION.SECURITY_PATCH);
        if (build_number != null) build_number.setText(Build.DISPLAY);
        if (bootloader != null) bootloader.setText(Build.BOOTLOADER);
        
        // Hardware Information
        if (processor != null) processor.setText(getProcessorInfo());
        if (cpu_cores != null) cpu_cores.setText(String.valueOf(Runtime.getRuntime().availableProcessors()));
        if (ram_info != null) ram_info.setText(getRAMInfo());
        if (storage_info != null) storage_info.setText(getStorageInfo());
        
        // Network Information
        if (ip_address != null) ip_address.setText(getIPAddress());
        if (mac_address != null) mac_address.setText(getMACAddress());
        if (network_status != null) network_status.setText(getNetworkStatus());
        
        // Proxy Information
        loadProxyInfo();
        
        // Display Information
        loadDisplayInfo();
    }
    
    private String getDeviceSerial() {
        try {
            // Try getting Android ID
            String androidId = android.provider.Settings.Secure.getString(
                getContentResolver(), 
                android.provider.Settings.Secure.ANDROID_ID
            );
            
            // Special handling for known device
            if (androidId != null && androidId.equals("3891763675bf1b6d")) {
                return "R5CY61RZ0HR";
            }
            
            if (androidId != null && !androidId.isEmpty()) {
                return androidId.substring(0, Math.min(androidId.length(), 11)).toUpperCase();
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return "Unknown";
    }
    
    private String getIPAddress() {
        try {
            List<NetworkInterface> interfaces = Collections.list(NetworkInterface.getNetworkInterfaces());
            for (NetworkInterface intf : interfaces) {
                List<java.net.InetAddress> addrs = Collections.list(intf.getInetAddresses());
                for (java.net.InetAddress addr : addrs) {
                    if (!addr.isLoopbackAddress()) {
                        String sAddr = addr.getHostAddress();
                        boolean isIPv4 = sAddr.indexOf(':') < 0;
                        if (isIPv4) {
                            return sAddr;
                        }
                    }
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return "127.0.0.1";
    }
    
    private String getAndroidVersionName() {
        switch (Build.VERSION.SDK_INT) {
            case 35: return "Android 15";
            case 34: return "Android 14";
            case 33: return "Android 13";
            case 32: return "Android 12L";
            case 31: return "Android 12";
            case 30: return "Android 11";
            case 29: return "Android 10";
            case 28: return "Android 9";
            case 27: return "Android 8.1";
            case 26: return "Android 8.0";
            default: return "API " + Build.VERSION.SDK_INT;
        }
    }
    
    private String getProcessorInfo() {
        try {
            BufferedReader br = new BufferedReader(new FileReader("/proc/cpuinfo"));
            String line;
            while ((line = br.readLine()) != null) {
                if (line.startsWith("Hardware")) {
                    return line.split(":")[1].trim();
                }
            }
            br.close();
            return Build.HARDWARE;
        } catch (Exception e) {
            return Build.HARDWARE;
        }
    }
    
    private String getRAMInfo() {
        try {
            ActivityManager actManager = (ActivityManager) getSystemService(Context.ACTIVITY_SERVICE);
            ActivityManager.MemoryInfo memInfo = new ActivityManager.MemoryInfo();
            actManager.getMemoryInfo(memInfo);
            
            long totalMemory = memInfo.totalMem;
            long availMemory = memInfo.availMem;
            long usedMemory = totalMemory - availMemory;
            
            String total = formatSize(totalMemory);
            String used = formatSize(usedMemory);
            
            return used + " / " + total;
        } catch (Exception e) {
            return "Unknown";
        }
    }
    
    private String getStorageInfo() {
        try {
            StatFs stat = new StatFs(Environment.getDataDirectory().getPath());
            long blockSize = stat.getBlockSizeLong();
            long totalBlocks = stat.getBlockCountLong();
            long availableBlocks = stat.getAvailableBlocksLong();
            
            long totalStorage = totalBlocks * blockSize;
            long availableStorage = availableBlocks * blockSize;
            long usedStorage = totalStorage - availableStorage;
            
            String total = formatSize(totalStorage);
            String used = formatSize(usedStorage);
            
            return used + " / " + total;
        } catch (Exception e) {
            return "Unknown";
        }
    }
    
    private String getMACAddress() {
        try {
            List<NetworkInterface> interfaces = Collections.list(NetworkInterface.getNetworkInterfaces());
            for (NetworkInterface intf : interfaces) {
                if (intf.getName().equalsIgnoreCase("wlan0")) {
                    byte[] mac = intf.getHardwareAddress();
                    if (mac == null) return "Protected (Android 6.0+)";
                    
                    StringBuilder buf = new StringBuilder();
                    for (byte aMac : mac) {
                        buf.append(String.format("%02X:", aMac));
                    }
                    if (buf.length() > 0) {
                        buf.deleteCharAt(buf.length() - 1);
                    }
                    
                    if (buf.toString().equals("02:00:00:00:00:00")) {
                        return "Protected (Android 6.0+)";
                    }
                    
                    return buf.toString();
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return "Protected (Android 6.0+)";
    }
    
    private String formatSize(long size) {
        String[] units = {"B", "KB", "MB", "GB", "TB"};
        int unitIndex = 0;
        double sizeDouble = size;
        
        while (sizeDouble >= 1024 && unitIndex < units.length - 1) {
            sizeDouble /= 1024;
            unitIndex++;
        }
        
        DecimalFormat df = new DecimalFormat("#.##");
        return df.format(sizeDouble) + " " + units[unitIndex];
    }
    
    private void copyToClipboard(String label, String text) {
        ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        ClipData clip = ClipData.newPlainText(label, text);
        clipboard.setPrimaryClip(clip);
        Toast.makeText(this, label + " copied to clipboard", Toast.LENGTH_SHORT).show();
    }
    
    private String getNetworkStatus() {
        try {
            ConnectivityManager cm = (ConnectivityManager) getSystemService(Context.CONNECTIVITY_SERVICE);
            NetworkInfo activeNetwork = cm.getActiveNetworkInfo();
            
            if (activeNetwork != null && activeNetwork.isConnected()) {
                // For WiFi, try to get SSID
                if (activeNetwork.getType() == ConnectivityManager.TYPE_WIFI) {
                    WifiManager wifiManager = (WifiManager) getApplicationContext().getSystemService(Context.WIFI_SERVICE);
                    WifiInfo wifiInfo = wifiManager.getConnectionInfo();
                    String ssid = wifiInfo.getSSID();
                    if (ssid != null && !ssid.equals("<unknown ssid>") && !ssid.isEmpty()) {
                        return ssid.replace("\"", "");
                    }
                }
                return "Connected";
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return "Not Connected";
    }
    
    private void loadProxyInfo() {
        try {
            // Check system proxy settings
            String httpHost = System.getProperty("http.proxyHost");
            String httpPort = System.getProperty("http.proxyPort");
            
            // Also check HTTPS proxy
            String httpsHost = System.getProperty("https.proxyHost");
            String httpsPort = System.getProperty("https.proxyPort");
            
            // Check Android's global proxy settings
            String globalHost = android.provider.Settings.Global.getString(
                getContentResolver(), 
                android.provider.Settings.Global.HTTP_PROXY
            );
            
            boolean proxyEnabled = false;
            String activeHost = "None";
            String activeType = "None";
            
            // Check if any proxy is configured
            if (httpHost != null && !httpHost.isEmpty()) {
                proxyEnabled = true;
                activeHost = httpHost;
                if (httpPort != null && !httpPort.isEmpty()) {
                    activeHost += ":" + httpPort;
                }
                activeType = "HTTP";
            } else if (httpsHost != null && !httpsHost.isEmpty()) {
                proxyEnabled = true;
                activeHost = httpsHost;
                if (httpsPort != null && !httpsPort.isEmpty()) {
                    activeHost += ":" + httpsPort;
                }
                activeType = "HTTPS";
            } else if (globalHost != null && !globalHost.isEmpty()) {
                proxyEnabled = true;
                activeHost = globalHost;
                activeType = "Global";
            }
            
            // Check for VPN-based proxy (our TProxy service)
            try {
                ActivityManager activityManager = (ActivityManager) getSystemService(Context.ACTIVITY_SERVICE);
                for (ActivityManager.RunningServiceInfo service : activityManager.getRunningServices(Integer.MAX_VALUE)) {
                    if (TProxyService.class.getName().equals(service.service.getClassName())) {
                        // If the VPN service is running, proxy is connected
                        proxyEnabled = true;
                        SharedPreferences prefs = getSharedPreferences("ProxySettings", MODE_PRIVATE);
                        
                        // Get the actual proxy server details from ProxySettings (same as MainActivity uses)
                        String proxyIp = prefs.getString("proxy_ip", "");
                        String proxyPort = prefs.getString("proxy_port", "");
                        
                        if (!proxyIp.isEmpty()) {
                            activeHost = proxyIp;
                            if (!proxyPort.isEmpty()) {
                                activeHost += ":" + proxyPort;
                            }
                        } else {
                            activeHost = "Configuration Error";
                        }
                        activeType = "SOCKS5";
                        break;
                    }
                }
            } catch (Exception e) {
                // Ignore VPN check errors
            }
            
            // Update UI
            if (proxy_status != null) {
                proxy_status.setText(proxyEnabled ? "Connected" : "Disconnected");
                proxy_status.setTextColor(getResources().getColor(proxyEnabled ? R.color.forest_green : R.color.text_secondary));
            }
            if (proxy_host != null) proxy_host.setText(activeHost);
            if (proxy_type != null) proxy_type.setText(activeType);
            
        } catch (Exception e) {
            e.printStackTrace();
            if (proxy_status != null) proxy_status.setText("Unknown");
            if (proxy_host != null) proxy_host.setText("Error");
            if (proxy_type != null) proxy_type.setText("Error");
        }
    }
    
    private void loadDisplayInfo() {
        try {
            WindowManager wm = (WindowManager) getSystemService(Context.WINDOW_SERVICE);
            Display display = wm.getDefaultDisplay();
            DisplayMetrics metrics = new DisplayMetrics();
            display.getRealMetrics(metrics);
            
            // Resolution
            int width = metrics.widthPixels;
            int height = metrics.heightPixels;
            if (screen_resolution != null) screen_resolution.setText(width + " x " + height);
            
            // Density
            int density = metrics.densityDpi;
            String densityBucket = getDensityBucket(density);
            if (screen_density != null) screen_density.setText(density + " dpi (" + densityBucket + ")");
            
            // Screen size
            float widthInches = width / (float) density;
            float heightInches = height / (float) density;
            double diagonalInches = Math.sqrt(Math.pow(widthInches, 2) + Math.pow(heightInches, 2));
            DecimalFormat df = new DecimalFormat("#.#");
            if (screen_size != null) screen_size.setText(df.format(diagonalInches) + " inches");
            
        } catch (Exception e) {
            if (screen_resolution != null) screen_resolution.setText("Unknown");
            if (screen_density != null) screen_density.setText("Unknown");
            if (screen_size != null) screen_size.setText("Unknown");
        }
    }
    
    private String getDensityBucket(int density) {
        if (density <= 120) return "ldpi";
        else if (density <= 160) return "mdpi";
        else if (density <= 240) return "hdpi";
        else if (density <= 320) return "xhdpi";
        else if (density <= 480) return "xxhdpi";
        else if (density <= 640) return "xxxhdpi";
        else return "xxxhdpi+";
    }
}