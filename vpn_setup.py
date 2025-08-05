#!/usr/bin/env python3
"""
VPN Setup Script
Automates VPN configuration from Google Sheets data
"""

import subprocess
import time
import logging
import sys
import pandas as pd
import os
from google_sheets_helper import GoogleSheetsHelper

# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class VPNSetup:
    DEBUG_MODE = False
    
    @staticmethod
    def setup_logging(debug=False):
        VPNSetup.DEBUG_MODE = debug
        level = logging.DEBUG if debug else logging.INFO
        
        # Custom formatter to remove prefix and add colors
        class ColorFormatter(logging.Formatter):
            def format(self, record):
                if record.levelno == logging.ERROR:
                    return f"{Colors.FAIL}✗ {record.getMessage()}{Colors.ENDC}"
                elif record.levelno == logging.WARNING:
                    return f"{Colors.WARNING}⚠ {record.getMessage()}{Colors.ENDC}"
                elif record.levelno == logging.INFO:
                    return f"{Colors.CYAN}• {record.getMessage()}{Colors.ENDC}"
                else:
                    return record.getMessage()
        
        handler = logging.StreamHandler()
        handler.setFormatter(ColorFormatter())
        logging.root.handlers = []
        logging.root.addHandler(handler)
        logging.root.setLevel(level)
    
    def debug_log(self, message):
        if VPNSetup.DEBUG_MODE:
            logging.info(message)
    
    def __init__(self, sheet_name='VPN/Email Bank'):
        self.package_name = "com.scheler.superproxy"
        # Hardcoded spreadsheet URL
        self.spreadsheet_url = "https://docs.google.com/spreadsheets/d/1XssR8xcKcjZzZuuqy_oTK8wG55WLcQGcqjFWtF29B30/edit?gid=1573003490#gid=1573003490"
        self.spreadsheet_id = self._extract_spreadsheet_id(self.spreadsheet_url)
        self.sheet_name = sheet_name
        self.devices = self.get_devices()
        self.df = None
        self.scrcpy_processes = {}
        self.sheets_helper = GoogleSheetsHelper()
        self.configured_devices = []
        
        # Column mapping for flexible column names
        self.column_mapping = {
            'proxy': ['Proxy', 'VPN', 'VPN Server', 'Server', 'Host'],
            'port': ['Port', 'VPN Port', 'Server Port'],
            'username': ['Username', 'User', 'Login', 'VPN Username'],
            'password': ['Password', 'Pass', 'VPN Password'],
            'status': ['Status', 'State', 'VPN Status'],
            'serial': ['Serial', 'Device Serial', 'Serial Number'],
            'device_assignment': ['Device Assignment', 'Device', 'Assigned Device'],
            'device_location': ['Device Location', 'Location', 'Device Loc']
        }
        
        self.actual_columns = {}
        
        if not self.spreadsheet_id:
            logging.error("Invalid spreadsheet URL!")
            sys.exit(1)
            
        self.load_spreadsheet()
        self.check_existing_vpn_configs()
    
    def _extract_spreadsheet_id(self, url):
        """Extract spreadsheet ID from Google Sheets URL"""
        if '/d/' in url:
            parts = url.split('/d/')
            if len(parts) > 1:
                id_part = parts[1].split('/')[0]
                return id_part
        elif len(url) == 44:
            return url
        return None
    
    def _find_column(self, df_columns, column_key):
        """Find the actual column name in the dataframe"""
        possible_names = self.column_mapping.get(column_key, [])
        for col in df_columns:
            if col in possible_names:
                return col
        return None
    
    def _map_columns(self):
        """Map the actual column names to our expected names"""
        df_columns = self.df.columns.tolist()
        
        for key in self.column_mapping:
            actual_col = self._find_column(df_columns, key)
            if actual_col:
                self.actual_columns[key] = actual_col
            else:
                self.actual_columns[key] = None
    
    def load_spreadsheet(self):
        """Load data from Google Sheets"""
        try:
            logging.info(f"Loading spreadsheet ID: {self.spreadsheet_id}, Sheet: {self.sheet_name}")
            self.df = self.sheets_helper.read_sheet(self.spreadsheet_id, self.sheet_name)
            
            if self.df.empty:
                logging.error("Spreadsheet is empty!")
                sys.exit(1)
            
            # Map columns
            self._map_columns()
            
            # Ensure string columns are of object dtype
            string_columns = ['status', 'serial', 'device_assignment', 'device_location']
            for key in string_columns:
                col = self.actual_columns.get(key)
                if col and col in self.df.columns:
                    self.df[col] = self.df[col].astype('object')
            
            logging.info(f"Loaded spreadsheet with {len(self.df)} rows")
            
        except Exception as e:
            logging.error(f"Error loading spreadsheet: {e}")
            sys.exit(1)
    
    def save_spreadsheet(self):
        """Save the DataFrame back to Google Sheets"""
        try:
            self.sheets_helper.write_sheet(self.spreadsheet_id, self.df, self.sheet_name)
            logging.info("Saved data to Google Sheets")
        except Exception as e:
            logging.error(f"Error saving to Google Sheets: {e}")
    
    def get_next_available_proxy(self):
        """Get the next available proxy configuration"""
        status_col = self.actual_columns.get('status')
        
        for idx, row in self.df.iterrows():
            status_val = row[status_col] if status_col else ''
            if pd.isna(status_val) or str(status_val).strip() == '':
                proxy_info = {
                    'row_index': idx,
                    'host': str(row[self.actual_columns['proxy']]),
                    'port': str(row[self.actual_columns['port']]),
                    'username': str(row[self.actual_columns['username']]),
                    'password': str(row[self.actual_columns['password']])
                }
                logging.info(f"Found available proxy at row {idx + 2}")
                return proxy_info
        
        logging.warning("No available proxies found!")
        return None
    
    def mark_proxy_used(self, row_index, device_serial, device_assignment=None, location=None):
        """Mark proxy as used and add device info"""
        try:
            # Update DataFrame
            if self.actual_columns.get('status'):
                self.df.at[row_index, self.actual_columns['status']] = 'Verify'
            if self.actual_columns.get('serial'):
                self.df.at[row_index, self.actual_columns['serial']] = str(device_serial)
            if device_assignment and self.actual_columns.get('device_assignment'):
                self.df.at[row_index, self.actual_columns['device_assignment']] = str(device_assignment)
            if location and self.actual_columns.get('device_location'):
                self.df.at[row_index, self.actual_columns['device_location']] = str(location)
            
            # Save entire spreadsheet
            self.save_spreadsheet()
            
            logging.info(f"Marked row {row_index + 2} as 'Verify' with serial {device_serial}")
            if device_assignment:
                logging.info(f"Added device assignment: {device_assignment}")
            if location:
                logging.info(f"Added location: {location}")
        except Exception as e:
            logging.error(f"Error updating Google Sheets: {e}")
    
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
    
    def tap(self, device_id, x, y, quick=False):
        """Tap at coordinates"""
        self.debug_log(f"Tapping at ({x}, {y})")
        self.run_adb(device_id, f"shell input tap {x} {y}")
        if quick:
            time.sleep(0.625)  # Increased by 25% from 0.5
        else:
            time.sleep(1.875)  # Increased by 25% from 1.5
    
    def clear_and_type(self, device_id, text):
        """Clear current text and type new text"""
        self.run_adb(device_id, "shell input keyevent KEYCODE_MOVE_END")
        time.sleep(0.5)  # Increased by 25% from 0.4
        
        self.run_adb(device_id, "shell input keyevent --longpress KEYCODE_DEL")
        time.sleep(0.5)  # Increased by 25% from 0.4
        
        for _ in range(20):
            self.run_adb(device_id, "shell input keyevent KEYCODE_DEL")
        
        time.sleep(0.5)  # Increased by 25% from 0.4
        
        self.debug_log(f"Typing: {text}")
        escaped_text = text.replace(' ', '%s').replace('"', '\\"')
        self.run_adb(device_id, f'shell input text "{escaped_text}"')
        time.sleep(0.94)  # Increased by 25% from 0.75
    
    def type_text(self, device_id, text):
        """Just type text without clearing"""
        self.debug_log(f"Typing: {text}")
        escaped_text = text.replace(' ', '%s').replace('"', '\\"')
        self.run_adb(device_id, f'shell input text "{escaped_text}"')
        time.sleep(0.375)  # Increased by 25% from 0.3
    
    def start_app(self, device_id):
        """Start Super Proxy app"""
        self.debug_log("Force stopping all apps...")
        self.run_adb(device_id, "shell am kill-all")
        time.sleep(1.25)  # Increased by 25% from 1
        
        self.debug_log("Going to home screen...")
        self.run_adb(device_id, "shell input keyevent KEYCODE_HOME")
        time.sleep(1.875)  # Increased by 25% from 1.5
        
        self.debug_log("Tapping on Super Proxy app icon...")
        self.run_adb(device_id, "shell input tap 275 800")
        self.debug_log("Waiting 9.4 seconds for app to fully load...")  # Increased by 25%
        time.sleep(9.4)  # Increased by 25% from 7.5
    
    def wake_and_go_home(self, device_id):
        """Wake device and go to home screen"""
        self.debug_log("Waking device and going to home...")
        
        # Check if screen is on
        screen_state = self.run_adb(device_id, "shell dumpsys power | grep 'mWakefulness='")
        if "Asleep" in screen_state or "Dozing" in screen_state:
            # Turn on screen
            self.run_adb(device_id, "shell input keyevent KEYCODE_WAKEUP")
            time.sleep(0.625)  # Increased by 25% from 0.5
            self.run_adb(device_id, "shell input keyevent KEYCODE_POWER")
            time.sleep(1.25)  # Increased by 25% from 1
        
        # Check if device is locked
        lock_state = self.run_adb(device_id, "shell dumpsys window | grep 'mDreamingLockscreen='")
        keyguard_state = self.run_adb(device_id, "shell dumpsys window | grep 'mShowingLockscreen='")
        
        if "true" in lock_state or "true" in keyguard_state:
            self.debug_log("Device is locked, attempting to unlock...")
            # Try swipe up to unlock (works for most devices without PIN/password)
            self.run_adb(device_id, "shell input swipe 540 1800 540 800 300")
            time.sleep(1.25)  # Increased by 25% from 1
            
            # If still locked, try keyevent method
            self.run_adb(device_id, "shell input keyevent 82")  # KEYCODE_MENU - works on some devices
            time.sleep(0.625)  # Increased by 25% from 0.5
        
        # Go to home
        self.run_adb(device_id, "shell input keyevent KEYCODE_HOME")
        time.sleep(1.56)  # Increased by 25% from 1.25
    
    def setup_proxy(self, device_id):
        """Configure proxy using UI automation"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*50}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.BLUE}Setting up Super Proxy on device: {device_id}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*50}{Colors.ENDC}")
        
        try:
            # Wake device and go to home first
            self.wake_and_go_home(device_id)
            
            # Get device serial
            serial = self.run_adb(device_id, "shell getprop ro.serialno") or device_id
            logging.info(f"Device serial: {serial}")
            
            # Get next available proxy
            proxy_info = self.get_next_available_proxy()
            if not proxy_info:
                logging.error("No available proxy found!")
                return False
            
            logging.info(f"Using proxy: {proxy_info['host']}:{proxy_info['port']}")
            
            # 1. Start the app
            self.start_app(device_id)
            
            # Verify app is running
            current_app = self.run_adb(device_id, "shell dumpsys window | grep -E 'mCurrentFocus'")
            self.debug_log(f"Current focus: {current_app}")
            
            if "superproxy" not in current_app.lower():
                logging.warning("Super Proxy app may not be in focus. Trying to start again...")
                self.start_app(device_id)
            
            # 2. Tap '+ Add Proxy' button
            self.debug_log("Step 1: Tapping '+ Add Proxy' button")
            self.tap(device_id, 510, 1250)
            
            # 3. Tap 'Profile name' field
            self.debug_log("Step 2: Tapping 'Profile name' field")
            self.tap(device_id, 320, 275, quick=True)
            
            # 4. Clear and type new profile name
            self.debug_log(f"Step 3: Setting profile name to VPN_{serial[-4:]}")
            self.clear_and_type(device_id, f"VPN_{serial[-4:]}")
            
            # 5. Server field
            self.debug_log(f"Step 4: Setting Server to {proxy_info['host']}")
            self.tap(device_id, 175, 500, quick=True)
            self.type_text(device_id, proxy_info['host'])
            
            # 6. Port field
            self.debug_log(f"Step 5: Setting Port to {proxy_info['port']}")
            self.tap(device_id, 175, 625, quick=True)
            self.type_text(device_id, str(proxy_info['port']))
            
            # 7. Authentication method dropdown
            self.debug_log("Step 6: Opening Authentication dropdown")
            self.tap(device_id, 175, 750)
            
            # 8. Select Username/Password
            self.debug_log("Step 7: Selecting Username/Password")
            self.tap(device_id, 175, 930)
            
            # 9. Username field
            self.debug_log(f"Step 8: Setting Username")
            self.tap(device_id, 175, 870, quick=True)
            self.type_text(device_id, proxy_info['username'])
            
            # Close keyboard
            self.debug_log("Closing keyboard")
            self.tap(device_id, 165, 1550, quick=True)
            time.sleep(1.25)  # Increased by 25% from 1
            
            # 10. Password field
            self.debug_log(f"Step 9: Setting Password")
            self.tap(device_id, 175, 1025, quick=True)
            self.type_text(device_id, proxy_info['password'])
            
            # 11. Save button
            self.debug_log("Step 10: Saving configuration")
            self.tap(device_id, 680, 135)
            time.sleep(1.875)  # Increased by 25% from 1.5
            
            # 12. Start button
            self.debug_log("Step 11: Starting proxy")
            self.tap(device_id, 365, 1250)
            time.sleep(1.875)  # Increased by 25% from 1.5
            
            # 13. OK on popup
            self.debug_log("Step 12: Accepting VPN permission")
            self.tap(device_id, 600, 1000)
            time.sleep(2.81)  # Increased by 25% from 2.25
            
            # 14. Configure Always-on VPN
            self.debug_log("Step 13: Configuring Always-on VPN")
            self.configure_always_on_vpn(device_id)
            
            # Store proxy info for later update
            self.current_proxy_info = proxy_info
            self.current_serial = serial
            
            logging.info(f"Device {serial} configured with proxy {proxy_info['host']}")
            return True
            
        except Exception as e:
            logging.error(f"Error: {e}")
            return False
    
    def configure_always_on_vpn(self, device_id):
        """Configure Always-on VPN through UI"""
        try:
            self.debug_log("Configuring Always-on VPN through Settings UI...")
            
            # Set VPN settings using secure namespace (as per baseline_setup.sh)
            self.run_adb(device_id, f"shell settings put secure always_on_vpn_app {self.package_name}")
            self.run_adb(device_id, "shell settings put secure always_on_vpn_lockdown 1")
            time.sleep(0.625)  # Increased by 25% from 0.5
            
            # Open VPN settings directly
            self.debug_log("Opening VPN settings...")
            self.run_adb(device_id, "shell am start -a android.settings.VPN_SETTINGS")
            time.sleep(3.125)  # Increased by 25% from 2.5
            
            # Look for Super Proxy in the list (usually has a gear icon)
            self.debug_log("Looking for Super Proxy VPN entry...")
            # Tap on the gear/settings icon next to Super Proxy
            # Position may vary, but typically on the right side
            self.tap(device_id, 650, 400)  # Adjust Y based on position in list
            time.sleep(1.875)  # Increased by 25% from 1.5
            
            # Toggle "Always-on VPN" if not already on
            self.debug_log("Enabling Always-on VPN toggle...")
            self.tap(device_id, 650, 600)  # Toggle switch position
            time.sleep(1.25)  # Increased by 25% from 1
            
            # Toggle "Block connections without VPN" 
            self.debug_log("Enabling Block connections without VPN...")
            self.tap(device_id, 650, 710)  # Second toggle position
            time.sleep(1.875)  # Increased by 25% from 1.5
            
            # Handle popup confirmation for blocking connections
            self.debug_log("Confirming Block connections popup...")
            self.tap(device_id, 600, 890)  # OK button on popup
            time.sleep(1.25)  # Increased by 25% from 1
            
            # Go back to home
            self.debug_log("Returning to home screen...")
            self.run_adb(device_id, "shell input keyevent KEYCODE_HOME")
            time.sleep(1.25)  # Increased by 25% from 1
            
            logging.info("Always-on VPN configured with connection blocking")
            
        except Exception as e:
            logging.error(f"Error configuring Always-on VPN: {e}")
    
    def reboot_device(self, device_id):
        """Reboot single device with user confirmation"""
        import select
        
        print(f"\n{Colors.CYAN}Reboot device before setup? (y/n) {Colors.BOLD}[auto-continuing in 5 seconds]:{Colors.ENDC} ", end='', flush=True)
        
        # Check if input is available within 5 seconds
        ready, _, _ = select.select([sys.stdin], [], [], 5.0)
        
        if ready:
            reboot_choice = sys.stdin.readline().strip().lower()
        else:
            reboot_choice = 'n'  # Default to 'n' after timeout
            print(f"{Colors.GREEN}n (auto-selected){Colors.ENDC}")
        
        if reboot_choice == 'y':
            print(f"\n{Colors.BOLD}{Colors.WARNING}{'='*50}{Colors.ENDC}")
            print(f"{Colors.BOLD}{Colors.WARNING}🔄 Rebooting device: {device_id}{Colors.ENDC}")
            print(f"{Colors.BOLD}{Colors.WARNING}{'='*50}{Colors.ENDC}")
            
            subprocess.run(f"adb -s {device_id} reboot", shell=True)
            
            print(f"\n{Colors.BOLD}{Colors.WARNING}{'='*60}{Colors.ENDC}")
            print(f"{Colors.BOLD}{Colors.WARNING}⚠️  IMPORTANT: Device is rebooting!{Colors.ENDC}")
            print(f"{Colors.WARNING}Please wait for device to fully reboot.{Colors.ENDC}")
            print(f"{Colors.WARNING}Press ENTER when device is back online...{Colors.ENDC}")
            print(f"{Colors.BOLD}{Colors.WARNING}{'='*60}{Colors.ENDC}")
            input()
            
            temp_devices = self.get_devices()
            if device_id not in temp_devices:
                logging.error(f"Device {device_id} not found after reboot!")
                return False
            
            self.debug_log("Device is back online")
            return True
        else:
            self.debug_log("Skipping reboot, proceeding with setup...")
            return True
    
    def start_scrcpy(self, device_id):
        """Start scrcpy for a specific device"""
        try:
            if device_id in self.scrcpy_processes:
                self.stop_scrcpy(device_id)
            
            self.debug_log(f"📱 Starting screen mirror (scrcpy) for device: {device_id}")
            process = subprocess.Popen(
                f"scrcpy -s {device_id} --window-title='Device: {device_id}' --window-width=400 --window-height=800 --window-x=100 --window-y=100",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.scrcpy_processes[device_id] = process
            time.sleep(2.5)  # Increased by 25% from 2
        except Exception as e:
            logging.warning(f"Could not start scrcpy for {device_id}: {e}")
    
    def stop_scrcpy(self, device_id):
        """Stop scrcpy for a specific device"""
        try:
            if device_id in self.scrcpy_processes:
                process = self.scrcpy_processes[device_id]
                if process.poll() is None:
                    process.terminate()
                    time.sleep(0.625)  # Increased by 25% from 0.5
                del self.scrcpy_processes[device_id]
        except Exception as e:
            logging.warning(f"Error stopping scrcpy: {e}")
    
    def stop_all_scrcpy(self):
        """Stop all scrcpy processes"""
        for device_id in list(self.scrcpy_processes.keys()):
            self.stop_scrcpy(device_id)
    
    def check_vpn_configured(self, device_id):
        """Check if device already has VPN configured"""
        try:
            vpn_app = self.run_adb(device_id, "shell settings get secure always_on_vpn_app")
            lockdown = self.run_adb(device_id, "shell settings get secure always_on_vpn_lockdown")
            
            if vpn_app and self.package_name in vpn_app and lockdown == "1":
                return True
            return False
        except:
            return False
    
    def check_app_installed(self, device_id, package_name):
        """Check if a specific app is installed"""
        try:
            result = self.run_adb(device_id, f"shell pm list packages {package_name}")
            return f"package:{package_name}" in result if result else False
        except:
            return False
    
    def check_vpn_active(self, device_id):
        """Check if VPN is currently active"""
        try:
            # Check for active VPN connection
            result = self.run_adb(device_id, "shell ip addr show tun0 2>/dev/null")
            if result and "tun0" in result:
                return True
            
            # Alternative check using connectivity service
            result = self.run_adb(device_id, "shell dumpsys connectivity | grep 'Active default network'")
            if result and "VPN" in result:
                return True
            
            return False
        except:
            return False
    
    def get_device_name(self, device_id):
        """Get the device name if set"""
        try:
            device_name = self.run_adb(device_id, "shell settings get global device_name")
            return device_name.strip() if device_name and device_name != "null" else None
        except:
            return None
    
    def display_device_status(self):
        """Display comprehensive status of all connected devices"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}DEVICE STATUS OVERVIEW{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.ENDC}")
        
        total_devices = len(self.devices)
        print(f"\n{Colors.BOLD}Connected Devices: {Colors.CYAN}{total_devices}{Colors.ENDC}")
        
        if total_devices == 0:
            print(f"{Colors.FAIL}No devices connected!{Colors.ENDC}")
            return
        
        # Get all device information
        device_statuses = []
        for device in self.devices:
            status = self.get_device_full_status(device)
            device_statuses.append(status)
        
        # Display each device status
        for idx, status in enumerate(device_statuses):
            print(f"\n{Colors.BOLD}{Colors.HEADER}[Device {idx + 1}/{total_devices}]{Colors.ENDC}")
            print(f"{Colors.BOLD}Serial: {Colors.CYAN}{status['serial']}{Colors.ENDC}")
            
            # Device name
            if status['device_name']:
                print(f"  Device Name: {Colors.GREEN}{status['device_name']}{Colors.ENDC}")
            else:
                print(f"  Device Name: {Colors.WARNING}Not set{Colors.ENDC}")
            
            # Apps status
            print(f"\n  {Colors.BOLD}Apps:{Colors.ENDC}")
            if status['super_proxy_installed']:
                print(f"    Super Proxy: {Colors.GREEN}✓ Installed{Colors.ENDC}")
            else:
                print(f"    Super Proxy: {Colors.FAIL}✗ Missing{Colors.ENDC}")
            
            if status['tiktok_installed']:
                print(f"    TikTok: {Colors.GREEN}✓ Installed{Colors.ENDC}")
            else:
                print(f"    TikTok: {Colors.FAIL}✗ Missing{Colors.ENDC}")
            
            # VPN status
            print(f"\n  {Colors.BOLD}VPN Status:{Colors.ENDC}")
            if status['vpn_configured']:
                print(f"    Configuration: {Colors.GREEN}✓ Configured{Colors.ENDC}")
                if status['vpn_active']:
                    print(f"    Connection: {Colors.GREEN}✓ Active{Colors.ENDC}")
                else:
                    print(f"    Connection: {Colors.WARNING}⚠ Not Active{Colors.ENDC}")
            else:
                print(f"    Configuration: {Colors.FAIL}✗ Not Configured{Colors.ENDC}")
            
            # Spreadsheet status
            print(f"\n  {Colors.BOLD}Spreadsheet Status:{Colors.ENDC}")
            if status['in_spreadsheet']:
                print(f"    Registration: {Colors.GREEN}✓ Found in sheet (Row {status['row_number']}){Colors.ENDC}")
                
                # Show all spreadsheet fields
                fields = [
                    ('Proxy/VPN', status['has_proxy'], status['proxy']),
                    ('Port', status['has_port'], status['port']),
                    ('Username', status['has_username'], status['username']),
                    ('Password', status['has_password'], '[hidden]' if status['has_password'] else None),
                    ('Status', status['has_status'], status['status_value']),
                    ('Serial', True, status['serial']),  # Always present if in sheet
                    ('Assignment', status['has_assignment'], status['assignment']),
                    ('Location', status['has_location'], status['location'])
                ]
                
                for field_name, has_value, value in fields:
                    if has_value and value:
                        print(f"    {field_name}: {Colors.GREEN}✓ {value}{Colors.ENDC}")
                    else:
                        print(f"    {field_name}: {Colors.FAIL}✗ Missing{Colors.ENDC}")
                
                # Show missing fields summary if any
                missing_fields = [name for name, has_value, _ in fields if not has_value]
                if missing_fields:
                    print(f"\n    {Colors.WARNING}Missing fields: {', '.join(missing_fields)}{Colors.ENDC}")
            else:
                print(f"    Registration: {Colors.WARNING}⚠ Not in sheet{Colors.ENDC}")
                print(f"    {Colors.WARNING}Device needs to be added to spreadsheet{Colors.ENDC}")
            
            # Overall status
            print(f"\n  {Colors.BOLD}Overall Status: ", end='')
            if status['fully_configured']:
                print(f"{Colors.GREEN}✓ Fully Configured{Colors.ENDC}")
            elif status['in_spreadsheet']:
                missing_count = len([name for name, has_value, _ in fields if not has_value])
                print(f"{Colors.WARNING}⚠ Partially Configured ({missing_count} fields missing){Colors.ENDC}")
            else:
                print(f"{Colors.CYAN}• Ready for Setup{Colors.ENDC}")
            
            print(f"{Colors.CYAN}{'─'*70}{Colors.ENDC}")
        
        # Summary
        fully_configured = sum(1 for s in device_statuses if s['fully_configured'])
        partially_configured = sum(1 for s in device_statuses if s['in_spreadsheet'] and not s['fully_configured'])
        not_configured = total_devices - fully_configured - partially_configured
        
        print(f"\n{Colors.BOLD}Summary:{Colors.ENDC}")
        print(f"  {Colors.GREEN}Fully Configured: {fully_configured}{Colors.ENDC}")
        if partially_configured > 0:
            print(f"  {Colors.WARNING}Partially Configured: {partially_configured}{Colors.ENDC}")
        if not_configured > 0:
            print(f"  {Colors.CYAN}Not Configured: {not_configured}{Colors.ENDC}")
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.ENDC}\n")
    
    def get_device_full_status(self, device_id):
        """Get comprehensive status information for a single device"""
        serial = self.run_adb(device_id, "shell getprop ro.serialno") or device_id
        device_name = self.get_device_name(device_id)
        
        # Check apps
        super_proxy_installed = self.check_app_installed(device_id, self.package_name)
        tiktok_installed = self.check_app_installed(device_id, "com.zhiliaoapp.musically") or \
                          self.check_app_installed(device_id, "com.ss.android.ugc.trill")
        
        # Check VPN
        vpn_configured = self.check_vpn_configured(device_id)
        vpn_active = self.check_vpn_active(device_id)
        
        # Check spreadsheet
        serial_col = self.actual_columns.get('serial')
        device_assignment_col = self.actual_columns.get('device_assignment')
        device_location_col = self.actual_columns.get('device_location')
        proxy_col = self.actual_columns.get('proxy')
        port_col = self.actual_columns.get('port')
        username_col = self.actual_columns.get('username')
        password_col = self.actual_columns.get('password')
        status_col = self.actual_columns.get('status')
        
        in_spreadsheet = False
        row_number = None
        has_proxy = False
        has_port = False
        has_username = False
        has_password = False
        has_status = False
        has_assignment = False
        has_location = False
        proxy = None
        port = None
        username = None
        status_value = None
        assignment = None
        location = None
        vpn_info = None
        
        if serial_col:
            for idx, row in self.df.iterrows():
                if pd.notna(row.get(serial_col)) and str(row[serial_col]).strip() == serial:
                    in_spreadsheet = True
                    row_number = idx + 2  # Excel row number (1-indexed + header)
                    
                    # Check each field
                    if proxy_col and pd.notna(row.get(proxy_col)) and str(row[proxy_col]).strip():
                        has_proxy = True
                        proxy = str(row[proxy_col])
                    
                    if port_col and pd.notna(row.get(port_col)) and str(row[port_col]).strip():
                        has_port = True
                        port = str(row[port_col])
                    
                    if username_col and pd.notna(row.get(username_col)) and str(row[username_col]).strip():
                        has_username = True
                        username = str(row[username_col])
                    
                    if password_col and pd.notna(row.get(password_col)) and str(row[password_col]).strip():
                        has_password = True
                    
                    if status_col and pd.notna(row.get(status_col)) and str(row[status_col]).strip():
                        has_status = True
                        status_value = str(row[status_col])
                    
                    if device_assignment_col and pd.notna(row.get(device_assignment_col)) and str(row[device_assignment_col]).strip():
                        has_assignment = True
                        assignment = str(row[device_assignment_col])
                    
                    if device_location_col and pd.notna(row.get(device_location_col)) and str(row[device_location_col]).strip():
                        has_location = True
                        location = str(row[device_location_col])
                    
                    # Get VPN info for display
                    if has_proxy and has_port:
                        vpn_info = f"{proxy}:{port}"
                    
                    break
        
        # Check if all required fields are present
        all_vpn_fields = has_proxy and has_port and has_username and has_password
        fully_configured = (in_spreadsheet and has_assignment and has_location and 
                           all_vpn_fields and super_proxy_installed and vpn_configured)
        
        return {
            'serial': serial,
            'device_name': device_name,
            'super_proxy_installed': super_proxy_installed,
            'tiktok_installed': tiktok_installed,
            'vpn_configured': vpn_configured,
            'vpn_active': vpn_active,
            'in_spreadsheet': in_spreadsheet,
            'row_number': row_number,
            'has_proxy': has_proxy,
            'has_port': has_port,
            'has_username': has_username,
            'has_password': has_password,
            'has_status': has_status,
            'has_assignment': has_assignment,
            'has_location': has_location,
            'proxy': proxy,
            'port': port,
            'username': username,
            'status_value': status_value,
            'assignment': assignment,
            'location': location,
            'vpn_info': vpn_info,
            'fully_configured': fully_configured
        }
    
    def check_existing_vpn_configs(self):
        """Check all devices for existing VPN configurations"""
        if not self.devices:
            return
        
        serial_col = self.actual_columns.get('serial')
        device_assignment_col = self.actual_columns.get('device_assignment')
        device_location_col = self.actual_columns.get('device_location')
        configured_devices = []
        
        for device in self.devices[:]:
            serial = self.run_adb(device, "shell getprop ro.serialno") or device
            
            # Check if serial exists in spreadsheet
            serial_in_spreadsheet = False
            spreadsheet_row = None
            row_idx = None
            if serial_col:
                for idx, row in self.df.iterrows():
                    if pd.notna(row.get(serial_col)) and str(row[serial_col]).strip() == serial:
                        serial_in_spreadsheet = True
                        spreadsheet_row = row
                        row_idx = idx
                        break
            
            if serial_in_spreadsheet:
                # Check if device assignment and location are filled
                has_assignment = device_assignment_col and pd.notna(spreadsheet_row.get(device_assignment_col)) and str(spreadsheet_row[device_assignment_col]).strip() != ''
                has_location = device_location_col and pd.notna(spreadsheet_row.get(device_location_col)) and str(spreadsheet_row[device_location_col]).strip() != ''
                
                if has_assignment and has_location:
                    # Device is fully configured
                    configured_devices.append(device)
                    self.debug_log(f"Device {serial} already fully configured")
                else:
                    # Device is partially configured - needs assignment/location
                    self.debug_log(f"Device {serial} needs assignment/location info")
            else:
                self.debug_log(f"Device {serial} not in spreadsheet - will be configured")
        
        # Store configured devices but don't remove them yet
        self.configured_devices = configured_devices
        
        if configured_devices:
            self.debug_log(f"Found {len(configured_devices)} fully configured devices")
    
    def setup_all_devices(self):
        """Setup all connected devices"""
        if not self.devices:
            logging.error("No devices found!")
            return
        
        # Display comprehensive device status
        self.display_device_status()
        
        # Filter out fully configured devices after showing status
        if hasattr(self, 'configured_devices') and self.configured_devices:
            for device in self.configured_devices:
                if device in self.devices:
                    self.devices.remove(device)
            
            if not self.devices:
                print(f"\n{Colors.GREEN}All devices are already fully configured!{Colors.ENDC}")
                return
        
        # Show what will be configured
        if len(self.devices) > 0:
            print(f"\n{Colors.BOLD}{Colors.CYAN}Will configure {len(self.devices)} device(s) that are not fully set up.{Colors.ENDC}")
        
        # Ask if user wants to continue
        print(f"{Colors.CYAN}Do you want to continue with the setup? (y/n): {Colors.ENDC}", end='', flush=True)
        choice = input().strip().lower()
        if choice != 'y':
            print(f"{Colors.WARNING}Setup cancelled by user.{Colors.ENDC}")
            return
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}Starting proxy setup for {len(self.devices)} devices{Colors.ENDC}")
        
        successful = 0
        failed = 0
        device_index = 0
        
        while device_index < len(self.devices):
            device = self.devices[device_index]
            
            print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
            print(f"{Colors.BOLD}{Colors.HEADER}DEVICE {device_index + 1}/{len(self.devices)}: {device}{Colors.ENDC}")
            print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
            
            if not self.reboot_device(device):
                logging.error("Device not available after reboot, skipping...")
                device_index += 1
                continue
            
            self.start_scrcpy(device)
            
            result = self.setup_proxy(device)
            
            self.stop_scrcpy(device)
            
            if result:
                successful += 1
            else:
                failed += 1
            
            # User interaction
            while True:
                print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*50}{Colors.ENDC}")
                print(f"{Colors.BOLD}{Colors.CYAN}Device {device_index + 1}/{len(self.devices)} completed{Colors.ENDC}")
                
                if device_index < len(self.devices) - 1:
                    user_input = input(f"{Colors.CYAN}Press 'r' to repeat, 's' to skip, or ENTER to continue: {Colors.ENDC}").strip().lower()
                else:
                    user_input = input(f"{Colors.CYAN}Press 'r' to repeat, 's' to skip, or ENTER to finish: {Colors.ENDC}").strip().lower()
                
                if user_input == 'r':
                    self.debug_log("Repeating current device...")
                    if result:
                        successful -= 1
                    else:
                        failed -= 1
                    time.sleep(1.25)  # Increased by 25% from 1
                    break
                elif user_input == 's':
                    self.debug_log("Skipping current device...")
                    if result:
                        successful -= 1
                    else:
                        failed -= 1
                    device_index += 1
                    break
                else:  # ENTER
                    if result:
                        # Ask for device info
                        print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*50}{Colors.ENDC}")
                        print(f"{Colors.BOLD}{Colors.GREEN}Device setup successful! Please provide:{Colors.ENDC}")
                        print(f"{Colors.BOLD}{Colors.GREEN}{'='*50}{Colors.ENDC}")
                        
                        assignment = None
                        while not assignment:
                            assignment = input(f"\n{Colors.CYAN}Device Assignment (required): {Colors.ENDC}").strip()
                            if not assignment:
                                print(f"{Colors.FAIL}Device assignment is required.{Colors.ENDC}")
                        
                        location = None
                        while not location:
                            location = input(f"\n{Colors.CYAN}Device Location (required): {Colors.ENDC}").strip()
                            if not location:
                                print(f"{Colors.FAIL}Device location is required.{Colors.ENDC}")
                        
                        # Prompt user to place the device in the assigned location
                        print(f"\n{Colors.BOLD}{Colors.WARNING}{'='*60}{Colors.ENDC}")
                        print(f"{Colors.BOLD}{Colors.WARNING}⚠️  IMPORTANT: Please place the device in the assigned location{Colors.ENDC}")
                        print(f"{Colors.CYAN}   Assignment: {Colors.BOLD}{assignment}{Colors.ENDC}")
                        print(f"{Colors.CYAN}   Location: {Colors.BOLD}{location}{Colors.ENDC}")
                        print(f"{Colors.BOLD}{Colors.WARNING}{'='*60}{Colors.ENDC}")
                        input(f"\n{Colors.CYAN}Press ENTER after placing the device in the correct location...{Colors.ENDC}")
                        
                        # Update Google Sheets
                        self.mark_proxy_used(self.current_proxy_info['row_index'], 
                                           self.current_serial, 
                                           device_assignment=assignment,
                                           location=location)
                        
                        # Update device name
                        device_name = f"{location} - {self.current_serial}"
                        self.debug_log(f"Setting device name to: {device_name}")
                        self.run_adb(device, f'shell settings put global device_name "{device_name}"')
                        time.sleep(0.625)  # Increased by 25% from 0.5
                        
                        print(f"\n{Colors.BOLD}{Colors.GREEN}✅ Device configured successfully!{Colors.ENDC}")
                        print(f"{Colors.CYAN}   Assignment: {Colors.BOLD}{assignment}{Colors.ENDC}")
                        print(f"{Colors.CYAN}   Location: {Colors.BOLD}{location}{Colors.ENDC}")
                        print(f"{Colors.CYAN}   Device Name: {Colors.BOLD}{device_name}{Colors.ENDC}")
                    
                    device_index += 1
                    break
        
        print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*50}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.GREEN}Setup Complete!{Colors.ENDC}")
        print(f"{Colors.GREEN}✓ Successful: {successful}{Colors.ENDC}")
        if failed > 0:
            print(f"{Colors.FAIL}✗ Failed: {failed}{Colors.ENDC}")
        else:
            print(f"{Colors.GREEN}✓ Failed: {failed}{Colors.ENDC}")
        print(f"{Colors.CYAN}View results at: {self.sheets_helper.get_sheet_url(self.spreadsheet_id)}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.GREEN}{'='*50}{Colors.ENDC}")

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='VPN Setup with Google Sheets',
        epilog='Example: python3 vpn_setup.py'
    )
    parser.add_argument('--device', help='Setup specific device only')
    parser.add_argument('--sheet', default='VPN/Email Bank', help='Sheet name to use (default: VPN/Email Bank)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode with verbose output')
    args = parser.parse_args()
    
    VPNSetup.setup_logging(args.debug)
    setup = VPNSetup(args.sheet)
    try:
        if args.device:
            setup.start_scrcpy(args.device)
            setup.setup_proxy(args.device)
            setup.stop_scrcpy(args.device)
        else:
            setup.setup_all_devices()
    finally:
        setup.stop_all_scrcpy()

if __name__ == "__main__":
    main()