"""Optimized ADB command execution for large device farms"""

import asyncio
import subprocess
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from loguru import logger
import time

class BatchADB:
    """Execute ADB commands in parallel across multiple devices efficiently"""
    
    def __init__(self, max_workers: int = 50):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def run_command_batch(
        self, 
        devices: List[str], 
        command: List[str],
        timeout: float = 10.0
    ) -> Dict[str, Any]:
        """Run the same ADB command on multiple devices in parallel
        
        Args:
            devices: List of device serial numbers
            command: ADB command to run (without 'adb -s <serial>')
            timeout: Command timeout in seconds
            
        Returns:
            Dict mapping device serial to result
        """
        start_time = time.time()
        
        async def run_single(serial: str) -> tuple[str, dict]:
            """Run command on a single device"""
            full_cmd = ["adb", "-s", serial] + command
            
            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.executor,
                    subprocess.run,
                    full_cmd,
                    {
                        "capture_output": True,
                        "text": True,
                        "timeout": timeout
                    }
                )
                
                return serial, {
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                }
            except subprocess.TimeoutExpired:
                return serial, {
                    "success": False,
                    "error": "Command timed out",
                    "timeout": True
                }
            except Exception as e:
                return serial, {
                    "success": False,
                    "error": str(e)
                }
        
        # Run all commands in parallel
        tasks = [run_single(serial) for serial in devices]
        results = await asyncio.gather(*tasks)
        
        # Convert to dict
        results_dict = dict(results)
        
        elapsed = time.time() - start_time
        if len(devices) > 10:
            logger.debug(f"Batch ADB: {len(devices)} devices, {elapsed:.2f}s ({len(devices)/elapsed:.1f} devices/sec)")
        
        return results_dict
    
    async def get_device_properties_batch(self, devices: List[str]) -> Dict[str, Dict]:
        """Get device properties for multiple devices in parallel"""
        
        async def get_props(serial: str) -> tuple[str, dict]:
            """Get properties for a single device"""
            props = {}
            
            # Commands to get various properties
            prop_commands = {
                "model": ["shell", "getprop", "ro.product.model"],
                "android_version": ["shell", "getprop", "ro.build.version.release"],
                "sdk": ["shell", "getprop", "ro.build.version.sdk"],
                "brand": ["shell", "getprop", "ro.product.brand"],
                "ip": ["shell", "ip", "addr", "show", "wlan0"]
            }
            
            for prop_name, cmd in prop_commands.items():
                full_cmd = ["adb", "-s", serial] + cmd
                try:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        self.executor,
                        subprocess.run,
                        full_cmd,
                        {
                            "capture_output": True,
                            "text": True,
                            "timeout": 2
                        }
                    )
                    if result.returncode == 0:
                        if prop_name == "ip":
                            # Extract IP from output
                            for line in result.stdout.split('\n'):
                                if 'inet ' in line:
                                    ip = line.split('inet ')[1].split('/')[0]
                                    props["ip"] = ip
                                    break
                        else:
                            props[prop_name] = result.stdout.strip()
                except:
                    pass
            
            return serial, props
        
        # Get properties for all devices in parallel
        tasks = [get_props(serial) for serial in devices]
        results = await asyncio.gather(*tasks)
        
        return dict(results)
    
    async def install_apk_batch(
        self, 
        devices: List[str], 
        apk_path: str,
        grant_permissions: bool = True
    ) -> Dict[str, Any]:
        """Install an APK on multiple devices in parallel
        
        Args:
            devices: List of device serial numbers
            apk_path: Path to the APK file
            grant_permissions: Whether to grant all permissions
            
        Returns:
            Dict mapping device serial to installation result
        """
        cmd = ["install"]
        if grant_permissions:
            cmd.append("-g")
        cmd.append(apk_path)
        
        return await self.run_command_batch(devices, cmd, timeout=60.0)
    
    async def launch_app_batch(
        self,
        devices: List[str],
        package: str,
        activity: str = None
    ) -> Dict[str, Any]:
        """Launch an app on multiple devices in parallel"""
        
        if activity:
            cmd = ["shell", "am", "start", "-n", f"{package}/{activity}"]
        else:
            # Use monkey to launch the app by package name
            cmd = ["shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1"]
        
        return await self.run_command_batch(devices, cmd, timeout=5.0)
    
    def cleanup(self):
        """Cleanup thread pool"""
        self.executor.shutdown(wait=False)