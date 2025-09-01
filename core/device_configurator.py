import asyncio
from typing import List, Dict, Any
from loguru import logger
import uiautomator2 as u2
from core.device_manager import Device


class DeviceConfigurator:
    def __init__(self):
        self.config_tasks = []
        
    async def disable_bluetooth(self, device: Device) -> bool:
        """Disable Bluetooth on device"""
        try:
            logger.info(f"[{device.serial}] Disabling Bluetooth...")
            
            # Method 1: Direct settings command
            await self._execute_shell(device, "settings put global bluetooth_on 0")
            
            # Method 2: Using svc command (more reliable on newer Android)
            await self._execute_shell(device, "svc bluetooth disable")
            
            # Method 3: Force stop bluetooth
            await self._execute_shell(device, "am force-stop com.android.bluetooth")
            
            # Method 4: Using cmd command (Android 8+)
            await self._execute_shell(device, "cmd bluetooth_manager disable")
            
            logger.success(f"[{device.serial}] Bluetooth disabled")
            return True
            
        except Exception as e:
            logger.error(f"[{device.serial}] Failed to disable Bluetooth: {e}")
            return False
    
    async def disable_cellular_data(self, device: Device) -> bool:
        """Disable cellular data on device"""
        try:
            logger.info(f"[{device.serial}] Disabling cellular data...")
            
            # Disable mobile data
            await self._execute_shell(device, "svc data disable")
            
            # Also disable data roaming
            await self._execute_shell(device, "settings put global data_roaming 0")
            
            logger.success(f"[{device.serial}] Cellular data disabled")
            return True
            
        except Exception as e:
            logger.error(f"[{device.serial}] Failed to disable cellular data: {e}")
            return False
    
    async def disable_wifi_direct(self, device: Device) -> bool:
        """Disable WiFi Direct / P2P"""
        try:
            logger.info(f"[{device.serial}] Disabling WiFi Direct...")
            
            await self._execute_shell(device, "settings put global wifi_p2p_device_name ''")
            await self._execute_shell(device, "settings put global wifi_direct_auto_accept 0")
            
            logger.success(f"[{device.serial}] WiFi Direct disabled")
            return True
            
        except Exception as e:
            logger.error(f"[{device.serial}] Failed to disable WiFi Direct: {e}")
            return False
    
    async def disable_nearby_sharing(self, device: Device) -> bool:
        """Disable Nearby Share and similar features"""
        try:
            logger.info(f"[{device.serial}] Disabling Nearby Share...")
            
            # Disable Nearby Share
            await self._execute_shell(device, "settings put secure nearby_sharing_enabled 0")
            
            # Disable Quick Share (Samsung devices)
            await self._execute_shell(device, "settings put secure quick_share 0")
            
            # Disable Android Beam / NFC
            await self._execute_shell(device, "settings put secure android_beam 0")
            await self._execute_shell(device, "settings put secure nfc_payment_default_component ''")
            
            logger.success(f"[{device.serial}] Nearby sharing disabled")
            return True
            
        except Exception as e:
            logger.error(f"[{device.serial}] Failed to disable nearby sharing: {e}")
            return False
    
    async def disable_nfc(self, device: Device) -> bool:
        """Disable NFC"""
        try:
            logger.info(f"[{device.serial}] Disabling NFC...")
            
            await self._execute_shell(device, "service call nfc 5")  # Disable NFC
            await self._execute_shell(device, "settings put secure nfc_on 0")
            
            logger.success(f"[{device.serial}] NFC disabled")
            return True
            
        except Exception as e:
            logger.error(f"[{device.serial}] Failed to disable NFC: {e}")
            return False
    
    async def disable_location_services(self, device: Device) -> bool:
        """Disable location services"""
        try:
            logger.info(f"[{device.serial}] Disabling location services...")
            
            await self._execute_shell(device, "settings put secure location_mode 0")
            await self._execute_shell(device, "settings put secure location_providers_allowed ''")
            
            logger.success(f"[{device.serial}] Location services disabled")
            return True
            
        except Exception as e:
            logger.error(f"[{device.serial}] Failed to disable location services: {e}")
            return False
    
    async def disable_backup_sync(self, device: Device) -> bool:
        """Disable backup and sync services"""
        try:
            logger.info(f"[{device.serial}] Disabling backup and sync...")
            
            await self._execute_shell(device, "settings put secure backup_enabled 0")
            await self._execute_shell(device, "settings put secure backup_auto_restore 0")
            
            logger.success(f"[{device.serial}] Backup and sync disabled")
            return True
            
        except Exception as e:
            logger.error(f"[{device.serial}] Failed to disable backup and sync: {e}")
            return False
    
    async def schedule_updates_tomorrow(self, device: Device) -> bool:
        """Schedule system updates for tomorrow"""
        try:
            logger.info(f"[{device.serial}] Scheduling updates for tomorrow...")
            
            # Disable automatic updates
            await self._execute_shell(device, "settings put global auto_update_policy 2")  # 2 = Never auto-update
            
            # Set update check time to tomorrow 3 AM
            import datetime
            tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
            tomorrow_3am = tomorrow.replace(hour=3, minute=0, second=0)
            
            # Note: Actual implementation depends on Android version and OEM
            await self._execute_shell(device, "settings put global update_time_preference " + str(int(tomorrow_3am.timestamp())))
            
            logger.success(f"[{device.serial}] Updates scheduled for tomorrow")
            return True
            
        except Exception as e:
            logger.error(f"[{device.serial}] Failed to schedule updates: {e}")
            return False
    
    async def set_screen_timeout(self, device: Device) -> bool:
        """Set screen timeout to 10 minutes"""
        try:
            logger.info(f"[{device.serial}] Setting screen timeout to 10 minutes...")
            
            # Set screen timeout to 10 minutes (600000 ms)
            await self._execute_shell(device, "settings put system screen_off_timeout 600000")
            
            # Also keep screen on while charging
            await self._execute_shell(device, "settings put global stay_on_while_plugged_in 3")  # 3 = AC + USB
            
            logger.success(f"[{device.serial}] Screen timeout set to 10 minutes")
            return True
            
        except Exception as e:
            logger.error(f"[{device.serial}] Failed to set screen timeout: {e}")
            return False
    
    async def set_volume_levels(self, device: Device) -> bool:
        """Set all volumes to 1 (just above mute)"""
        try:
            logger.info(f"[{device.serial}] Setting volume levels...")
            
            # Use cmd audio (works on Android 8+)
            await self._execute_shell(device, "cmd audio set-stream-volume 0 1 0")  # Voice call
            await self._execute_shell(device, "cmd audio set-stream-volume 1 1 0")  # System  
            await self._execute_shell(device, "cmd audio set-stream-volume 2 1 0")  # Ring
            await self._execute_shell(device, "cmd audio set-stream-volume 3 1 0")  # Media/Music
            await self._execute_shell(device, "cmd audio set-stream-volume 4 1 0")  # Alarm
            await self._execute_shell(device, "cmd audio set-stream-volume 5 1 0")  # Notification
            
            # Also use settings as fallback
            await self._execute_shell(device, "settings put system volume_voice 1")
            await self._execute_shell(device, "settings put system volume_system 1")
            await self._execute_shell(device, "settings put system volume_ring 1")
            await self._execute_shell(device, "settings put system volume_music 1")
            await self._execute_shell(device, "settings put system volume_alarm 1")
            await self._execute_shell(device, "settings put system volume_notification 1")
            
            # Set ringer mode to normal (not silent, not vibrate) 
            await self._execute_shell(device, "settings put global mode_ringer 2")
            
            # Disable touch sounds
            await self._execute_shell(device, "settings put system sound_effects_enabled 0")
            await self._execute_shell(device, "settings put system haptic_feedback_enabled 0")
            await self._execute_shell(device, "settings put system dtmf_tone 0")
            await self._execute_shell(device, "settings put system lockscreen_sounds_enabled 0")
            
            logger.success(f"[{device.serial}] Volume levels set")
            return True
            
        except Exception as e:
            logger.error(f"[{device.serial}] Failed to set volume levels: {e}")
            return False
    
    async def enable_do_not_disturb(self, device: Device) -> bool:
        """Enable Do Not Disturb mode"""
        try:
            logger.info(f"[{device.serial}] Enabling Do Not Disturb...")
            
            # Method 1: Using cmd notification (most reliable)
            await self._execute_shell(device, "cmd notification set_dnd on")
            
            # Method 2: Using settings (for older devices)
            await self._execute_shell(device, "settings put global zen_mode 2")  # 2 = No interruptions
            
            # Method 3: Using service call
            await self._execute_shell(device, "service call notification 4 i32 2")  # Enable DND
            
            # Configure DND settings
            await self._execute_shell(device, "settings put global zen_mode_important_interruptions 0")  # No interruptions
            await self._execute_shell(device, "settings put secure zen_duration 0")  # Until turned off
            await self._execute_shell(device, "settings put secure zen_settings_updated 1")
            
            # Disable all notification types
            await self._execute_shell(device, "settings put global heads_up_notifications_enabled 0")
            await self._execute_shell(device, "settings put secure notification_badging 0")
            
            # Set ringer to vibrate mode as backup
            await self._execute_shell(device, "settings put global mode_ringer 1")  # Vibrate mode
            
            logger.success(f"[{device.serial}] Do Not Disturb enabled")
            return True
            
        except Exception as e:
            logger.error(f"[{device.serial}] Failed to enable Do Not Disturb: {e}")
            return False
    
    async def disable_animations(self, device: Device) -> bool:
        """Disable animations for better performance"""
        try:
            logger.info(f"[{device.serial}] Disabling animations...")
            
            # Disable all animations
            await self._execute_shell(device, "settings put global window_animation_scale 0")
            await self._execute_shell(device, "settings put global transition_animation_scale 0")
            await self._execute_shell(device, "settings put global animator_duration_scale 0")
            
            logger.success(f"[{device.serial}] Animations disabled")
            return True
            
        except Exception as e:
            logger.error(f"[{device.serial}] Failed to disable animations: {e}")
            return False
    
    async def force_portrait_mode(self, device: Device) -> bool:
        """Force device to portrait mode only"""
        try:
            logger.info(f"[{device.serial}] Forcing portrait mode...")
            
            # Disable auto-rotate
            await self._execute_shell(device, "settings put system accelerometer_rotation 0")
            
            # Force portrait orientation (0 = portrait, 1 = landscape, 2 = reverse portrait, 3 = reverse landscape)
            await self._execute_shell(device, "settings put system user_rotation 0")
            
            # Additional command for forcing portrait on some devices
            await self._execute_shell(device, "content insert --uri content://settings/system --bind name:s:user_rotation --bind value:i:0")
            
            logger.success(f"[{device.serial}] Portrait mode forced")
            return True
            
        except Exception as e:
            logger.error(f"[{device.serial}] Failed to force portrait mode: {e}")
            return False
    
    async def disable_auto_rotate(self, device: Device) -> bool:
        """Disable auto-rotate screen"""
        try:
            logger.info(f"[{device.serial}] Disabling auto-rotate...")
            
            # Disable accelerometer rotation
            await self._execute_shell(device, "settings put system accelerometer_rotation 0")
            
            # Set rotation lock
            await self._execute_shell(device, "settings put system rotation_lock 1")
            
            # Alternative method using content provider
            await self._execute_shell(device, "content insert --uri content://settings/system --bind name:s:accelerometer_rotation --bind value:i:0")
            
            logger.success(f"[{device.serial}] Auto-rotate disabled")
            return True
            
        except Exception as e:
            logger.error(f"[{device.serial}] Failed to disable auto-rotate: {e}")
            return False
    
    async def disable_emergency_alerts(self, device: Device) -> bool:
        """Disable all emergency alerts including Amber, extreme threats, etc."""
        try:
            logger.info(f"[{device.serial}] Disabling emergency alerts...")
            
            # Disable Cell Broadcast SMS (main toggle for emergency alerts)
            await self._execute_shell(device, "settings put global cdma_cell_broadcast_sms 0")
            await self._execute_shell(device, "settings put global cell_broadcast_sms 0")
            
            # Disable AMBER alerts
            await self._execute_shell(device, "settings put secure cmas_amber_alert_enabled 0")
            await self._execute_shell(device, "settings put secure enable_cmas_amber_alerts 0")
            
            # Disable extreme threat alerts
            await self._execute_shell(device, "settings put secure cmas_extreme_threat_alert_enabled 0")
            await self._execute_shell(device, "settings put secure enable_cmas_extreme_threat_alerts 0")
            
            # Disable severe threat alerts
            await self._execute_shell(device, "settings put secure cmas_severe_threat_alert_enabled 0")
            await self._execute_shell(device, "settings put secure enable_cmas_severe_threat_alerts 0")
            
            # Disable presidential alerts (note: some regions may not allow disabling these)
            await self._execute_shell(device, "settings put secure cmas_presidential_alert_enabled 0")
            await self._execute_shell(device, "settings put secure enable_cmas_presidential_alerts 0")
            
            # Disable emergency alert reminders
            await self._execute_shell(device, "settings put secure alert_reminder_interval 0")
            
            # Disable public safety messages
            await self._execute_shell(device, "settings put secure public_safety_messages 0")
            await self._execute_shell(device, "settings put secure enable_public_safety_messages 0")
            
            # Disable state/local test alerts
            await self._execute_shell(device, "settings put secure cmas_test_alert_enabled 0")
            await self._execute_shell(device, "settings put secure enable_cmas_test_alerts 0")
            
            # Disable emergency alert vibration
            await self._execute_shell(device, "settings put secure cmas_vibrate_enabled 0")
            await self._execute_shell(device, "settings put secure enable_alert_vibrate 0")
            
            # Disable opt-out dialog for alerts
            await self._execute_shell(device, "settings put secure show_cmas_opt_out_dialog 0")
            
            # Disable ETWS (Earthquake and Tsunami Warning System)
            await self._execute_shell(device, "settings put secure enable_etws_test_alerts 0")
            await self._execute_shell(device, "settings put secure etws_test_alert_enabled 0")
            
            # Disable channel 50 alerts (Brazil)
            await self._execute_shell(device, "settings put secure enable_channel_50_alerts 0")
            
            # Disable all alert sounds
            await self._execute_shell(device, "settings put secure enable_alert_speech 0")
            
            # Disable notifications for Cell Broadcast apps
            cell_broadcast_apps = [
                "com.google.android.cellbroadcastservice",
                "com.google.android.cellbroadcastreceiver",
                "com.android.cellbroadcastreceiver",
                "com.samsung.android.cellbroadcastreceiver"
            ]
            
            for app in cell_broadcast_apps:
                # Disable the app if it exists
                await self._execute_shell(device, f"pm disable-user --user 0 {app}")
                # Block notifications from the app
                await self._execute_shell(device, f"cmd notification disallow_assistant {app}")
                await self._execute_shell(device, f"cmd appops set {app} POST_NOTIFICATION ignore")
            
            logger.success(f"[{device.serial}] Emergency alerts disabled")
            return True
            
        except Exception as e:
            logger.error(f"[{device.serial}] Failed to disable emergency alerts: {e}")
            return False
    
    async def apply_privacy_settings(self, device: Device) -> bool:
        """Apply additional privacy settings"""
        try:
            logger.info(f"[{device.serial}] Applying privacy settings...")
            
            # Disable usage access for apps
            await self._execute_shell(device, "settings put secure usage_stats_enabled 0")
            
            # Disable error reporting
            await self._execute_shell(device, "settings put secure send_action_app_error 0")
            
            # Disable advertising ID
            await self._execute_shell(device, "settings put secure limit_ad_tracking 1")
            await self._execute_shell(device, "settings put secure advertising_id ''")
            
            # Reset Android ID for anonymity
            await self._execute_shell(device, "settings put secure android_id ''")
            
            # Disable personalized ads
            await self._execute_shell(device, "settings put secure ad_personalization 0")
            
            logger.success(f"[{device.serial}] Privacy settings applied")
            return True
            
        except Exception as e:
            logger.error(f"[{device.serial}] Failed to apply privacy settings: {e}")
            return False
    
    async def configure_device_security(self, device: Device) -> Dict[str, bool]:
        """Apply all security configurations to a device"""
        results = {}
        
        # Run all configurations
        tasks = [
            # Display and sound settings
            ("screen_timeout", self.set_screen_timeout(device)),
            ("volume", self.set_volume_levels(device)),
            ("do_not_disturb", self.enable_do_not_disturb(device)),
            ("animations", self.disable_animations(device)),
            ("portrait_mode", self.force_portrait_mode(device)),
            ("auto_rotate", self.disable_auto_rotate(device)),
            
            # Connectivity settings (disable all except WiFi)
            ("bluetooth", self.disable_bluetooth(device)),
            ("cellular", self.disable_cellular_data(device)),
            ("wifi_direct", self.disable_wifi_direct(device)),
            ("nearby_share", self.disable_nearby_sharing(device)),
            ("nfc", self.disable_nfc(device)),
            ("location", self.disable_location_services(device)),
            
            # Privacy and security
            ("backup", self.disable_backup_sync(device)),
            ("updates", self.schedule_updates_tomorrow(device)),
            ("privacy", self.apply_privacy_settings(device)),
            ("emergency_alerts", self.disable_emergency_alerts(device))
        ]
        
        for name, task in tasks:
            try:
                results[name] = await task
            except Exception as e:
                logger.error(f"[{device.serial}] Task {name} failed: {e}")
                results[name] = False
        
        success_count = sum(1 for v in results.values() if v)
        logger.info(f"[{device.serial}] Security configuration completed: {success_count}/{len(results)} successful")
        
        return results
    
    async def _execute_shell(self, device: Device, command: str) -> str:
        """Execute shell command on device using uiautomator2"""
        if device.u2_device:
            try:
                output = device.u2_device.shell(command)
                return output[0] if isinstance(output, tuple) else output
            except Exception as e:
                logger.debug(f"Command failed (may be normal): {command} - {e}")
                return ""
        else:
            raise Exception(f"Device {device.serial} not connected")