#!/usr/bin/env python3
"""
Download Super Proxy App
Opens Play Store link for Super Proxy app
"""

import subprocess
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

class SuperProxyDownloader:
    def __init__(self):
        self.play_store_url = "https://play.google.com/store/apps/details?id=com.scheler.superproxy&hl=en_US"
        self.devices = self.get_devices()
    
    def get_devices(self):
        """Get list of connected devices"""
        try:
            result = subprocess.run("adb devices", shell=True, capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')[1:]
            devices = [line.split('\t')[0] for line in lines if '\tdevice' in line]
            logging.info(f"Found {len(devices)} devices")
            return devices
        except:
            return []
    
    def run_adb(self, device_id, command):
        """Run ADB command"""
        full_command = f"adb -s {device_id} {command}"
        try:
            result = subprocess.run(full_command, shell=True, capture_output=True, text=True)
            return result.stdout.strip()
        except Exception as e:
            logging.error(f"Error: {e}")
            return None
    
    def go_home(self, device_id):
        """Navigate to home screen"""
        logging.info("Going to home screen...")
        self.run_adb(device_id, "shell input keyevent KEYCODE_HOME")
        time.sleep(1.5)
    
    def open_play_store_link(self, device_id):
        """Open Play Store link in browser"""
        logging.info("Opening Super Proxy Play Store page...")
        # Use am start with ACTION_VIEW to open URL
        self.run_adb(device_id, f'shell am start -a android.intent.action.VIEW -d "{self.play_store_url}"')
        logging.info("Waiting 10 seconds for Play Store to load...")
        time.sleep(10)  # Wait for browser/Play Store to load
        
        # Accept terms of service for first time Play Store usage
        logging.info("Accepting Play Store terms of service...")
        self.run_adb(device_id, "shell input tap 600 1040")
        time.sleep(2)  # Wait for terms acceptance to process
    
    def click_install_button(self, device_id):
        """Click the install button in Play Store"""
        logging.info("Clicking Install button...")
        self.run_adb(device_id, "shell input tap 360 530")
        time.sleep(5)  # Wait for installation to start
        
        # Click verify install button
        logging.info("Clicking Verify Install button...")
        self.run_adb(device_id, "shell input tap 360 1460")
        time.sleep(2)  # Wait for verification to process
        
        # Click Continue button
        logging.info("Clicking Continue button...")
        self.run_adb(device_id, "shell input tap 200 1450")
        time.sleep(2)  # Wait for continue to process
    
    def download_for_device(self, device_id):
        """Complete process to open Super Proxy download page"""
        try:
            logging.info(f"\n{'='*50}")
            logging.info(f"Opening Super Proxy download for device: {device_id}")
            logging.info(f"{'='*50}")
            
            # Get device serial for logging
            serial = self.run_adb(device_id, "shell getprop ro.serialno") or device_id
            logging.info(f"Device serial: {serial}")
            
            # Step 1: Go to home screen
            self.go_home(device_id)
            
            # Step 2: Open Play Store link
            self.open_play_store_link(device_id)
            
            # Step 3: Click Install button
            self.click_install_button(device_id)
            
            logging.info(f"✅ Started Super Proxy installation for {serial}")
            logging.info("⏳ App will install in the background...")
            
            return True
            
        except Exception as e:
            logging.error(f"Error opening download page: {e}")
            return False
    
    def download_all_devices(self):
        """Open download page on all connected devices"""
        if not self.devices:
            logging.error("No devices found!")
            return
        
        logging.info(f"\nStarting Super Proxy download for {len(self.devices)} devices")
        
        successful = 0
        failed = 0
        
        for device in self.devices:
            if self.download_for_device(device):
                successful += 1
            else:
                failed += 1
            
            # Small delay between devices
            if device != self.devices[-1]:
                time.sleep(1.5)
        
        logging.info(f"\n{'='*50}")
        logging.info(f"Download Page Opening Complete!")
        logging.info(f"Successful: {successful}")
        logging.info(f"Failed: {failed}")
        logging.info(f"{'='*50}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Download Super Proxy App')
    parser.add_argument('--device', type=str, help='Download on specific device only')
    args = parser.parse_args()
    
    downloader = SuperProxyDownloader()
    
    if args.device:
        downloader.download_for_device(args.device)
    else:
        downloader.download_all_devices()

if __name__ == "__main__":
    main()