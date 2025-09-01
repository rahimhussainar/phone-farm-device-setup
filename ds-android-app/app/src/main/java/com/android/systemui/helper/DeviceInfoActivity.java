package com.android.systemui.helper;

import android.app.Activity;
import android.app.ActivityManager;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.pm.PackageManager;
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
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.InputStreamReader;
import java.io.RandomAccessFile;
import java.net.NetworkInterface;
import java.text.DecimalFormat;
import java.util.Collections;
import java.util.List;

public class DeviceInfoActivity extends Activity {
    
    private ImageView back_button;
    private TextView device_model, device_manufacturer, device_serial, android_version;
    private TextView sdk_version, security_patch, build_number, bootloader;
    private TextView processor, cpu_cores, ram_info, storage_info;
    private TextView ip_address, mac_address, wifi_ssid;
    private TextView proxy_status, proxy_host, proxy_type;
    private TextView screen_resolution, screen_density, screen_size;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_device_info);
        
        initializeViews();
        loadDeviceInfo();
        setupClickListeners();
    }
    
    private void initializeViews() {
        back_button = findViewById(R.id.back_button);
        
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
        wifi_ssid = findViewById(R.id.wifi_ssid);
        proxy_status = findViewById(R.id.proxy_status);
        proxy_host = findViewById(R.id.proxy_host);
        proxy_type = findViewById(R.id.proxy_type);
        
        // Display Information
        screen_resolution = findViewById(R.id.screen_resolution);
        screen_density = findViewById(R.id.screen_density);
        screen_size = findViewById(R.id.screen_size);
    }
    
    private void setupClickListeners() {
        back_button.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                finish();
            }
        });
        
        // Make copyable fields clickable
        device_model.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                copyToClipboard("Device Model", device_model.getText().toString());
            }
        });
        
        device_serial.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                copyToClipboard("Serial Number", device_serial.getText().toString());
            }
        });
        
        build_number.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                copyToClipboard("Build Number", build_number.getText().toString());
            }
        });
        
        ip_address.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                copyToClipboard("IP Address", ip_address.getText().toString());
            }
        });
    }
    
    private void loadDeviceInfo() {
        // Device Overview
        device_model.setText(Build.MODEL);
        device_manufacturer.setText(Build.MANUFACTURER);
        device_serial.setText(getDeviceSerial());
        android_version.setText(Build.VERSION.RELEASE + " (" + getAndroidVersionName() + ")");
        
        // System Information
        sdk_version.setText("API " + Build.VERSION.SDK_INT);
        security_patch.setText(Build.VERSION.SECURITY_PATCH);
        build_number.setText(Build.DISPLAY);
        bootloader.setText(Build.BOOTLOADER);
        
        // Hardware Information
        processor.setText(getProcessorInfo());
        cpu_cores.setText(String.valueOf(Runtime.getRuntime().availableProcessors()));
        ram_info.setText(getRAMInfo());
        storage_info.setText(getStorageInfo());
        
        // Network Information
        ip_address.setText(getIPAddress());
        mac_address.setText(getMACAddress());
        wifi_ssid.setText(getNetworkStatus());
        
        // Proxy Information
        loadProxyInfo();
        
        // Display Information
        loadDisplayInfo();
    }
    
    private String getDeviceSerial() {
        try {
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
    
    private String getAndroidVersionName() {
        switch (Build.VERSION.SDK_INT) {
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
            
            // Fallback to build info
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
            String available = formatSize(availMemory);
            
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
    
    private String getMACAddress() {
        // Android 6.0+ returns a constant value for privacy
        // The real MAC is no longer accessible to apps
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
                    
                    // Android returns 02:00:00:00:00:00 for privacy
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
                // Check if our VPN service is running
                android.app.ActivityManager activityManager = (android.app.ActivityManager) getSystemService(Context.ACTIVITY_SERVICE);
                for (android.app.ActivityManager.RunningServiceInfo service : activityManager.getRunningServices(Integer.MAX_VALUE)) {
                    if (TProxyService.class.getName().equals(service.service.getClassName())) {
                        // Read proxy config from shared preferences
                        android.content.SharedPreferences prefs = getSharedPreferences("TProxySettings", MODE_PRIVATE);
                        String vpnHost = prefs.getString("proxy_host", "");
                        String vpnPort = prefs.getString("proxy_port", "");
                        
                        // Only show VPN proxy if it's not localhost
                        if (!vpnHost.isEmpty() && !vpnHost.equals("127.0.0.1") && !vpnHost.equals("localhost")) {
                            proxyEnabled = true;
                            activeHost = vpnHost;
                            if (!vpnPort.isEmpty()) {
                                activeHost += ":" + vpnPort;
                            }
                            activeType = "SOCKS5 (VPN)";
                        }
                        break;
                    }
                }
            } catch (Exception e) {
                // Ignore VPN check errors
            }
            
            // Update UI
            proxy_status.setText(proxyEnabled ? "Enabled" : "Disabled");
            proxy_status.setTextColor(getResources().getColor(proxyEnabled ? R.color.success_green : R.color.text_secondary));
            proxy_host.setText(activeHost);
            proxy_type.setText(activeType);
            
        } catch (Exception e) {
            e.printStackTrace();
            proxy_status.setText("Unknown");
            proxy_host.setText("Error");
            proxy_type.setText("Error");
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
            screen_resolution.setText(width + " x " + height);
            
            // Density
            int density = metrics.densityDpi;
            String densityBucket = getDensityBucket(density);
            screen_density.setText(density + " dpi (" + densityBucket + ")");
            
            // Screen size
            float widthInches = width / (float) density;
            float heightInches = height / (float) density;
            double diagonalInches = Math.sqrt(Math.pow(widthInches, 2) + Math.pow(heightInches, 2));
            DecimalFormat df = new DecimalFormat("#.#");
            screen_size.setText(df.format(diagonalInches) + " inches");
            
        } catch (Exception e) {
            screen_resolution.setText("Unknown");
            screen_density.setText("Unknown");
            screen_size.setText("Unknown");
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
}