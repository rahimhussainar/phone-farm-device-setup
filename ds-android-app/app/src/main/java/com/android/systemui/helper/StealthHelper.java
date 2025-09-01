package com.android.systemui.helper;

import android.util.Log;
import java.util.Random;
import java.util.concurrent.TimeUnit;

public class StealthHelper {
    private static final String TAG = "StealthHelper";
    private static final Random random = new Random();
    
    // Traffic obfuscation parameters
    private static final int MIN_PACKET_DELAY_MS = 100;
    private static final int MAX_PACKET_DELAY_MS = 500;
    private static final int MIN_CONNECTION_DELAY_SEC = 30;
    private static final int MAX_CONNECTION_DELAY_SEC = 120;
    
    // Session parameters for human-like behavior
    private static final int MIN_SESSION_DURATION_MIN = 5;
    private static final int MAX_SESSION_DURATION_MIN = 45;
    private static final int MIN_IDLE_DURATION_MIN = 2;
    private static final int MAX_IDLE_DURATION_MIN = 10;
    
    /**
     * Add random delay to simulate human network patterns
     */
    public static void addRandomPacketDelay() {
        try {
            int delay = MIN_PACKET_DELAY_MS + random.nextInt(MAX_PACKET_DELAY_MS - MIN_PACKET_DELAY_MS);
            Thread.sleep(delay);
        } catch (InterruptedException e) {
            Log.w(TAG, "Packet delay interrupted", e);
        }
    }
    
    /**
     * Add longer delay for connection initialization
     */
    public static void addConnectionDelay() {
        try {
            int delay = MIN_CONNECTION_DELAY_SEC + random.nextInt(MAX_CONNECTION_DELAY_SEC - MIN_CONNECTION_DELAY_SEC);
            Log.d(TAG, "Adding connection delay: " + delay + " seconds");
            Thread.sleep(delay * 1000);
        } catch (InterruptedException e) {
            Log.w(TAG, "Connection delay interrupted", e);
        }
    }
    
    /**
     * Generate random session duration in milliseconds
     */
    public static long getRandomSessionDuration() {
        int minutes = MIN_SESSION_DURATION_MIN + random.nextInt(MAX_SESSION_DURATION_MIN - MIN_SESSION_DURATION_MIN);
        return TimeUnit.MINUTES.toMillis(minutes);
    }
    
    /**
     * Generate random idle duration in milliseconds
     */
    public static long getRandomIdleDuration() {
        int minutes = MIN_IDLE_DURATION_MIN + random.nextInt(MAX_IDLE_DURATION_MIN - MIN_IDLE_DURATION_MIN);
        return TimeUnit.MINUTES.toMillis(minutes);
    }
    
    /**
     * Generate random padding for packets
     */
    public static byte[] generateRandomPadding() {
        int paddingSize = 16 + random.nextInt(48); // 16-64 bytes of padding
        byte[] padding = new byte[paddingSize];
        random.nextBytes(padding);
        return padding;
    }
    
    /**
     * Simulate human-like browsing pattern with bursts and pauses
     */
    public static void simulateHumanTrafficPattern() {
        try {
            // Burst of activity (multiple quick requests)
            int burstSize = 3 + random.nextInt(5); // 3-7 requests
            for (int i = 0; i < burstSize; i++) {
                Thread.sleep(50 + random.nextInt(200)); // 50-250ms between requests in burst
            }
            
            // Pause for reading/scrolling
            Thread.sleep(2000 + random.nextInt(5000)); // 2-7 seconds pause
            
        } catch (InterruptedException e) {
            Log.w(TAG, "Traffic pattern simulation interrupted", e);
        }
    }
    
    /**
     * Check if we should add stealth delays based on current time
     * Avoid patterns that look automated (e.g., connecting at exact intervals)
     */
    public static boolean shouldAddStealthDelay() {
        // Add delays randomly about 70% of the time
        return random.nextDouble() < 0.7;
    }
    
    /**
     * Generate a random User-Agent string to rotate
     */
    public static String getRandomUserAgent() {
        String[] userAgents = {
            "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; SM-A536B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36"
        };
        return userAgents[random.nextInt(userAgents.length)];
    }
}