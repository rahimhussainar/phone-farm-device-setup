import asyncio
import time
from typing import List, Dict, Optional
from loguru import logger
import uiautomator2 as u2
from core.device_manager import Device


class AppManager:
    def __init__(self):
        self.play_store_package = "com.android.vending"
        
    async def open_play_store(self, device: Device) -> bool:
        """Open Google Play Store"""
        try:
            d = device.u2_device
            if not d:
                raise Exception("Device not connected")
            
            logger.info(f"[{device.serial}] Opening Play Store...")
            
            # Clear any existing apps
            d.press("home")
            await asyncio.sleep(1)
            
            # Open Play Store
            d.app_start(self.play_store_package)
            await asyncio.sleep(3)
            
            # Check if opened successfully
            if d.app_current()['package'] == self.play_store_package:
                logger.success(f"[{device.serial}] Play Store opened")
                return True
            else:
                # Try alternative method
                # Alternative Play Store launch method
                d.shell("am start -a android.intent.action.VIEW -d 'market://search'")
                await asyncio.sleep(3)
                return True
                
        except Exception as e:
            logger.error(f"[{device.serial}] Failed to open Play Store: {e}")
            return False
    
    async def search_app(self, device: Device, app_name: str) -> bool:
        """Search for an app in Play Store"""
        try:
            d = device.u2_device
            if not d:
                raise Exception("Device not connected")
            
            logger.info(f"[{device.serial}] Searching for '{app_name}'...")
            
            # Look for search button/field
            search_found = False
            
            # Try different search selectors
            selectors = [
                {"resourceId": "com.android.vending:id/search_box"},
                {"resourceId": "com.android.vending:id/search_bar"},
                {"text": "Search for apps & games"},
                {"text": "Search"},
                {"description": "Search"}
            ]
            
            for selector in selectors:
                if d(**selector).exists(timeout=2):
                    d(**selector).click()
                    search_found = True
                    break
            
            if not search_found:
                # Try clicking on general search area
                d.click(0.5, 0.1)  # Top center of screen
                await asyncio.sleep(1)
            
            # Type search query
            d.send_keys(app_name, clear=True)
            await asyncio.sleep(1)
            
            # Press enter/search
            d.press("enter")
            await asyncio.sleep(3)
            
            logger.success(f"[{device.serial}] Search completed for '{app_name}'")
            return True
            
        except Exception as e:
            logger.error(f"[{device.serial}] Failed to search app: {e}")
            return False
    
    async def install_app_from_play_store(self, device: Device, app_name: str, package_name: str) -> bool:
        """Install an app from Play Store"""
        try:
            d = device.u2_device
            if not d:
                raise Exception("Device not connected")
            
            logger.info(f"[{device.serial}] Installing '{app_name}'...")
            
            # Check if app is already installed
            if package_name in d.app_list():
                logger.info(f"[{device.serial}] '{app_name}' is already installed")
                return True
            
            # Open Play Store and search
            if not await self.open_play_store(device):
                return False
            
            if not await self.search_app(device, app_name):
                return False
            
            # Click on the app from search results
            await asyncio.sleep(2)
            
            # Try to find and click the app
            app_found = False
            selectors = [
                {"text": app_name},
                {"textContains": app_name.split()[0]},  # First word of app name
                {"resourceId": "com.android.vending:id/li_title", "instance": 0}
            ]
            
            for selector in selectors:
                if d(**selector).exists(timeout=2):
                    d(**selector).click()
                    app_found = True
                    break
            
            if not app_found:
                # Click first result
                d.click(0.5, 0.3)
            
            await asyncio.sleep(3)
            
            # Click Install button
            install_clicked = False
            install_selectors = [
                {"text": "Install"},
                {"text": "INSTALL"},
                {"text": "Get"},
                {"text": "GET"},
                {"resourceId": "com.android.vending:id/buy_button"}
            ]
            
            for selector in install_selectors:
                if d(**selector).exists(timeout=2):
                    d(**selector).click()
                    install_clicked = True
                    logger.info(f"[{device.serial}] Installation started for '{app_name}'")
                    break
            
            if not install_clicked:
                logger.warning(f"[{device.serial}] Install button not found - app might already be installed")
                return package_name in d.app_list()
            
            # Wait for installation to complete (with timeout)
            max_wait = 120  # 2 minutes
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                if package_name in d.app_list():
                    logger.success(f"[{device.serial}] '{app_name}' installed successfully")
                    return True
                
                # Check if "Open" button appeared (installation complete)
                if d(text="Open").exists() or d(text="OPEN").exists():
                    logger.success(f"[{device.serial}] '{app_name}' installed successfully")
                    return True
                
                await asyncio.sleep(5)
            
            logger.warning(f"[{device.serial}] Installation timeout for '{app_name}'")
            return False
            
        except Exception as e:
            logger.error(f"[{device.serial}] Failed to install '{app_name}': {e}")
            return False
    
    
    async def grant_app_permissions(self, device: Device, package_name: str) -> bool:
        """Grant all permissions to an app"""
        try:
            d = device.u2_device
            if not d:
                raise Exception("Device not connected")
            
            logger.info(f"[{device.serial}] Granting permissions to {package_name}...")
            
            # Common permissions for apps
            permissions = [
                "android.permission.INTERNET",
                "android.permission.ACCESS_NETWORK_STATE",
                "android.permission.ACCESS_WIFI_STATE"
            ]
            
            for permission in permissions:
                cmd = f"pm grant {package_name} {permission}"
                try:
                    d.shell(cmd)
                except:
                    pass  # Some permissions might not be grantable via ADB
            
            logger.success(f"[{device.serial}] Permissions granted to {package_name}")
            return True
            
        except Exception as e:
            logger.error(f"[{device.serial}] Failed to grant permissions: {e}")
            return False
    
    async def disable_app_auto_update(self, device: Device) -> bool:
        """Disable automatic app updates in Play Store"""
        try:
            d = device.u2_device
            if not d:
                raise Exception("Device not connected")
            
            logger.info(f"[{device.serial}] Disabling auto-update...")
            
            # Open Play Store
            d.app_start(self.play_store_package)
            await asyncio.sleep(3)
            
            # Open menu (usually profile icon or hamburger menu)
            menu_opened = False
            
            # Try profile icon (newer Play Store)
            if d(resourceId="com.android.vending:id/avatar").exists(timeout=2):
                d(resourceId="com.android.vending:id/avatar").click()
                menu_opened = True
            # Try hamburger menu (older Play Store)
            elif d(description="Show navigation drawer").exists(timeout=2):
                d(description="Show navigation drawer").click()
                menu_opened = True
            
            if not menu_opened:
                logger.warning(f"[{device.serial}] Could not open Play Store menu")
                return False
            
            await asyncio.sleep(2)
            
            # Go to Settings
            if d(text="Settings").exists(timeout=3):
                d(text="Settings").click()
                await asyncio.sleep(2)
                
                # Find and click Auto-update apps
                if d(textContains="Auto-update").exists(timeout=3):
                    d(textContains="Auto-update").click()
                    await asyncio.sleep(1)
                    
                    # Select "Don't auto-update apps"
                    if d(text="Don't auto-update apps").exists(timeout=2):
                        d(text="Don't auto-update apps").click()
                        logger.success(f"[{device.serial}] Auto-update disabled")
                        return True
            
            logger.warning(f"[{device.serial}] Could not disable auto-update")
            return False
            
        except Exception as e:
            logger.error(f"[{device.serial}] Failed to disable auto-update: {e}")
            return False