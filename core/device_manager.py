import asyncio
import subprocess
from typing import List, Dict, Optional
from dataclasses import dataclass
from loguru import logger
import uiautomator2 as u2
from adb_shell.adb_device import AdbDeviceTcp, AdbDeviceUsb
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from adb_shell.auth.keygen import keygen
import os
import time
import json
from pathlib import Path

try:
    from config.farm_settings import PERFORMANCE, OPTIMIZATIONS
except ImportError:
    # Default settings if config not found
    PERFORMANCE = {
        'max_concurrent_connections': 50,
        'fast_mode_threshold': 20,
        'batch_sizes': {'small': 10, 'medium': 25, 'large': 50, 'xlarge': 75},
        'connection_timeout': 5
    }
    OPTIMIZATIONS = {'skip_device_info': True}


@dataclass
class Device:
    serial: str
    model: str = "Unknown"
    android_version: str = "Unknown"
    status: str = "disconnected"
    u2_device: Optional[u2.Device] = None
    adb_device: Optional[object] = None
    network_info: Optional[Dict] = None
    proxy_status: Optional[str] = None
    
    def __hash__(self):
        return hash(self.serial)


class DeviceManager:
    def __init__(self):
        self.devices: Dict[str, Device] = {}
        self.adb_key_path = os.path.expanduser("~/.android/adbkey")
        self._ensure_adb_key()
        self.cache_file = Path("data/device_cache.json")
        self._load_device_cache()
        
    def _ensure_adb_key(self):
        """Ensure ADB RSA key exists"""
        if not os.path.exists(self.adb_key_path):
            os.makedirs(os.path.dirname(self.adb_key_path), exist_ok=True)
            keygen(self.adb_key_path)
            logger.info(f"Generated new ADB key at {self.adb_key_path}")
    
    def _load_device_cache(self):
        """Load cached device information for faster startup"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                    # Load basic device info from cache
                    for serial, info in cache.items():
                        device = Device(
                            serial=serial,
                            model=info.get('model', 'Unknown'),
                            android_version=info.get('android_version', 'Unknown'),
                            status='disconnected'
                        )
                        self.devices[serial] = device
                    logger.debug(f"Loaded {len(cache)} devices from cache")
            except Exception as e:
                logger.debug(f"Could not load device cache: {e}")
    
    def _save_device_cache(self):
        """Save device information to cache"""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache = {}
            for serial, device in self.devices.items():
                cache[serial] = {
                    'model': device.model,
                    'android_version': device.android_version
                }
            with open(self.cache_file, 'w') as f:
                json.dump(cache, f)
            logger.debug(f"Saved {len(cache)} devices to cache")
        except Exception as e:
            logger.debug(f"Could not save device cache: {e}")
    
    async def scan_devices(self) -> List[Device]:
        """Scan for all connected ADB devices"""
        try:
            # Start ADB server with timeout
            subprocess.run(["adb", "start-server"], capture_output=True, timeout=10)
            
            # Get device list with timeout
            result = subprocess.run(
                ["adb", "devices", "-l"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            
            # Track which devices are currently plugged in
            currently_plugged_serials = set()
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Split by whitespace
                parts = line.split()
                if len(parts) < 2:
                    continue
                    
                serial = parts[0]
                status = parts[1]
                currently_plugged_serials.add(serial)
                
                # Extract model from the detailed info
                model = "Unknown"
                if "model:" in line:
                    model_part = line.split("model:")[1]
                    model = model_part.split()[0].replace("_", " ")
                
                if serial not in self.devices:
                    device = Device(serial=serial, model=model, status=status)
                    self.devices[serial] = device
                    logger.info(f"Found new device: {serial} ({model})")
                else:
                    # Update existing device status
                    existing_device = self.devices[serial]
                    
                    # If device was disconnected and now reappears, update its status
                    if existing_device.status == "disconnected":
                        existing_device.status = status
                        existing_device.model = model  # Update model in case it changed
                        logger.info(f"Device reconnected: {serial} -> {status}")
                    # Only update status if device is not already connected
                    elif existing_device.status != "connected":
                        existing_device.status = status
                        logger.debug(f"Updated device status: {serial} -> {status}")
            
            # Mark devices as disconnected if they're no longer in adb devices list
            for serial, device in self.devices.items():
                if serial not in currently_plugged_serials:
                    if device.status != "disconnected":
                        device.status = "disconnected"
                        device.u2_device = None  # Clear the connection
                        logger.info(f"Device disconnected: {serial}")
            
            return list(self.devices.values())
            
        except Exception as e:
            logger.error(f"Error scanning devices: {e}")
            return []
    
    async def connect_device(self, device: Device, skip_u2: bool = False) -> bool:
        """Initialize connection for a device
        
        Args:
            device: Device to connect to
            skip_u2: If True, skip UIAutomator2 initialization for faster startup
        """
        try:
            # Skip unauthorized devices
            if device.status == "unauthorized":
                logger.warning(f"Skipping unauthorized device {device.serial} - please authorize on device")
                return False
                
            # Only connect to devices with status "device" (authorized)
            if device.status != "device":
                logger.warning(f"Skipping {device.serial} - status: {device.status}")
                return False
            
            if skip_u2:
                # Fast mode: Just mark as connected without initializing UIAutomator2
                device.status = "connected"
                self.devices[device.serial] = device
                
                # Use cached info if available
                if not device.model or device.model == "Unknown":
                    # Try to get basic info without UIAutomator2
                    try:
                        loop = asyncio.get_event_loop()
                        result = await loop.run_in_executor(
                            None,
                            subprocess.run,
                            ["adb", "-s", device.serial, "shell", "getprop", "ro.product.model"],
                            {"capture_output": True, "text": True, "timeout": 2}
                        )
                        if result.returncode == 0:
                            device.model = result.stdout.strip().replace("_", " ")
                    except:
                        pass
                
                logger.debug(f"Fast connected to {device.serial}")
                return True
            
            logger.info(f"Connecting to device {device.serial}...")
            
            # Run the blocking u2.connect in a thread pool to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            device.u2_device = await loop.run_in_executor(None, u2.connect, device.serial)
            
            # Test connection - also run in executor to avoid blocking
            info = await loop.run_in_executor(None, lambda: device.u2_device.info)
            device.android_version = str(info.get('version', 'Unknown'))
            
            # Update device in our dictionary
            device.status = "connected"
            self.devices[device.serial] = device
            
            # Save to cache for faster future startups
            self._save_device_cache()
            
            logger.success(f"Connected to {device.serial} - Android {device.android_version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {device.serial}: {e}")
            device.status = "error"
            return False
    
    async def connect_all_devices(self, progress_callback=None, batch_size=None, fast_mode=False) -> int:
        """Connect to all detected devices in parallel with optional progress callback
        
        Args:
            progress_callback: Optional callback for progress updates
            batch_size: Max number of devices to connect simultaneously (None = all at once)
            fast_mode: If True, skip UIAutomator2 initialization for faster startup
        """
        start_time = time.time()
        
        # Use existing devices if already scanned, otherwise scan
        if not self.devices:
            devices = await self.scan_devices()
        else:
            devices = list(self.devices.values())
        
        if not devices:
            logger.warning("No devices found")
            return 0
        
        # Filter only authorized devices (status == "device")
        authorized_devices = [d for d in devices if d.status == "device"]
        
        if not authorized_devices:
            logger.warning(f"No authorized devices found. Total devices: {len(devices)}")
            for device in devices:
                logger.info(f"  Device {device.serial}: status={device.status}")
            return 0
        
        device_count = len(authorized_devices)
        logger.info(f"Connecting to {device_count} authorized device(s) in parallel...")
        
        # Determine batch size from config
        if batch_size is None:
            if device_count <= 10:
                batch_size = PERFORMANCE['batch_sizes']['small']
            elif device_count <= 50:
                batch_size = PERFORMANCE['batch_sizes']['medium']
            elif device_count <= 100:
                batch_size = PERFORMANCE['batch_sizes']['large']
            else:
                batch_size = PERFORMANCE['batch_sizes']['xlarge']
            
            # Increase batch size in fast mode
            if fast_mode:
                batch_size = min(batch_size * 2, PERFORMANCE['max_concurrent_connections'])
        
        total_connected = 0
        
        # Process in batches if needed
        if batch_size >= device_count:
            # Single batch - connect all at once
            tasks = [asyncio.create_task(self.connect_device(device, skip_u2=fast_mode)) for device in authorized_devices]
            
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                total_connected = sum(1 for r in results if r is True)
                
                if progress_callback:
                    await progress_callback(total_connected, device_count)
                    
            except asyncio.CancelledError:
                for task in tasks:
                    if not task.done():
                        task.cancel()
                raise
        else:
            # Multiple batches for large device farms
            for batch_start in range(0, device_count, batch_size):
                batch_end = min(batch_start + batch_size, device_count)
                batch_devices = authorized_devices[batch_start:batch_end]
                
                logger.info(f"Connecting batch {batch_start//batch_size + 1}: devices {batch_start+1}-{batch_end} of {device_count}")
                
                tasks = [asyncio.create_task(self.connect_device(device, skip_u2=fast_mode)) for device in batch_devices]
                
                try:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    batch_connected = sum(1 for r in results if r is True)
                    total_connected += batch_connected
                    
                    if progress_callback:
                        await progress_callback(total_connected, device_count)
                        
                except asyncio.CancelledError:
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                    raise
        
        # Calculate and log connection time
        elapsed_time = time.time() - start_time
        logger.info(f"Successfully connected to {total_connected}/{device_count} devices in {elapsed_time:.1f} seconds")
        
        if device_count > 10:
            # Log performance metrics for large farms
            avg_time_per_device = elapsed_time / device_count if device_count > 0 else 0
            connection_rate = device_count / elapsed_time if elapsed_time > 0 else 0
            logger.info(f"Performance: {avg_time_per_device:.2f} sec/device, {connection_rate:.1f} devices/sec")
        
        # Save cache after successful connections
        if fast_mode:
            self._save_device_cache()
        
        return total_connected
    
    def get_connected_devices(self) -> List[Device]:
        """Get all connected devices"""
        return [d for d in self.devices.values() if d.status == "connected"]
    
    async def ensure_u2_connection(self, device: Device) -> bool:
        """Ensure UIAutomator2 is connected for a device (for operations that need it)"""
        if device.u2_device is not None:
            return True
        
        try:
            logger.debug(f"Initializing UIAutomator2 for {device.serial}...")
            loop = asyncio.get_event_loop()
            device.u2_device = await loop.run_in_executor(None, u2.connect, device.serial)
            
            # Test connection
            info = await loop.run_in_executor(None, lambda: device.u2_device.info)
            device.android_version = str(info.get('version', 'Unknown'))
            
            logger.debug(f"UIAutomator2 ready for {device.serial}")
            return True
        except Exception as e:
            logger.error(f"Failed to init UIAutomator2 for {device.serial}: {e}")
            return False
    
    async def check_proxy_status(self, device: Device) -> str:
        """Check if DoubleSpeed proxy is running on the device"""
        try:
            # Check if the DoubleSpeed app is running with VPN service
            result = subprocess.run(
                ["adb", "-s", device.serial, "shell", 
                 "dumpsys activity services com.android.systemui.helper"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            output = result.stdout
            
            # Check if VPN service is running (TProxyService is the actual VPN service)
            if "TProxyService" in output and "app=ProcessRecord" in output:
                # The service is running, proxy is active
                return "Running"
            
            # Check if app is at least installed and running
            ps_result = subprocess.run(
                ["adb", "-s", device.serial, "shell", 
                 "ps -A | grep com.android.systemui.helper"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if "com.android.systemui.helper" in ps_result.stdout:
                # App is running but proxy might not be active
                return "App Open"
            
            # Check if proxy settings are configured (app installed)
            package_result = subprocess.run(
                ["adb", "-s", device.serial, "shell",
                 "pm list packages | grep com.android.systemui.helper"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if "com.android.systemui.helper" in package_result.stdout:
                return "Installed"
            
            return "Not Installed"
            
        except Exception as e:
            logger.debug(f"Failed to check proxy status for {device.serial}: {e}")
            return "Unknown"
    
    async def get_device_network_info(self, device: Device) -> Dict:
        """Get network interface information for device"""
        network_info = {
            'interfaces': [],
            'primary_ip': None,
            'primary_interface': None
        }
        
        try:
            # Get network interfaces with IP addresses
            ip_output = subprocess.run(
                ["adb", "-s", device.serial, "shell", "ip", "addr", "show"],
                capture_output=True,
                text=True,
                timeout=5
            ).stdout
            
            # Parse the output
            current_interface = None
            for line in ip_output.split('\n'):
                # Check for interface name
                if ': ' in line and '@' not in line:
                    parts = line.split(': ')
                    if len(parts) >= 2:
                        current_interface = parts[1].split('@')[0] if '@' in parts[1] else parts[1]
                        
                # Check for IPv4 address
                if 'inet ' in line and current_interface:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        ip_addr = parts[1].split('/')[0]
                        
                        # Skip loopback
                        if ip_addr != '127.0.0.1':
                            interface_info = {
                                'name': current_interface,
                                'ip': ip_addr,
                                'type': self._get_interface_type(current_interface)
                            }
                            network_info['interfaces'].append(interface_info)
                            
                            # Set primary interface (prefer wlan0, then rmnet, then eth0)
                            if not network_info['primary_ip']:
                                network_info['primary_ip'] = ip_addr
                                network_info['primary_interface'] = current_interface
                            elif 'wlan' in current_interface.lower():
                                network_info['primary_ip'] = ip_addr
                                network_info['primary_interface'] = current_interface
            
            # If no IP found with ip command, try ifconfig
            if not network_info['interfaces']:
                ifconfig_output = subprocess.run(
                    ["adb", "-s", device.serial, "shell", "ifconfig"],
                    capture_output=True,
                    text=True,
                    timeout=5
                ).stdout
                
                current_interface = None
                for line in ifconfig_output.split('\n'):
                    # Interface name
                    if line and not line.startswith(' '):
                        current_interface = line.split()[0].rstrip(':')
                    # IP address
                    elif 'inet addr:' in line and current_interface:
                        ip_addr = line.split('inet addr:')[1].split()[0]
                        if ip_addr != '127.0.0.1':
                            interface_info = {
                                'name': current_interface,
                                'ip': ip_addr,
                                'type': self._get_interface_type(current_interface)
                            }
                            network_info['interfaces'].append(interface_info)
                            
                            if not network_info['primary_ip']:
                                network_info['primary_ip'] = ip_addr
                                network_info['primary_interface'] = current_interface
            
            device.network_info = network_info
            return network_info
            
        except Exception as e:
            logger.debug(f"Failed to get network info for {device.serial}: {e}")
            return network_info
    
    def _get_interface_type(self, interface_name: str) -> str:
        """Determine interface type from name"""
        interface_lower = interface_name.lower()
        if 'wlan' in interface_lower or 'wifi' in interface_lower:
            return 'WiFi'
        elif 'eth' in interface_lower:
            return 'Ethernet'
        elif 'rmnet' in interface_lower or 'ccmni' in interface_lower:
            return 'Mobile'
        elif 'lo' in interface_lower:
            return 'Loopback'
        elif 'tun' in interface_lower or 'tap' in interface_lower:
            return 'Tunnel'
        elif 'usb' in interface_lower or 'rndis' in interface_lower:
            return 'USB'
        else:
            return 'Unknown'
    
    async def execute_adb_command(self, device: Device, command: str) -> Optional[str]:
        """Execute ADB shell command on device"""
        try:
            result = subprocess.run(
                ["adb", "-s", device.serial, "shell", command],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout
        except Exception as e:
            logger.error(f"ADB command failed on {device.serial}: {e}")
            return None