"""Removes all non-system apps from devices using allowlist approach"""

import subprocess
import asyncio
from typing import List, Dict
from loguru import logger
from core.device_manager import Device
from config.bloatware import SAFE_TO_REMOVE, SAFE_TO_DISABLE, is_bloatware
from config.allowlist import get_full_allowlist, should_remove

# Apps to keep (whitelist) - for backward compatibility
WHITELIST = [
    "com.zhiliaoapp.musically",  # TikTok
    "com.scheler.superproxy",  # Super Proxy
]

class BloatwareRemover:
    """Remove all non-system apps except whitelisted ones"""
    
    def __init__(self, use_allowlist=False):  # DEFAULT TO FALSE FOR SAFETY
        self.removed_apps = {}
        self.whitelist = WHITELIST
        self.use_allowlist = use_allowlist
        # Get allowlist for the new approach
        self.allowlist = get_full_allowlist(include_optional=False, include_phone_farm=True) if use_allowlist else None
        
        # WARNING flag
        self.aggressive_mode = use_allowlist
    
    async def get_all_packages(self, device: Device) -> List[str]:
        """Get all packages on device (including system apps)"""
        try:
            # Get ALL packages, not just third-party
            cmd = ["adb", "-s", device.serial, "shell", "pm", "list", "packages"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                packages = []
                for line in result.stdout.strip().split('\n'):
                    if line.startswith('package:'):
                        package = line.replace('package:', '').strip()
                        packages.append(package)
                return packages
            else:
                logger.error(f"Failed to get packages for {device.serial}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting packages for {device.serial}: {e}")
            return []
    
    async def get_non_system_packages(self, device: Device) -> List[str]:
        """Get all third-party (non-system) packages on device"""
        try:
            # Use -3 flag to get only third-party packages
            cmd = ["adb", "-s", device.serial, "shell", "pm", "list", "packages", "-3"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                packages = []
                for line in result.stdout.strip().split('\n'):
                    if line.startswith('package:'):
                        package = line.replace('package:', '').strip()
                        packages.append(package)
                return packages
            else:
                logger.error(f"Failed to get packages for {device.serial}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting packages for {device.serial}: {e}")
            return []
    
    
    async def uninstall_package(self, device: Device, package: str) -> bool:
        """Uninstall a package from device (user-level only for safety)"""
        try:
            # Only uninstall for current user (can be restored with factory reset)
            cmd = ["adb", "-s", device.serial, "shell", "pm", "uninstall", "--user", "0", package]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 or "Success" in result.stdout:
                logger.info(f"Uninstalled {package} from {device.serial}")
                if device.serial not in self.removed_apps:
                    self.removed_apps[device.serial] = []
                self.removed_apps[device.serial].append(package)
                return True
            else:
                logger.warning(f"Failed to uninstall {package} from {device.serial}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error uninstalling {package} from {device.serial}: {e}")
            return False
    
    
    async def remove_bloatware_from_list(self, device: Device) -> Dict:
        """Remove bloatware based on the predefined list"""
        results = {
            'removed': [],
            'failed': [],
            'skipped': [],
            'total': 0
        }
        
        # Get all packages (including system)
        all_packages = await self.get_all_packages(device)
        
        # Filter for bloatware
        bloatware_to_remove = []
        for package in all_packages:
            if package in self.whitelist:
                logger.info(f"Skipping whitelisted app: {package}")
                results['skipped'].append(package)
                continue
                
            if package in SAFE_TO_REMOVE or is_bloatware(package):
                bloatware_to_remove.append(package)
        
        results['total'] = len(bloatware_to_remove)
        logger.info(f"Found {len(bloatware_to_remove)} bloatware apps to remove on {device.serial}")
        
        # Remove each bloatware package
        for package in bloatware_to_remove:
            logger.info(f"Attempting to remove {package}...")
            if await self.uninstall_package(device, package):
                results['removed'].append(package)
            else:
                results['failed'].append(package)
        
        logger.info(f"Bloatware removal complete for {device.serial}: "
                   f"{len(results['removed'])} removed, {len(results['skipped'])} kept, {len(results['failed'])} failed")
        
        return results
    
    async def remove_with_allowlist(self, device: Device) -> Dict:
        """Remove all apps NOT in the allowlist (aggressive cleanup)"""
        results = {
            'removed': [],
            'failed': [],
            'skipped': [],
            'total': 0
        }
        
        # Get all packages on device
        all_packages = await self.get_all_packages(device)
        
        # Add our special whitelist apps to allowlist temporarily
        extended_allowlist = self.allowlist.copy() if self.allowlist else []
        extended_allowlist.extend(self.whitelist)
        
        # Determine what to remove
        packages_to_remove = []
        for package in all_packages:
            if should_remove(package, extended_allowlist):
                packages_to_remove.append(package)
            else:
                results['skipped'].append(package)
        
        results['total'] = len(packages_to_remove)
        logger.info(f"Found {len(packages_to_remove)} packages to remove on {device.serial} (allowlist mode)")
        
        # Remove each package
        for package in packages_to_remove:
            # Skip gaming and bloatware apps with higher priority
            if any(keyword in package.lower() for keyword in ["game", "solitaire", "monopoly", "candy", "facebook", "instagram"]):
                logger.info(f"Removing bloatware/game: {package}")
            
            if await self.uninstall_package(device, package):
                results['removed'].append(package)
            else:
                # Try disable if uninstall fails
                try:
                    cmd = ["adb", "-s", device.serial, "shell", "pm", "disable-user", "--user", "0", package]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    if result.returncode == 0 or "disabled" in result.stdout.lower():
                        logger.info(f"Disabled {package} on {device.serial}")
                        results['removed'].append(package)
                    else:
                        results['failed'].append(package)
                except:
                    results['failed'].append(package)
        
        logger.info(f"Allowlist cleanup complete for {device.serial}: "
                   f"{len(results['removed'])} removed, {len(results['skipped'])} kept, {len(results['failed'])} failed")
        
        return results
    
    async def remove_all_non_system_apps(self, device: Device) -> Dict:
        """Remove all non-system apps from device (except whitelisted)"""
        results = {
            'removed': [],
            'failed': [],
            'skipped': [],
            'total': 0
        }
        
        # Get all third-party packages
        packages = await self.get_non_system_packages(device)
        results['total'] = len(packages)
        
        logger.info(f"Found {len(packages)} non-system apps on {device.serial}")
        
        # Remove each package (skip whitelisted)
        for package in packages:
            if package in self.whitelist:
                logger.info(f"Skipping whitelisted app: {package}")
                results['skipped'].append(package)
                continue
                
            if await self.uninstall_package(device, package):
                results['removed'].append(package)
            else:
                results['failed'].append(package)
        
        logger.info(f"Removal complete for {device.serial}: "
                   f"{len(results['removed'])} removed, {len(results['skipped'])} kept, {len(results['failed'])} failed")
        
        return results
    
    
