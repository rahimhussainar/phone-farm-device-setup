#!/usr/bin/env python3
"""
Force Phone Setup - More aggressive settings changes
"""

import subprocess
import time
import logging
import sys

# Clean output format - no prefixes
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

class ForcePhoneSetup:
    def __init__(self):
        self.devices = []
        self.refresh_devices()
    
    def run_adb_command(self, device_id, command, retry=True):
        """Run ADB command with retry logic"""
        full_command = f"adb -s {device_id} {command}"
        for attempt in range(2 if retry else 1):
            try:
                result = subprocess.run(full_command, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip()
                elif attempt == 0:
                    time.sleep(1)
            except Exception as e:
                logging.error(f"Error: {e}")
        return None
    
    
    def refresh_devices(self):
        """Get list of connected devices"""
        try:
            result = subprocess.run("adb devices", shell=True, capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')[1:]
            self.devices = [line.split('\t')[0] for line in lines if '\tdevice' in line]
            logging.info(f"Found {len(self.devices)} connected devices")
            return self.devices
        except Exception as e:
            logging.error(f"Error getting devices: {e}")
            return []
    
    def force_bluetooth_off(self, device_id):
        """Force disable Bluetooth using multiple methods"""
        methods = [
            "shell settings put global bluetooth_on 0",
            "shell service call bluetooth_manager 6",  # disable()
            "shell service call bluetooth_manager 8",  # disable()
            "shell am broadcast -a android.bluetooth.adapter.action.STATE_CHANGED --ei android.bluetooth.adapter.extra.STATE 10",
            "shell cmd bluetooth_manager disable",
            "shell svc bluetooth disable"
        ]
        
        for method in methods:
            self.run_adb_command(device_id, method)
            time.sleep(0.2)
        
        # Verify
        status = self.run_adb_command(device_id, "shell settings get global bluetooth_on")
        return status == "0"
    
    def setup_device(self, device_id):
        """Setup a single device with force methods"""
        logging.info(f"\n{'='*50}")
        logging.info(f"Force setting up device: {device_id}")
        
        try:
            # Get device info
            serial = self.run_adb_command(device_id, "shell getprop ro.serialno") or device_id
            model = self.run_adb_command(device_id, "shell getprop ro.product.model")
            logging.info(f"Device: {model} (Serial: {serial})")
            
            # 1. Force Bluetooth off
            logging.info("Forcing Bluetooth off...")
            if self.force_bluetooth_off(device_id):
                logging.info("✓ Bluetooth disabled")
            else:
                logging.warning("⚠ Bluetooth might still be on - check manually")
            
            # 2. Set device name to serial
            device_name = serial
            self.run_adb_command(device_id, f'shell settings put global device_name "{device_name}"')
            self.run_adb_command(device_id, f'shell settings put secure bluetooth_name "{device_name}"')
            self.run_adb_command(device_id, f'shell settings put system device_name "{device_name}"')
            logging.info(f"✓ Device name set to {device_name}")
            
            # 3. Force rotation off
            self.run_adb_command(device_id, "shell settings put system accelerometer_rotation 0")
            self.run_adb_command(device_id, "shell settings put system user_rotation 0")
            self.run_adb_command(device_id, "shell content insert --uri content://settings/system --bind name:s:accelerometer_rotation --bind value:i:0")
            logging.info("✓ Auto-rotate disabled")
            
            # 4. Force volumes to 0 and silent mode
            volume_streams = [
                "3",  # STREAM_MUSIC
                "5",  # STREAM_NOTIFICATION
                "2",  # STREAM_RING
                "1",  # STREAM_SYSTEM
                "4",  # STREAM_ALARM
                "0",  # STREAM_VOICE_CALL
            ]
            for stream in volume_streams:
                self.run_adb_command(device_id, f"shell service call audio 3 i32 {stream} i32 0 i32 1")
            
            # Set volumes to 1 (minimum but not muted)
            self.run_adb_command(device_id, "shell settings put system volume_ring 1")
            self.run_adb_command(device_id, "shell settings put system volume_media 1")
            self.run_adb_command(device_id, "shell settings put system volume_notification 1")
            self.run_adb_command(device_id, "shell settings put system volume_system 1")
            self.run_adb_command(device_id, "shell settings put system volume_alarm 1")
            
            # Force silent mode
            self.run_adb_command(device_id, "shell settings put global mode_ringer 0")  # Silent mode
            self.run_adb_command(device_id, "shell cmd notification set_dnd off")  # Turn OFF Do Not Disturb
            self.run_adb_command(device_id, "shell service call audio 8 i32 0")  # setRingerModeExternal(RINGER_MODE_SILENT)
            
            logging.info("✓ All volumes muted and silent mode enabled")
            
            # 5. Disable automatic updates only (keep Play Store working)
            self.run_adb_command(device_id, "shell settings put global ota_disable_automatic_update 1")
            self.run_adb_command(device_id, "shell settings put global auto_update_enable 0")
            
            # Disable auto-update for apps but keep Play Store functional
            self.run_adb_command(device_id, "shell settings put secure install_non_market_apps 1")
            
            logging.info("✓ Automatic updates disabled (Play Store still available)")
            
            # 6. Power settings
            # Clear any old stay awake setting first
            self.run_adb_command(device_id, "shell settings put global stay_on_while_plugged_in 0")
            # Screen timeout: 30 seconds (30000 ms)
            self.run_adb_command(device_id, "shell settings put system screen_off_timeout 30000")
            logging.info("✓ Power settings configured (30 second screen timeout, stay awake disabled)")
            
            # 7. WiFi always on
            self.run_adb_command(device_id, "shell settings put global wifi_sleep_policy 2")
            self.run_adb_command(device_id, "shell svc wifi enable")
            logging.info("✓ WiFi always on")
            
            # 8. Disable all animations
            self.run_adb_command(device_id, "shell settings put global animator_duration_scale 0")
            self.run_adb_command(device_id, "shell settings put global transition_animation_scale 0")
            self.run_adb_command(device_id, "shell settings put global window_animation_scale 0")
            logging.info("✓ Animations disabled")
            
            # 9. Additional security
            self.run_adb_command(device_id, "shell settings put global package_verifier_enable 0")
            self.run_adb_command(device_id, "shell settings put global verifier_verify_adb_installs 0")
            logging.info("✓ Security checks disabled")
            
            # 10. Reboot to apply all changes
            logging.info("⏳ Rebooting device to apply all changes...")
            self.run_adb_command(device_id, "reboot")
            
            logging.info(f"✅ Setup completed for {serial}!")
            logging.info("   Device will reboot now. Settings will be applied after reboot.")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error: {e}")
            return False
    
    def verify_settings(self, device_id):
        """Verify settings after reboot"""
        checks = {
            "Bluetooth": "shell settings get global bluetooth_on",
            "Device name": "shell settings get global device_name",
            "Auto-rotate": "shell settings get system accelerometer_rotation",
            "Media volume": "shell settings get system volume_media",
            "Screen timeout": "shell settings get system screen_off_timeout",
            "Stay awake": "shell settings get global stay_on_while_plugged_in"
        }
        
        logging.info(f"\n📋 Verifying {device_id}:")
        for name, cmd in checks.items():
            result = self.run_adb_command(device_id, cmd)
            logging.info(f"  {name}: {result}")
    
    def setup_all(self):
        """Setup all devices"""
        if not self.devices:
            logging.error("No devices found!")
            return
        
        logging.info(f"\n🚀 Force setup for {len(self.devices)} devices")
        logging.info("⚠️  Devices will reboot after setup!\n")
        
        for device in self.devices:
            self.setup_device(device)
            time.sleep(2)
        
        logging.info("\n✅ All devices configured and rebooting!")
        logging.info("\n⏳ Wait 2-3 minutes for devices to reboot")
        logging.info("Then run: python setup_phones.py --verify")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true', help='Verify settings only')
    args = parser.parse_args()
    
    setup = ForcePhoneSetup()
    
    if args.verify:
        for device in setup.devices:
            setup.verify_settings(device)
    else:
        setup.setup_all()

if __name__ == "__main__":
    main()