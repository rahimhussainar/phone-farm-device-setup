package com.android.systemui.helper;

import android.os.AsyncTask;
import android.util.Log;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.net.SocketTimeoutException;
import java.io.OutputStream;
import java.io.InputStream;

public class ProxyChecker {
    private static final String TAG = "ProxyChecker";
    private static final int TIMEOUT = 3000; // 3 seconds timeout
    
    public interface ProxyCheckCallback {
        void onCheckComplete(boolean isValid, String message);
    }
    
    public static void checkProxy(String address, int port, String username, String password, ProxyCheckCallback callback) {
        new ProxyCheckTask(callback).execute(address, String.valueOf(port), username, password);
    }
    
    private static class ProxyCheckTask extends AsyncTask<String, Void, ProxyCheckResult> {
        private ProxyCheckCallback callback;
        
        ProxyCheckTask(ProxyCheckCallback callback) {
            this.callback = callback;
        }
        
        @Override
        protected ProxyCheckResult doInBackground(String... params) {
            String address = params[0];
            int port = Integer.parseInt(params[1]);
            String username = params[2];
            String password = params[3];
            
            Socket socket = null;
            try {
                // First, try to connect to the proxy server
                socket = new Socket();
                socket.connect(new InetSocketAddress(address, port), TIMEOUT);
                
                // If we need auth, try SOCKS5 handshake
                if (username != null && !username.isEmpty()) {
                    OutputStream out = socket.getOutputStream();
                    InputStream in = socket.getInputStream();
                    
                    // Send SOCKS5 greeting with username/password auth method
                    byte[] greeting = new byte[]{0x05, 0x01, 0x02}; // Version 5, 1 method, username/password
                    out.write(greeting);
                    out.flush();
                    
                    // Read server response
                    byte[] response = new byte[2];
                    int bytesRead = in.read(response);
                    
                    if (bytesRead == 2 && response[0] == 0x05) {
                        if (response[1] == 0x02) {
                            // Server wants username/password auth
                            // Send username and password
                            byte[] authRequest = buildAuthRequest(username, password);
                            out.write(authRequest);
                            out.flush();
                            
                            // Read auth response
                            byte[] authResponse = new byte[2];
                            bytesRead = in.read(authResponse);
                            
                            if (bytesRead == 2 && authResponse[0] == 0x01 && authResponse[1] == 0x00) {
                                return new ProxyCheckResult(true, "Proxy connected successfully");
                            } else {
                                return new ProxyCheckResult(false, "Authentication failed");
                            }
                        } else if (response[1] == 0x00) {
                            // No auth required
                            return new ProxyCheckResult(true, "Proxy connected (no auth)");
                        } else if (response[1] == (byte)0xFF) {
                            return new ProxyCheckResult(false, "No acceptable auth methods");
                        }
                    }
                }
                
                // If we got here with no username, connection was successful
                return new ProxyCheckResult(true, "Proxy reachable");
                
            } catch (SocketTimeoutException e) {
                return new ProxyCheckResult(false, "Connection timeout");
            } catch (IOException e) {
                String message = e.getMessage();
                if (message != null && message.contains("refused")) {
                    return new ProxyCheckResult(false, "Connection refused");
                } else if (message != null && message.contains("unreachable")) {
                    return new ProxyCheckResult(false, "Host unreachable");
                }
                return new ProxyCheckResult(false, "Connection failed");
            } catch (Exception e) {
                Log.e(TAG, "Proxy check error", e);
                return new ProxyCheckResult(false, "Check failed");
            } finally {
                if (socket != null) {
                    try {
                        socket.close();
                    } catch (IOException e) {
                        // Ignore
                    }
                }
            }
        }
        
        private byte[] buildAuthRequest(String username, String password) {
            byte[] userBytes = username.getBytes();
            byte[] passBytes = password.getBytes();
            
            byte[] authRequest = new byte[3 + userBytes.length + passBytes.length];
            authRequest[0] = 0x01; // Version
            authRequest[1] = (byte) userBytes.length;
            System.arraycopy(userBytes, 0, authRequest, 2, userBytes.length);
            authRequest[2 + userBytes.length] = (byte) passBytes.length;
            System.arraycopy(passBytes, 0, authRequest, 3 + userBytes.length, passBytes.length);
            
            return authRequest;
        }
        
        @Override
        protected void onPostExecute(ProxyCheckResult result) {
            if (callback != null) {
                callback.onCheckComplete(result.isValid, result.message);
            }
        }
    }
    
    private static class ProxyCheckResult {
        boolean isValid;
        String message;
        
        ProxyCheckResult(boolean isValid, String message) {
            this.isValid = isValid;
            this.message = message;
        }
    }
}