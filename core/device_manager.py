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


@dataclass
class Device:
    serial: str
    model: str = "Unknown"
    android_version: str = "Unknown"
    status: str = "disconnected"
    u2_device: Optional[u2.Device] = None
    adb_device: Optional[object] = None
    network_info: Optional[Dict] = None
    
    def __hash__(self):
        return hash(self.serial)


class DeviceManager:
    def __init__(self):
        self.devices: Dict[str, Device] = {}
        self.adb_key_path = os.path.expanduser("~/.android/adbkey")
        self._ensure_adb_key()
        
    def _ensure_adb_key(self):
        """Ensure ADB RSA key exists"""
        if not os.path.exists(self.adb_key_path):
            os.makedirs(os.path.dirname(self.adb_key_path), exist_ok=True)
            keygen(self.adb_key_path)
            logger.info(f"Generated new ADB key at {self.adb_key_path}")
    
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
    
    async def connect_device(self, device: Device) -> bool:
        """Initialize uiautomator2 connection for a device"""
        try:
            # Skip unauthorized devices
            if device.status == "unauthorized":
                logger.warning(f"Skipping unauthorized device {device.serial} - please authorize on device")
                return False
                
            # Only connect to devices with status "device" (authorized)
            if device.status != "device":
                logger.warning(f"Skipping {device.serial} - status: {device.status}")
                return False
            
            logger.info(f"Connecting to device {device.serial}...")
            
            # Initialize uiautomator2
            device.u2_device = u2.connect(device.serial)
            
            # Test connection
            info = device.u2_device.info
            device.android_version = str(info.get('version', 'Unknown'))
            
            # Update device in our dictionary
            device.status = "connected"
            self.devices[device.serial] = device
            
            logger.success(f"Connected to {device.serial} - Android {device.android_version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {device.serial}: {e}")
            device.status = "error"
            return False
    
    async def connect_all_devices(self) -> int:
        """Connect to all detected devices"""
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
        
        logger.info(f"Connecting to {len(authorized_devices)} authorized device(s)...")
        
        # Connect to devices concurrently
        tasks = [self.connect_device(device) for device in authorized_devices]
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        except asyncio.CancelledError:
            # Cancel all tasks if interrupted
            for task in tasks:
                if hasattr(task, 'cancel'):
                    task.cancel()
            raise
        
        connected_count = sum(results)
        logger.info(f"Successfully connected to {connected_count}/{len(authorized_devices)} authorized devices")
        
        return connected_count
    
    def get_connected_devices(self) -> List[Device]:
        """Get all connected devices"""
        return [d for d in self.devices.values() if d.status == "connected"]
    
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