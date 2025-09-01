"""Local APK installer with split APK support"""

import os
import asyncio
import subprocess
from typing import List, Dict, Optional
from pathlib import Path
from loguru import logger
from core.device_manager import Device


class LocalAPKInstaller:
    def __init__(self):
        self.apks_dir = Path("apks")
        
    def scan_apk_folders(self) -> Dict[str, List[str]]:
        """Scan APK folder for available apps and their APK files"""
        apps = {}
        
        if not self.apks_dir.exists():
            logger.warning(f"APK directory {self.apks_dir} does not exist")
            return apps
        
        # Scan for app folders
        for item in self.apks_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                apk_files = list(item.glob("*.apk"))
                if apk_files:
                    # Sort APK files: base.apk first, then splits
                    apk_files.sort(key=lambda x: (not x.name.startswith("base"), x.name))
                    apps[item.name] = [str(f) for f in apk_files]
                    logger.debug(f"Found app '{item.name}' with {len(apk_files)} APK file(s)")
        
        return apps
    
    async def check_app_installed(self, device: Device, package_name: str) -> bool:
        """Check if an app is already installed on device"""
        try:
            result = subprocess.run(
                ["adb", "-s", device.serial, "shell", "pm", "list", "packages"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Check if package appears in the list
                return f"package:{package_name}" in result.stdout
            
        except Exception as e:
            logger.error(f"Error checking app installation on {device.serial}: {e}")
        
        return False
    
    async def get_package_name_from_apk(self, apk_path: str) -> Optional[str]:
        """Extract package name from APK file"""
        try:
            # Use aapt to get package name
            result = subprocess.run(
                ["aapt", "dump", "badging", apk_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Parse package name from output
                for line in result.stdout.split('\n'):
                    if line.startswith("package:"):
                        # Extract name='com.example.app' from the line
                        parts = line.split()
                        for part in parts:
                            if part.startswith("name="):
                                return part.split("'")[1]
            else:
                # Fallback: try with aapt2
                result = subprocess.run(
                    ["aapt2", "dump", "badging", apk_path],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if line.startswith("package:"):
                            parts = line.split()
                            for part in parts:
                                if part.startswith("name="):
                                    return part.split("'")[1]
        except FileNotFoundError:
            # aapt not found, will check after installation instead
            pass
        except Exception as e:
            logger.error(f"Error extracting package name from {apk_path}: {e}")
        
        return None
    
    async def install_apk_on_device(self, device: Device, app_name: str, apk_files: List[str], status_callback=None) -> Dict[str, any]:
        """Install APK(s) on a single device"""
        result = {
            'success': False,
            'already_installed': False,
            'message': '',
            'device': device.serial,
            'app_name': app_name
        }
        
        async def update_status(text):
            if status_callback:
                await status_callback(text)
        
        try:
            # Check if we have APK files
            if not apk_files:
                result['message'] = "No APK files found"
                await update_status("No APK files")
                return result
            
            # Get package name from base APK
            base_apk = None
            for apk in apk_files:
                if "base.apk" in apk or len(apk_files) == 1:
                    base_apk = apk
                    break
            
            if not base_apk:
                base_apk = apk_files[0]
            
            await update_status("Checking package info...")
            package_name = await self.get_package_name_from_apk(base_apk)
            
            # Check if already installed (if we have package name)
            if package_name:
                await update_status("Checking if installed...")
                if await self.check_app_installed(device, package_name):
                    result['already_installed'] = True
                    result['message'] = f"App already installed"
                    await update_status("Already installed")
                    return result
            
            # Prepare installation command
            await update_status("Preparing installation...")
            
            if len(apk_files) > 1:
                # Use install-multiple for split APKs
                cmd = ["adb", "-s", device.serial, "install-multiple", "-r", "-g"] + apk_files
                logger.debug(f"Installing split APKs for {app_name} on {device.serial}")
            else:
                # Use regular install for single APK
                cmd = ["adb", "-s", device.serial, "install", "-r", "-g", apk_files[0]]
                logger.debug(f"Installing single APK for {app_name} on {device.serial}")
            
            # Execute installation
            await update_status("Installing APK...")
            logger.debug(f"Running command: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Monitor installation with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=120  # 2 minute timeout
                )
                
                stdout_text = stdout.decode() if stdout else ""
                stderr_text = stderr.decode() if stderr else ""
                
                # Check installation result
                if process.returncode == 0 and "Success" in stdout_text:
                    result['success'] = True
                    result['message'] = "Installation successful"
                    await update_status("Installation complete!")
                    logger.debug(f"Successfully installed {app_name} on {device.serial}")
                else:
                    # Parse error message
                    error_msg = stderr_text or stdout_text
                    if "ALREADY_EXISTS" in error_msg:
                        result['already_installed'] = True
                        result['message'] = "App already installed"
                        await update_status("Already installed")
                    elif "INSTALL_FAILED_INSUFFICIENT_STORAGE" in error_msg:
                        result['message'] = "Insufficient storage"
                        await update_status("Storage full")
                    elif "INSTALL_FAILED_VERSION_DOWNGRADE" in error_msg:
                        result['message'] = "Version downgrade"
                        await update_status("Version conflict")
                    else:
                        result['message'] = f"Installation failed: {error_msg[:50]}"
                        await update_status("Installation failed")
                    
                    logger.error(f"Failed to install {app_name} on {device.serial}: {error_msg}")
                    
            except asyncio.TimeoutError:
                # Kill the process to prevent zombie
                try:
                    process.kill()
                    await process.wait()  # Ensure process is properly reaped
                except ProcessLookupError:
                    pass  # Process already terminated
                
                result['message'] = "Installation timeout"
                await update_status("Installation timeout")
                logger.error(f"Installation timeout for {app_name} on {device.serial}")
                
        except Exception as e:
            logger.error(f"Error installing {app_name} on {device.serial}: {e}")
            result['message'] = f"Error: {str(e)[:30]}"
            await update_status(f"Error: {str(e)[:20]}")
        
        return result
    
    async def install_app_on_devices(self, app_name: str, apk_files: List[str], devices: List[Device], progress_callback=None) -> List[Dict]:
        """Install an app on multiple devices in parallel"""
        results = []
        
        # Install on all devices in parallel
        tasks = []
        for device in devices:
            # Create individual status callback if progress callback provided
            if progress_callback:
                async def device_status_callback(status, dev=device):
                    await progress_callback(dev.serial, status)
                tasks.append(self.install_apk_on_device(device, app_name, apk_files, device_status_callback))
            else:
                tasks.append(self.install_apk_on_device(device, app_name, apk_files))
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        except asyncio.CancelledError:
            # Cancel all tasks if interrupted
            for task in tasks:
                if hasattr(task, 'cancel'):
                    task.cancel()
            raise
        return results