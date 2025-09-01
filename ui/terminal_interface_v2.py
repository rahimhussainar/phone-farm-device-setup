"""Enhanced terminal interface with arrow key navigation and forest green theme"""

import asyncio
import sys
import subprocess
from typing import List, Dict, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID
import time
from rich.live import Live
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich import box
from loguru import logger

from core.device_manager import Device, DeviceManager
from core.device_configurator import DeviceConfigurator
from core.app_manager import AppManager
from core.local_apk_installer import LocalAPKInstaller
from core.bloatware_remover import BloatwareRemover
from core.fast_startup import FastStartup
from core.batch_adb import BatchADB
from ui.interactive_menu import InteractiveMenu, create_menu_items, THEME

try:
    from config.farm_settings import PERFORMANCE, DISPLAY
except ImportError:
    PERFORMANCE = {'fast_mode_threshold': 20, 'auto_continue_threshold': 20}
    DISPLAY = {'show_metrics': True}


class EnhancedTerminalInterface:
    def __init__(self):
        self.console = Console()
        self.menu = InteractiveMenu(self.console)
        self.device_manager = DeviceManager()
        self.configurator = DeviceConfigurator()
        self.app_manager = AppManager()
        self.local_apk_installer = LocalAPKInstaller()
        self.bloatware_remover = BloatwareRemover()
        self.batch_adb = BatchADB()
        self.selected_devices: List[Device] = []
    
    async def select_devices_interactive(self, devices: List[Device]) -> List[Device]:
        """Interactive device selection with arrow keys"""
        if not devices:
            self.console.print(f"[{THEME['error']}]No devices available[/{THEME['error']}]")
            return []
        
        # Initialize selected devices list
        selected_devices = []
        self.menu.selected_index = 0
        
        # Build initial menu items
        menu_items = []
        menu_items.append({
            'icon': '[A]',
            'label': 'Select All',
            'action': 'all'
        })
        
        for idx, device in enumerate(devices, 1):
            icon = f'[{idx}]'  # Initially none selected
            menu_items.append({
                'icon': icon,
                'label': f"{device.serial} ({device.model})",
                'action': device.serial,
                'device': device
            })
        
        menu_items.append({
            'icon': 'b',
            'label': 'Back',
            'action': 'back'
        })
        
        while True:
            self.menu.clear_screen()
            self.menu.display_header()
            
            # Show selected devices
            if selected_devices:
                self.console.print(f"[{THEME['dim']}]Selected: [{THEME['secondary']}]{len(selected_devices)}[/{THEME['secondary']}] device(s)[/{THEME['dim']}]")
                self.console.print()
            
            # Show menu
            selection = self.menu.navigate_menu(menu_items, len(devices), len([d for d in devices if d.status == "connected"]))
            
            if not selection or selection['action'] == 'back':
                break
            elif selection['action'] == 'all':
                return devices
            elif 'device' in selection:
                device = selection['device']
                if device in selected_devices:
                    selected_devices.remove(device)
                else:
                    selected_devices.append(device)
                
                # Update menu item to show selection status
                for i, item in enumerate(menu_items):
                    if item.get('device') == device:
                        if device in selected_devices:
                            item['icon'] = '[✓]'
                        else:
                            # Find the device index
                            device_idx = devices.index(device) + 1
                            item['icon'] = f'[{device_idx}]'
        
        return selected_devices
    
    async def show_progress_enhanced(self, task_name: str, devices: List[Device], task_func):
        """Enhanced progress display with forest green theme"""
        with Progress(
            SpinnerColumn(style=THEME['accent']),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(style=THEME['primary'], complete_style=THEME['success']),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%", style=THEME['text']),
            console=self.console
        ) as progress:
            
            task = progress.add_task(f"[{THEME['text']}] {task_name}...", total=len(devices))
            
            results = []
            for device in devices:
                try:
                    result = await task_func(device)
                    results.append((device, result))
                    status = "✓" if result else "✗"
                    color = THEME['success'] if result else THEME['error']
                    self.console.print(f"  [{color}]{status}[/{color}] {device.serial}", style=THEME['text'])
                except Exception as e:
                    logger.error(f"Error processing {device.serial}: {e}")
                    results.append((device, False))
                    self.console.print(f"  [{THEME['error']}]✗[/{THEME['error']}] {device.serial}: {str(e)[:30]}")
                
                progress.update(task, advance=1)
            
            return results
    
    async def refresh_connections(self):
        """Refresh all device connections - called from view_status now"""
        self.console.print(f"\n[{THEME['dim']}]Refreshing device connections...[/{THEME['dim']}]")
        
        # Rescan for new devices (preserves existing connections)
        await self.device_manager.scan_devices()
        
        # Try to connect to any authorized but not connected devices
        devices = list(self.device_manager.devices.values())
        authorized_not_connected = [d for d in devices if d.status == "device"]
        
        if authorized_not_connected:
            if len(authorized_not_connected) == 1:
                self.console.print(f"[{THEME['dim']}]Connecting to 1 authorized device...[/{THEME['dim']}]")
            else:
                self.console.print(f"[{THEME['dim']}]Connecting to {len(authorized_not_connected)} authorized devices in parallel...[/{THEME['dim']}]")
            count = await self.device_manager.connect_all_devices()
            if count > 0:
                if count == 1:
                    self.console.print(f"[{THEME['success']}]✓ Connected to 1 device[/{THEME['success']}]")
                else:
                    self.console.print(f"[{THEME['success']}]✓ Connected to {count} devices in parallel[/{THEME['success']}]")
    
    async def select_devices_for_install(self, devices: List[Device], action: str = None) -> List[Device]:
        """Select devices for app installation with spacebar"""
        if not devices:
            return []
        
        selected = set()
        current_index = 0
        
        while True:
            self.menu.clear_screen()
            self.menu.display_header()
            self.console.print()
            
            # Show action description based on what we're doing
            if action == "configure":
                self.console.print(f"[{THEME['primary']}]Configure Device Settings[/{THEME['primary']}]")
                self.console.print(f"[{THEME['dim']}]Optimized settings for phone farm operation:[/{THEME['dim']}]")
                self.console.print()
                self.console.print(f"[{THEME['secondary']}]Display & Sound:[/{THEME['secondary']}]")
                self.console.print(f"[{THEME['dim']}]  • Set screen timeout to 10 minutes[/{THEME['dim']}]")
                self.console.print(f"[{THEME['dim']}]  • Keep screen on while charging[/{THEME['dim']}]")
                self.console.print(f"[{THEME['dim']}]  • Set volume to minimum (1 above mute)[/{THEME['dim']}]")
                self.console.print(f"[{THEME['dim']}]  • Enable Do Not Disturb mode[/{THEME['dim']}]")
                self.console.print(f"[{THEME['dim']}]  • Disable touch sounds and haptic feedback[/{THEME['dim']}]")
                self.console.print()
                self.console.print(f"[{THEME['secondary']}]Connectivity (WiFi Only):[/{THEME['secondary']}]")
                self.console.print(f"[{THEME['dim']}]  • Disable Bluetooth[/{THEME['dim']}]")
                self.console.print(f"[{THEME['dim']}]  • Disable cellular data[/{THEME['dim']}]")
                self.console.print(f"[{THEME['dim']}]  • Disable NFC[/{THEME['dim']}]")
                self.console.print(f"[{THEME['dim']}]  • Disable location services[/{THEME['dim']}]")
                self.console.print(f"[{THEME['dim']}]  • Disable file sharing & nearby devices[/{THEME['dim']}]")
                self.console.print()
                self.console.print(f"[{THEME['secondary']}]Privacy & Performance:[/{THEME['secondary']}]")
                self.console.print(f"[{THEME['dim']}]  • Disable all animations (faster UI)[/{THEME['dim']}]")
                self.console.print(f"[{THEME['dim']}]  • Reset advertising ID[/{THEME['dim']}]")
                self.console.print(f"[{THEME['dim']}]  • Disable usage statistics & error reporting[/{THEME['dim']}]")
                self.console.print(f"[{THEME['dim']}]  • Disable auto-updates (manual control)[/{THEME['dim']}]")
                self.console.print(f"[{THEME['dim']}]  • Disable backup & sync[/{THEME['dim']}]")
            elif action == "bloatware":
                self.console.print(f"[{THEME['primary']}]Remove Bloatware[/{THEME['primary']}]")
                self.console.print(f"[{THEME['dim']}]This will clean up devices by removing unnecessary apps:[/{THEME['dim']}]")
                self.console.print()
                self.console.print(f"[{THEME['secondary']}]Apps to Remove:[/{THEME['secondary']}]")
                self.console.print(f"[{THEME['dim']}]  • All social media apps (except TikTok)[/{THEME['dim']}]")
                self.console.print(f"[{THEME['dim']}]  • All games and entertainment apps[/{THEME['dim']}]")
                self.console.print(f"[{THEME['dim']}]  • Shopping apps (Amazon, eBay, etc.)[/{THEME['dim']}]")
                self.console.print(f"[{THEME['dim']}]  • Carrier bloatware (Verizon, AT&T, etc.)[/{THEME['dim']}]")
                self.console.print(f"[{THEME['dim']}]  • News and media apps[/{THEME['dim']}]")
                self.console.print(f"[{THEME['dim']}]  • Pre-installed manufacturer apps[/{THEME['dim']}]")
                self.console.print()
                self.console.print(f"[{THEME['secondary']}]Apps to Keep:[/{THEME['secondary']}]")
                self.console.print(f"[{THEME['success']}]  ✓ TikTok (com.zhiliaoapp.musically)[/{THEME['success']}]")
                self.console.print(f"[{THEME['success']}]  ✓ All system apps (Android core)[/{THEME['success']}]")
                self.console.print()
                self.console.print(f"[{THEME['dim']}]Note: Removed apps can be restored via factory reset[/{THEME['dim']}]")
            elif action == "complete":
                self.console.print(f"[{THEME['primary']}]Complete Setup[/{THEME['primary']}]")
                self.console.print(f"[{THEME['dim']}]Performs full device preparation in one operation:[/{THEME['dim']}]")
                self.console.print()
                self.console.print(f"[{THEME['secondary']}]Step 1 - Security Configuration:[/{THEME['secondary']}]")
                self.console.print(f"[{THEME['dim']}]  • Enable developer options & USB debugging[/{THEME['dim']}]")
                self.console.print(f"[{THEME['dim']}]  • Configure display timeout and stay awake[/{THEME['dim']}]")
                self.console.print(f"[{THEME['dim']}]  • Disable security restrictions[/{THEME['dim']}]")
                self.console.print()
                self.console.print(f"[{THEME['secondary']}]Step 2 - Application Setup:[/{THEME['secondary']}]")
                self.console.print(f"[{THEME['dim']}]  • Install TikTok if not present[/{THEME['dim']}]")
                self.console.print(f"[{THEME['dim']}]  • Configure app permissions[/{THEME['dim']}]")
                self.console.print()
                self.console.print(f"[{THEME['secondary']}]Step 3 - Clean Device:[/{THEME['secondary']}]")
                self.console.print(f"[{THEME['dim']}]  • Remove all unnecessary apps[/{THEME['dim']}]")
                self.console.print(f"[{THEME['dim']}]  • Clear cache and temporary files[/{THEME['dim']}]")
                self.console.print(f"[{THEME['dim']}]  • Optimize storage space[/{THEME['dim']}]")
                self.console.print()
                self.console.print(f"[{THEME['warning']}]⚠ This process takes 5-10 minutes per device[/{THEME['warning']}]")
            else:
                # Default for install apps or no specific action
                self.console.print(f"[{THEME['secondary']}]Select Target Devices[/{THEME['secondary']}]")
            
            self.console.print()
            
            # Create a table for device selection
            device_table = Table(
                show_header=False,
                border_style=THEME['dim'],
                box=None,
                pad_edge=False,
                show_edge=False
            )
            
            device_table.add_column("", width=3)  # Arrow
            device_table.add_column("", width=3)  # Selection
            device_table.add_column("Device", style=THEME['text'])
            device_table.add_column("Model", style=THEME['dim'])
            
            # Display devices with selection status
            for idx, device in enumerate(devices):
                is_selected = device in selected
                is_current = idx == current_index
                
                # Selection indicator
                if is_selected:
                    indicator = f"[{THEME['success']}]●[/{THEME['success']}]"
                else:
                    indicator = f"[{THEME['dim']}]○[/{THEME['dim']}]"
                
                # Current position indicator
                arrow = "→" if is_current else " "
                arrow_style = THEME['primary'] if is_current else THEME['text']
                
                # Device status
                status_color = THEME['success'] if device.status == "connected" else THEME['warning']
                
                device_table.add_row(
                    f"[{arrow_style}]{arrow}[/{arrow_style}]",
                    indicator,
                    f"[{status_color}]{device.serial}[/{status_color}]",
                    device.model
                )
            
            self.console.print(device_table)
            self.console.print()
            
            # Footer
            if selected:
                self.console.print(f"[{THEME['success']}]Selected: {len(selected)} device(s)[/{THEME['success']}]")
            else:
                self.console.print(f"[{THEME['dim']}]No devices selected[/{THEME['dim']}]")
            
            self.console.print()
            # Show "Deselect All" when all are selected
            if len(selected) == len(devices):
                self.console.print(f"[{THEME['dim']}]space: toggle  a: deselect all  enter: continue  b: back  q: quit[/{THEME['dim']}]")
            else:
                self.console.print(f"[{THEME['dim']}]space: toggle  a: select all  enter: continue  b: back  q: quit[/{THEME['dim']}]")
            
            # Get key input
            key = self.menu.get_key()
            
            if key == '\x1b[A':  # Up arrow
                current_index = (current_index - 1) % len(devices)
            elif key == '\x1b[B':  # Down arrow
                current_index = (current_index + 1) % len(devices)
            elif key == ' ':  # Spacebar
                current_device = devices[current_index]
                if current_device in selected:
                    selected.remove(current_device)
                else:
                    selected.add(current_device)
            elif key.lower() == 'a':  # Select all
                if len(selected) == len(devices):
                    selected.clear()  # Deselect all if all selected
                else:
                    selected = set(devices)  # Select all devices
            elif key in ['\r', '\n']:  # Enter
                return list(selected)
            elif key in ['b', 'B']:  # Back
                return []
            elif key == '\x03':  # Ctrl+C - exit program
                import sys
                sys.exit(0)
    
    
    async def select_apps_to_install(self) -> List[tuple[str, List[str]]]:
        """Select apps from local APK folders with spacebar"""
        # Scan for available apps
        apps = self.local_apk_installer.scan_apk_folders()
        
        if not apps:
            self.console.print(f"\n[{THEME['error']}]No APK folders found in 'apks' directory[/{THEME['error']}]")
            self.console.print(f"[{THEME['dim']}]Place APK folders in the 'apks' directory[/{THEME['dim']}]")
            self.console.print(f"\n[{THEME['dim']}]Press any key to continue...[/{THEME['dim']}]")
            self.menu.get_key()
            return []
        
        selected = set()
        current_index = 0
        app_list = list(apps.items())
        
        while True:
            self.menu.clear_screen()
            self.menu.display_header()
            self.console.print()
            
            # Header
            self.console.print(f"[{THEME['secondary']}]Select Apps to Install[/{THEME['secondary']}]")
            self.console.print()
            
            # Create a table for app selection
            app_table = Table(
                show_header=False,
                border_style=THEME['dim'],
                box=None,
                pad_edge=False,
                show_edge=False
            )
            
            app_table.add_column("", width=3)  # Arrow
            app_table.add_column("", width=3)  # Selection
            app_table.add_column("App Name", style=THEME['text'])
            app_table.add_column("APK Info", style=THEME['dim'])
            
            # Display apps with selection status
            for idx, (app_name, apk_files) in enumerate(app_list):
                is_selected = app_name in selected
                is_current = idx == current_index
                
                # Selection indicator
                if is_selected:
                    indicator = f"[{THEME['success']}]●[/{THEME['success']}]"
                else:
                    indicator = f"[{THEME['dim']}]○[/{THEME['dim']}]"
                
                # Current position indicator
                arrow = "→" if is_current else " "
                arrow_style = THEME['primary'] if is_current else THEME['text']
                
                # APK info
                apk_count = len(apk_files)
                apk_info = f"{apk_count} file{'s' if apk_count > 1 else ''}"
                if apk_count > 1:
                    apk_info += " (split APK)"
                
                app_table.add_row(
                    f"[{arrow_style}]{arrow}[/{arrow_style}]",
                    indicator,
                    app_name,
                    apk_info
                )
            
            self.console.print(app_table)
            self.console.print()
            
            # Footer
            if selected:
                self.console.print(f"[{THEME['success']}]Selected: {len(selected)} app(s)[/{THEME['success']}]")
            else:
                self.console.print(f"[{THEME['dim']}]No apps selected[/{THEME['dim']}]")
            
            self.console.print()
            self.console.print(f"[{THEME['dim']}]space: toggle  a: select all  enter: continue  b: back[/{THEME['dim']}]")
            
            # Get key input
            key = self.menu.get_key()
            
            if key == '\x1b[A':  # Up arrow
                current_index = (current_index - 1) % len(app_list)
            elif key == '\x1b[B':  # Down arrow
                current_index = (current_index + 1) % len(app_list)
            elif key == ' ':  # Spacebar
                current_app = app_list[current_index][0]
                if current_app in selected:
                    selected.remove(current_app)
                else:
                    selected.add(current_app)
            elif key.lower() == 'a':  # Select all
                if len(selected) == len(app_list):
                    selected.clear()  # Deselect all if all selected
                else:
                    selected = set(app[0] for app in app_list)
            elif key in ['\r', '\n']:  # Enter
                if selected:
                    return [(app_name, apps[app_name]) for app_name in selected]
                else:
                    self.console.print(f"\n[{THEME['warning']}]No apps selected[/{THEME['warning']}]")
                    await asyncio.sleep(1)
            elif key in ['b', 'B']:  # Back
                return []
            elif key == '\x03':  # Ctrl+C - exit program
                import sys
                sys.exit(0)
    
    async def install_apps(self):
        """Install apps on devices"""
        devices = self.device_manager.get_connected_devices()
        if not devices:
            self.console.print(f"\n[{THEME['error']}]No connected devices. Please connect devices first.[/{THEME['error']}]")
            self.console.print(f"\n[{THEME['dim']}]Press any key to continue...[/{THEME['dim']}]")
            self.menu.get_key()
            return
        
        # Select apps from APK folder
        selected_apps = await self.select_apps_to_install()
        
        if not selected_apps:
            return
        
        # Select devices
        selected_devices = await self.select_devices_for_install(devices)
        
        if not selected_devices:
            self.console.print(f"\n[{THEME['warning']}]No devices selected[/{THEME['warning']}]")
            self.console.print(f"\n[{THEME['dim']}]Press any key to continue...[/{THEME['dim']}]")
            self.menu.get_key()
            return
        
        # Install each selected app on selected devices
        for app_name, apk_files in selected_apps:
            await self.install_local_apks(app_name, apk_files, selected_devices)
    
    async def install_local_apks(self, app_name: str, apk_files: List[str], selected_devices: List[Device]):
        """Install local APKs on selected devices"""
        # Install on selected devices
        self.menu.clear_screen()
        self.menu.display_header()
        self.console.print()
        
        # Simple status message
        self.console.print(f"[{THEME['primary']}]Installing: {app_name}[/{THEME['primary']}]")
        self.console.print(f"[{THEME['dim']}]APK files: {len(apk_files)} • Devices: {len(selected_devices)}[/{THEME['dim']}]")
        self.console.print()
        
        # Track results
        results = []
        installation_details = []
        
        # For large numbers of devices, use a compact display
        use_compact = len(selected_devices) > 10
        
        if use_compact:
            # Compact progress display for many devices
            with Progress(
                SpinnerColumn(style=THEME['primary']),
                TextColumn("{task.description}", style=THEME['text']),
                BarColumn(
                    style=THEME['dim'],
                    complete_style=THEME['success'],
                    finished_style=THEME['success'],
                    pulse_style=THEME['accent']
                ),
                TextColumn("{task.completed}/{task.total}", style=THEME['text']),
                TextColumn("{task.fields[status]}", style=THEME['dim']),
                console=self.console,
                refresh_per_second=4,
                transient=False
            ) as progress:
                
                # Single overall progress bar
                overall_task = progress.add_task(
                    "Overall Progress",
                    total=len(selected_devices),
                    status="Starting..."
                )
                
                # Track individual device statuses
                device_statuses = {}
                completed_count = 0
                
                async def install_on_device_compact(device):
                    """Install APK on a single device with compact progress"""
                    
                    async def update_status(status_text: str):
                        device_statuses[device.serial] = status_text
                        # Update overall status with current states
                        active_devices = [d for d, s in device_statuses.items() if s and "complete" not in s.lower() and "installed" not in s.lower()]
                        if active_devices:
                            status_summary = f"Active: {len(active_devices)} | Last: {status_text[:20]}"
                        else:
                            status_summary = status_text[:30]
                        progress.update(overall_task, status=status_summary)
                    
                    # Start installation
                    result = await self.local_apk_installer.install_apk_on_device(
                        device, app_name, apk_files, update_status
                    )
                    
                    # Update completed count
                    nonlocal completed_count
                    completed_count += 1
                    progress.update(overall_task, completed=completed_count)
                    
                    # Final status
                    if result['already_installed']:
                        final_status = "Already installed"
                    elif result['success']:
                        final_status = "Success"
                    else:
                        final_status = f"Failed: {result['message'][:20]}"
                    
                    device_statuses[device.serial] = final_status
                    progress.update(overall_task, status=f"Completed: {completed_count}/{len(selected_devices)}")
                    
                    return device, result
                
                # Run installations in parallel
                installation_tasks = [install_on_device_compact(device) for device in selected_devices]
                try:
                    installation_results = await asyncio.gather(*installation_tasks, return_exceptions=True)
                except asyncio.CancelledError:
                    # Cancel all tasks if interrupted
                    for task in installation_tasks:
                        if hasattr(task, 'cancel'):
                            task.cancel()
                    raise
                
                # Process results
                for device, result in installation_results:
                    results.append(result)
                    
                    # Store details for table
                    if result['already_installed']:
                        status_icon = "›"
                        status_color = THEME['warning']
                        status_text = "Already Installed"
                    elif result['success']:
                        status_icon = "▸"
                        status_color = THEME['success']
                        status_text = "Installed"
                    else:
                        status_icon = "‹"
                        status_color = THEME['error']
                        status_text = f"Failed: {result['message'][:30]}"
                    
                    installation_details.append({
                        'device': device.serial,
                        'model': device.model,
                        'status_icon': status_icon,
                        'status_color': status_color,
                        'status_text': status_text
                    })
        else:
            # Original detailed progress bars for fewer devices
            with Progress(
                SpinnerColumn(style=THEME['primary']),
                TextColumn("{task.description}", style=THEME['text']),
                BarColumn(
                    style=THEME['dim'],
                    complete_style=THEME['success'],
                    finished_style=THEME['success'],
                    pulse_style=THEME['accent']
                ),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%", style=THEME['text']),
                TextColumn("│", style=THEME['dim']),
                TextColumn("{task.fields[status]}", style=THEME['dim']),
                console=self.console,
                refresh_per_second=10,
                expand=False,
                disable=False
            ) as progress:
                # Create a task for each device
                device_tasks = []
                for device in selected_devices:
                    task_id = progress.add_task(
                        f"{device.serial}",
                        total=100,
                        status="Waiting...",
                        visible=True
                    )
                    device_tasks.append((device, task_id))
                
                # Install on all devices in parallel
                async def install_on_device(device, task_id):
                    """Install APK on a single device with progress tracking"""
                    
                    last_progress = 0
                    
                    async def update_status(status_text: str):
                        nonlocal last_progress
                        # Update progress based on status
                        progress_mapping = {
                            "Checking package info...": 20,
                            "Checking if installed...": 40,
                            "Preparing installation...": 60,
                            "Installing APK...": 80,
                            "Installation complete!": 100,
                            "Already installed": 100,
                            "Installation failed": 100,
                            "Installation timeout": 100
                        }
                        
                        current_progress = 0
                        for key, value in progress_mapping.items():
                            if key in status_text:
                                current_progress = value
                                break
                        
                        # Only update if progress changed
                        if current_progress != last_progress or status_text != progress.tasks[task_id].fields.get('status', ''):
                            progress.update(task_id, completed=current_progress, status=status_text[:30])
                            last_progress = current_progress
                    
                    # Start installation
                    result = await self.local_apk_installer.install_apk_on_device(
                        device, app_name, apk_files, update_status
                    )
                    
                    # Final status update
                    if result['already_installed']:
                        progress.update(task_id, completed=100, status="✓ Already installed")
                    elif result['success']:
                        progress.update(task_id, completed=100, status="✓ Installed successfully")
                    else:
                        progress.update(task_id, completed=100, status=f"✗ {result['message'][:25]}")
                    
                    return device, result
                
                # Run installations in parallel
                installation_tasks = [
                    install_on_device(device, task_id)
                    for device, task_id in device_tasks
                ]
                
                # Wait for all installations to complete
                try:
                    installation_results = await asyncio.gather(*installation_tasks, return_exceptions=True)
                except asyncio.CancelledError:
                    # Cancel all tasks if interrupted
                    for task in installation_tasks:
                        if hasattr(task, 'cancel'):
                            task.cancel()
                    raise
                
                # Brief pause to show completed progress
                await asyncio.sleep(1)
                
                # Process results
                for device, result in installation_results:
                    results.append(result)
                    
                    # Store details for table
                    if result['already_installed']:
                        status_icon = "›"
                        status_color = THEME['warning']
                        status_text = "Already Installed"
                    elif result['success']:
                        status_icon = "▸"
                        status_color = THEME['success']
                        status_text = "Installed"
                    else:
                        status_icon = "‹"
                        status_color = THEME['error']
                        status_text = f"Failed: {result['message'][:30]}"
                    
                    installation_details.append({
                        'device': device.serial,
                        'model': device.model,
                        'status_icon': status_icon,
                        'status_color': status_color,
                        'status_text': status_text
                    })
        
        # Show results
        self.show_installation_results(installation_details, results)
    
    def show_installation_results(self, installation_details: List[Dict], results: List[Dict]):
        """Display installation results table and summary"""
        # Show results in a clean table
        self.console.print()
        
        # For many devices, show a compact summary instead of full table
        if len(installation_details) > 20:
            # Compact summary for 20+ devices
            successful = sum(1 for r in results if r['success'])
            already_installed = sum(1 for r in results if r['already_installed'])
            failed = len(results) - successful - already_installed
            
            # Create summary panel
            summary_grid = Table.grid(padding=1)
            summary_grid.add_column(justify="right", style=THEME['dim'])
            summary_grid.add_column(justify="left")
            
            if successful > 0:
                summary_grid.add_row(
                    "Installed:",
                    f"[{THEME['success']}]{successful} device(s)[/{THEME['success']}]"
                )
            if already_installed > 0:
                summary_grid.add_row(
                    "Already installed:",
                    f"[{THEME['warning']}]{already_installed} device(s)[/{THEME['warning']}]"
                )
            if failed > 0:
                summary_grid.add_row(
                    "Failed:",
                    f"[{THEME['error']}]{failed} device(s)[/{THEME['error']}]"
                )
            
            panel = Panel(
                summary_grid,
                title="Installation Summary",
                border_style=THEME['primary'],
                box=box.ROUNDED
            )
            self.console.print(panel)
            
            # Show only failed devices if any
            if failed > 0:
                self.console.print(f"\n[{THEME['error']}]Failed devices:[/{THEME['error']}]")
                for detail in installation_details:
                    if detail['status_icon'] == "○":  # Failed icon
                        self.console.print(f"  • {detail['device']} ({detail['model']}): {detail['status_text']}")
        else:
            # Full table for fewer devices
            results_table = Table(
                show_header=True,
                header_style=THEME['dim'],
                border_style=THEME['dim'],
                box=box.SIMPLE,
                pad_edge=False,
                show_lines=False
            )
            
            results_table.add_column("Device", style=THEME['text'], no_wrap=True)
            results_table.add_column("Model", style=THEME['dim'])
            results_table.add_column("Status", justify="left")
            
            for detail in installation_details:
                status_display = Text()
                status_display.append(f"{detail['status_icon']} ", style=detail['status_color'])
                status_display.append(detail['status_text'], style=detail['status_color'])
                
                results_table.add_row(
                    detail['device'],
                    detail['model'],
                    status_display
                )
            
            self.console.print(results_table)
        
        # Summary
        successful = sum(1 for r in results if r['success'])
        already_installed = sum(1 for r in results if r['already_installed'])
        failed = len(results) - successful - already_installed
        
        # Summary line
        self.console.print()
        summary_parts = []
        if successful > 0:
            summary_parts.append(f"[{THEME['success']}]{successful} installed[/{THEME['success']}]")
        if already_installed > 0:
            summary_parts.append(f"[{THEME['warning']}]{already_installed} already installed[/{THEME['warning']}]")
        if failed > 0:
            summary_parts.append(f"[{THEME['error']}]{failed} failed[/{THEME['error']}]")
        
        if summary_parts:
            summary_text = f"[{THEME['dim']}]Summary:[/{THEME['dim']}] " + " • ".join(summary_parts)
            self.console.print(summary_text)
        
        self.console.print(f"\n[{THEME['dim']}]Press any key to continue...[/{THEME['dim']}]")
        self.menu.get_key()
    
    
    async def configure_device_settings(self):
        """Configure device settings (security, privacy, etc.)"""
        devices = self.device_manager.get_connected_devices()
        if not devices:
            self.console.print(f"\n[{THEME['error']}]No connected devices. Please connect devices first.[/{THEME['error']}]")
            self.console.print(f"\n[{THEME['dim']}]Press any key to continue...[/{THEME['dim']}]")
            self.menu.get_key()
            return
        
        # Select devices using the same UI as install apps
        selected_devices = await self.select_devices_for_install(devices, action="configure")
        
        if not selected_devices:
            self.console.print(f"\n[{THEME['warning']}]No devices selected[/{THEME['warning']}]")
            self.console.print(f"\n[{THEME['dim']}]Press any key to continue...[/{THEME['dim']}]")
            self.menu.get_key()
            return
        
        # Clear screen and show header
        self.menu.clear_screen()
        self.menu.display_header()
        self.console.print()
        
        # Simple status message
        self.console.print(f"[{THEME['primary']}]Configuring {len(selected_devices)} device(s)...[/{THEME['primary']}]")
        self.console.print()
        
        # Configure with progress
        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=self.console
            ) as progress:
            task = progress.add_task(f"Configuring devices...", total=len(selected_devices))
            
            all_results = []
            for device in selected_devices:
                progress.update(task, description=f"Configuring {device.serial}...")
                
                results = await self.configurator.configure_device_security(device)
                all_results.append((device, results))
                
                progress.advance(task)
        
        # Show results
        self.console.print()
        self.console.print(f"[{THEME['success']}]✓ Device configuration complete![/{THEME['success']}]")
        self.console.print()
        
        for device, results in all_results:
            self.console.print(f"[{THEME['secondary']}]{device.serial}[/{THEME['secondary']}]")
            success_count = sum(1 for v in results.values() if v)
            fail_count = sum(1 for v in results.values() if not v)
            
            if fail_count == 0:
                self.console.print(f"  All {success_count} settings configured")
            else:
                self.console.print(f"  Configured: {success_count} settings")
                if fail_count > 0:
                    self.console.print(f"  [{THEME['error']}]Failed: {fail_count} settings[/{THEME['error']}]")
        
        self.console.print(f"\n[{THEME['dim']}]Press any key to continue...[/{THEME['dim']}]")
        self.menu.get_key()
    
    async def view_status(self):
        """View device status - includes scanning if needed"""
        self.menu.clear_screen()
        self.menu.display_header()
        
        # If no devices, do a scan
        if not self.device_manager.devices:
            self.console.print(f"[{THEME['dim']}]Scanning for devices...[/{THEME['dim']}]")
            await self.device_manager.scan_devices()
        
        # Get current device list (preserves connection status)
        # Filter to only show plugged-in devices (not disconnected)
        devices = [d for d in self.device_manager.devices.values() if d.status != "disconnected"]
        
        if not devices:
            # Show same UI structure but with no devices message
            self.console.print()
            self.console.print(f"[{THEME['dim']}]Status: [/{THEME['dim']}][{THEME['warning']}]No devices connected[/{THEME['warning']}]")
            self.console.print()
            
            # Empty table
            table = Table(
                show_header=True,
                header_style=THEME['secondary'],
                border_style=THEME['dim'],
                box=box.SIMPLE_HEAD,
                pad_edge=False
            )
            
            table.add_column("#", style=THEME['dim'], width=3)
            table.add_column("Serial", style=THEME['text'])
            table.add_column("Model", style=THEME['text'])
            table.add_column("Status", justify="center")
            
            self.console.print(table)
            
            # Options
            self.console.print(f"\n[{THEME['dim']}]Options:[/{THEME['dim']}]")
            self.console.print(f"  • Connect devices via USB and authorize them")
            self.console.print(f"  • Press [{THEME['success']}]r[/{THEME['success']}] to refresh/rescan devices")
            self.console.print(f"  • Press [{THEME['success']}]b[/{THEME['success']}] to go back to menu")
            
            key = self.menu.get_key()
            
            if key.lower() == 'r':
                await self.refresh_connections()
                await self.view_status()  # Refresh view
            elif key.lower() == 'b':
                return  # Go back to menu
        else:
            # Count device statuses
            connected = len([d for d in devices if d.status == "connected"])
            authorized = len([d for d in devices if d.status == "device"])
            unauthorized = len([d for d in devices if d.status == "unauthorized"])
            disconnected = len([d for d in devices if d.status == "disconnected"])
            total = len(devices)
            
            # Status summary
            self.console.print()
            status_line = f"[{THEME['dim']}]Status: [/{THEME['dim']}]"
            
            if connected > 0:
                status_line += f"[{THEME['success']}]{connected} connected[/{THEME['success']}]  "
            if authorized > 0:
                status_line += f"[{THEME['warning']}]{authorized} authorized[/{THEME['warning']}]  "
            if unauthorized > 0:
                status_line += f"[{THEME['error']}]{unauthorized} unauthorized[/{THEME['error']}]  "
            
            self.console.print(status_line)
            self.console.print()
            
            # Get network info and proxy status for connected devices
            for device in devices:
                if device.status == "connected":
                    await self.device_manager.get_device_network_info(device)
                    # Check proxy status
                    device.proxy_status = await self.device_manager.check_proxy_status(device)
            
            # Detailed device table
            self.menu.display_device_table(devices)
            
            # Options
            self.console.print(f"\n[{THEME['dim']}]Options:[/{THEME['dim']}]")
            if authorized > 0:
                self.console.print(f"  • Press [{THEME['success']}]c[/{THEME['success']}] to connect to {authorized} authorized device(s)")
            if unauthorized > 0:
                self.console.print(f"  • Authorize {unauthorized} device(s) on their screens")
            self.console.print(f"  • Press [{THEME['success']}]r[/{THEME['success']}] to refresh/rescan devices")
            self.console.print(f"  • Press [{THEME['success']}]b[/{THEME['success']}] to go back to menu")
            
            key = self.menu.get_key()
            
            if key.lower() == 'c' and authorized > 0:
                self.console.print(f"\n[{THEME['dim']}]Connecting to authorized devices...[/{THEME['dim']}]")
                await self.device_manager.connect_all_devices()
                await self.view_status()  # Refresh view
            elif key.lower() == 'r':
                await self.refresh_connections()
                await self.view_status()  # Refresh view
            elif key.lower() == 'b':
                return  # Go back to menu
    
    async def run_complete_setup(self):
        """Run complete setup"""
        devices = self.device_manager.get_connected_devices()
        if not devices:
            self.console.print(f"\n[{THEME['error']}]No connected devices. Please connect devices first.[/{THEME['error']}]")
            self.console.print(f"\n[{THEME['dim']}]Press any key to continue...[/{THEME['dim']}]")
            self.menu.get_key()
            return
        
        # Select devices using consistent UI
        selected_devices = await self.select_devices_for_install(devices, action="complete")
        
        if not selected_devices:
            self.console.print(f"\n[{THEME['warning']}]No devices selected[/{THEME['warning']}]")
            self.console.print(f"\n[{THEME['dim']}]Press any key to continue...[/{THEME['dim']}]")
            self.menu.get_key()
            return
        
        # Clear screen and show header
        self.menu.clear_screen()
        self.menu.display_header()
        self.console.print()
        
        # Simple confirmation
        self.console.print(f"[{THEME['warning']}]Proceed with complete setup for {len(selected_devices)} device(s)? (y/n)[/{THEME['warning']}]")
        
        confirm = self.menu.get_key()
        if confirm not in ['y', 'Y']:
            return
        
        # Clear and start setup
        self.menu.clear_screen()
        self.menu.display_header()
        self.console.print()
        self.console.print(f"[{THEME['secondary']}]Starting complete setup...[/{THEME['secondary']}]\n")
        
        # Step 1: Security
        self.console.rule(f"[{THEME['primary']}]Security Configuration[/{THEME['primary']}]")
        await self.show_progress_enhanced("Configuring security", selected_devices, self.configurator.configure_device_security)
        
        # Step 2: Apps
        self.console.rule(f"[{THEME['primary']}]Application Installation[/{THEME['primary']}]")
        # Application installation step removed - add your own app installation logic here if needed
        
        self.console.print(f"\n[{THEME['success']}]✓ Complete setup finished![/{THEME['success']}]")
        self.console.print(f"\n[{THEME['dim']}]Press any key to continue...[/{THEME['dim']}]")
        self.menu.get_key()
    
    async def remove_bloatware(self):
        """Remove all non-system apps from devices using allowlist approach"""
        devices = self.device_manager.get_connected_devices()
        if not devices:
            self.console.print(f"\n[{THEME['error']}]No connected devices. Please connect devices first.[/{THEME['error']}]")
            self.console.print(f"\n[{THEME['dim']}]Press any key to continue...[/{THEME['dim']}]")
            self.menu.get_key()
            return
        
        # Select devices using the same UI as install apps
        selected_devices = await self.select_devices_for_install(devices, action="bloatware")
        
        if not selected_devices:
            self.console.print(f"\n[{THEME['warning']}]No devices selected[/{THEME['warning']}]")
            self.console.print(f"\n[{THEME['dim']}]Press any key to continue...[/{THEME['dim']}]")
            self.menu.get_key()
            return
        
        # Clear screen and show header
        self.menu.clear_screen()
        self.menu.display_header()
        self.console.print()
        
        # Confirmation prompt
        self.console.print(f"[{THEME['primary']}]Safe Bloatware Removal[/{THEME['primary']}]")
        self.console.print(f"[{THEME['dim']}]This will remove known bloatware:[/{THEME['dim']}]")
        self.console.print(f"[{THEME['dim']}]  • Games and entertainment apps[/{THEME['dim']}]")
        self.console.print(f"[{THEME['dim']}]  • Social media (Facebook, Instagram, etc.)[/{THEME['dim']}]")
        self.console.print(f"[{THEME['dim']}]  • Shopping apps (Amazon, eBay, etc.)[/{THEME['dim']}]")
        self.console.print(f"[{THEME['dim']}]  • Pre-installed manufacturer bloatware[/{THEME['dim']}]")
        self.console.print()
        self.console.print(f"[{THEME['success']}]Keeping: TikTok and all system apps[/{THEME['success']}]")
        self.console.print()
        self.console.print(f"[{THEME['warning']}]Remove bloatware from {len(selected_devices)} device(s)? (y/n)[/{THEME['warning']}]")
        
        confirm = self.menu.get_key()
        if confirm not in ['y', 'Y']:
            return
        
        # Clear screen again after confirmation
        self.menu.clear_screen()
        self.menu.display_header()
        self.console.print()
        
        # Status message
        self.console.print(f"[{THEME['primary']}]🧹 Removing bloatware from {len(selected_devices)} device(s)...[/{THEME['primary']}]")
        self.console.print(f"[{THEME['dim']}]Using safe blocklist method - only removing known bloatware[/{THEME['dim']}]")
        self.console.print()
        
        # Remove using allowlist approach with progress
        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=self.console
            ) as progress:
            task = progress.add_task(f"Cleaning devices...", total=len(selected_devices))
            
            all_results = []
            for device in selected_devices:
                progress.update(task, description=f"Cleaning {device.serial}...")
                
                # Use SAFE removal by default - not aggressive allowlist
                # To prevent bricking, we're using the old safe method
                results = await self.bloatware_remover.remove_bloatware_from_list(device)
                all_results.append((device, results))
                
                progress.advance(task)
        
        # Show results
        self.console.print()
        self.console.print(f"[{THEME['success']}]✓ Bloatware removal complete![/{THEME['success']}]")
        self.console.print()
        
        total_removed = 0
        total_kept = 0
        total_failed = 0
        
        for device, results in all_results:
            self.console.print(f"[{THEME['secondary']}]{device.serial}[/{THEME['secondary']}]")
            
            # Calculate percentages
            total_before = len(results['removed']) + len(results['skipped']) + len(results.get('failed', []))
            percent_removed = (len(results['removed']) / total_before * 100) if total_before > 0 else 0
            
            self.console.print(f"  📦 Removed: {len(results['removed'])} apps ({percent_removed:.0f}% reduction)")
            self.console.print(f"  ✅ Kept: {len(results['skipped'])} essential apps")
            
            if results.get('failed'):
                self.console.print(f"  [{THEME['error']}]⚠️  Failed: {len(results['failed'])} apps (system-protected)[/{THEME['error']}]")
                total_failed += len(results['failed'])
            
            total_removed += len(results['removed'])
            total_kept += len(results.get('skipped', []))
        
        if len(all_results) > 1:
            self.console.print()
            self.console.print(f"[{THEME['dim']}]Total across all devices:[/{THEME['dim']}]")
            self.console.print(f"[{THEME['dim']}]  • Removed: {total_removed} apps[/{THEME['dim']}]")
            self.console.print(f"[{THEME['dim']}]  • Kept: {total_kept} essential apps[/{THEME['dim']}]")
            if total_failed > 0:
                self.console.print(f"[{THEME['dim']}]  • Failed: {total_failed} apps[/{THEME['dim']}]")
        
        self.console.print(f"\n[{THEME['dim']}]Press any key to continue...[/{THEME['dim']}]")
        self.menu.get_key()
    
    async def install_doublespeed_app(self):
        """Install DoubleSpeed Helper app on all connected devices"""
        devices = self.device_manager.get_connected_devices()
        if not devices:
            self.console.print(f"\n[{THEME['error']}]No connected devices. Please connect devices first.[/{THEME['error']}]")
            self.console.print(f"\n[{THEME['dim']}]Press any key to continue...[/{THEME['dim']}]")
            self.menu.get_key()
            return
        
        # Check if APK exists
        apk_path = "ds-android-app/apks/doublespeed-helper.apk"
        import os
        if not os.path.exists(apk_path):
            self.console.print(f"\n[{THEME['error']}]APK not found at: {apk_path}[/{THEME['error']}]")
            self.console.print(f"[{THEME['dim']}]Make sure the DoubleSpeed APK is in the correct location[/{THEME['dim']}]")
            self.console.print(f"\n[{THEME['dim']}]Press any key to continue...[/{THEME['dim']}]")
            self.menu.get_key()
            return
        
        self.menu.clear_screen()
        self.menu.display_header()
        self.console.print()
        
        self.console.print(f"[{THEME['primary']}]Installing DoubleSpeed Helper App[/{THEME['primary']}]")
        self.console.print(f"[{THEME['dim']}]APK: {apk_path}[/{THEME['dim']}]")
        self.console.print(f"[{THEME['dim']}]Devices: {len(devices)}[/{THEME['dim']}]")
        self.console.print()
        
        # Use batch installer if available
        if hasattr(self, 'batch_adb'):
            device_serials = [d.serial for d in devices]
            
            # First check which devices already have the app
            self.console.print(f"[{THEME['dim']}]Checking existing installations...[/{THEME['dim']}]")
            check_results = await self.batch_adb.run_command_batch(
                device_serials,
                ["shell", "pm", "list", "packages"],
                timeout=5.0
            )
            
            already_installed = []
            to_install = []
            
            for serial, result in check_results.items():
                stdout = result.get('stdout', '')
                if result.get('success') and "package:com.android.systemui.helper" in stdout:
                    already_installed.append(serial)
                    self.console.print(f"  [{THEME['dim']}]○[/{THEME['dim']}] {serial}: Already installed")
                else:
                    to_install.append(serial)
            
            if not to_install:
                self.console.print(f"\n[{THEME['success']}]DoubleSpeed app is already installed on all devices[/{THEME['success']}]")
            else:
                # Install on devices that need it
                self.console.print(f"\n[{THEME['dim']}]Installing on {len(to_install)} device(s)...[/{THEME['dim']}]")
                
                install_results = await self.batch_adb.install_apk_batch(
                    to_install,
                    apk_path,
                    grant_permissions=True
                )
                
                success_count = 0
                failed_count = 0
                
                for serial, result in install_results.items():
                    if result['success']:
                        self.console.print(f"  [{THEME['success']}]✓[/{THEME['success']}] {serial}: Installed successfully")
                        success_count += 1
                    else:
                        error = result.get('stderr', '') or result.get('stdout', 'Unknown error')
                        self.console.print(f"  [{THEME['error']}]✗[/{THEME['error']}] {serial}: {error[:50]}")
                        failed_count += 1
                
                self.console.print()
                self.console.print(f"[{THEME['secondary']}]Installation Complete[/{THEME['secondary']}]")
                self.console.print(f"[{THEME['success']}]Success: {success_count}[/{THEME['success']}] | [{THEME['error']}]Failed: {failed_count}[/{THEME['error']}] | [{THEME['dim']}]Already installed: {len(already_installed)}[/{THEME['dim']}]")
                
                # Launch the app on newly installed devices to grant initial permissions
                if success_count > 0:
                    self.console.print(f"\n[{THEME['dim']}]Launching app to grant permissions...[/{THEME['dim']}]")
                    
                    launch_results = await self.batch_adb.launch_app_batch(
                        [s for s in to_install if install_results[s]['success']],
                        "com.android.systemui.helper",
                        ".MainActivity"
                    )
                    
                    for serial, result in launch_results.items():
                        if result['success']:
                            self.console.print(f"  [{THEME['success']}]✓[/{THEME['success']}] {serial}: App launched")
        else:
            # Fallback to sequential installation
            success_count = 0
            failed_count = 0
            already_installed = 0
            
            for device in devices:
                # Check if already installed
                cmd = ["adb", "-s", device.serial, "shell", "pm", "list", "packages", "com.android.systemui.helper"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                
                if "com.android.systemui.helper" in result.stdout:
                    self.console.print(f"  [{THEME['dim']}]○[/{THEME['dim']}] {device.serial}: Already installed")
                    already_installed += 1
                    continue
                
                # Install the APK
                cmd = ["adb", "-s", device.serial, "install", "-g", apk_path]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0 and "Success" in result.stdout:
                    self.console.print(f"  [{THEME['success']}]✓[/{THEME['success']}] {device.serial}: Installed successfully")
                    success_count += 1
                    
                    # Launch the app
                    cmd = ["adb", "-s", device.serial, "shell", "am", "start", "-n", "com.android.systemui.helper/.MainActivity"]
                    subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                else:
                    error = result.stderr or result.stdout
                    self.console.print(f"  [{THEME['error']}]✗[/{THEME['error']}] {device.serial}: {error[:50]}")
                    failed_count += 1
            
            self.console.print()
            self.console.print(f"[{THEME['secondary']}]Installation Complete[/{THEME['secondary']}]")
            self.console.print(f"[{THEME['success']}]Success: {success_count}[/{THEME['success']}] | [{THEME['error']}]Failed: {failed_count}[/{THEME['error']}] | [{THEME['dim']}]Already installed: {already_installed}[/{THEME['dim']}]")
        
        self.console.print()
        self.console.print(f"[{THEME['dim']}]Press any key to continue...[/{THEME['dim']}]")
        self.menu.get_key()
    
    async def start_proxy_all_devices(self):
        """Start proxy on all connected devices"""
        devices = self.device_manager.get_connected_devices()
        if not devices:
            self.console.print(f"\n[{THEME['error']}]No connected devices. Please connect devices first.[/{THEME['error']}]")
            self.console.print(f"\n[{THEME['dim']}]Press any key to continue...[/{THEME['dim']}]")
            self.menu.get_key()
            return
        
        self.menu.clear_screen()
        self.menu.display_header()
        self.console.print()
        
        self.console.print(f"[{THEME['primary']}]Starting Proxy on All Devices[/{THEME['primary']}]")
        self.console.print(f"[{THEME['dim']}]Devices: {len(devices)}[/{THEME['dim']}]")
        self.console.print()
        
        success_count = 0
        failed_count = 0
        
        # Use the same simple approach as stop proxy - it works!
        for device in devices:
            try:
                # Start proxy using broadcast command
                cmd = ["adb", "-s", device.serial, "shell", "am", "broadcast", 
                       "-n", "com.android.systemui.helper/.ProxyControlReceiver", 
                       "-a", "com.android.systemui.helper.START"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0 and "Broadcast completed" in result.stdout:
                    self.console.print(f"  [{THEME['success']}]✓[/{THEME['success']}] {device.serial}: Proxy started")
                    success_count += 1
                else:
                    self.console.print(f"  [{THEME['error']}]✗[/{THEME['error']}] {device.serial}: Failed to start")
                    failed_count += 1
                    
            except Exception as e:
                self.console.print(f"  [{THEME['error']}]✗[/{THEME['error']}] {device.serial}: {str(e)[:50]}")
                failed_count += 1
        
        self.console.print()
        self.console.print(f"[{THEME['secondary']}]Complete[/{THEME['secondary']}]")
        self.console.print(f"[{THEME['success']}]Success: {success_count}[/{THEME['success']}] | [{THEME['error']}]Failed: {failed_count}[/{THEME['error']}]")
        self.console.print()
        self.console.print(f"[{THEME['dim']}]Press any key to continue...[/{THEME['dim']}]")
        self.menu.get_key()
    
    async def stop_proxy_all_devices(self):
        """Stop proxy on all connected devices"""
        devices = self.device_manager.get_connected_devices()
        if not devices:
            self.console.print(f"\n[{THEME['error']}]No connected devices. Please connect devices first.[/{THEME['error']}]")
            self.console.print(f"\n[{THEME['dim']}]Press any key to continue...[/{THEME['dim']}]")
            self.menu.get_key()
            return
        
        self.menu.clear_screen()
        self.menu.display_header()
        self.console.print()
        
        self.console.print(f"[{THEME['primary']}]Stopping Proxy on All Devices[/{THEME['primary']}]")
        self.console.print(f"[{THEME['dim']}]Devices: {len(devices)}[/{THEME['dim']}]")
        self.console.print()
        
        success_count = 0
        failed_count = 0
        
        for device in devices:
            try:
                # Stop proxy using broadcast command
                cmd = ["adb", "-s", device.serial, "shell", "am", "broadcast", 
                       "-n", "com.android.systemui.helper/.ProxyControlReceiver", 
                       "-a", "com.android.systemui.helper.STOP"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0 and "Broadcast completed" in result.stdout:
                    self.console.print(f"  [{THEME['success']}]✓[/{THEME['success']}] {device.serial}: Proxy stopped")
                    success_count += 1
                else:
                    self.console.print(f"  [{THEME['error']}]✗[/{THEME['error']}] {device.serial}: Failed to stop")
                    failed_count += 1
                    
            except Exception as e:
                self.console.print(f"  [{THEME['error']}]✗[/{THEME['error']}] {device.serial}: {str(e)[:50]}")
                failed_count += 1
        
        self.console.print()
        self.console.print(f"[{THEME['secondary']}]Complete[/{THEME['secondary']}]")
        self.console.print(f"[{THEME['success']}]Success: {success_count}[/{THEME['success']}] | [{THEME['error']}]Failed: {failed_count}[/{THEME['error']}]")
        self.console.print()
        self.console.print(f"[{THEME['dim']}]Press any key to continue...[/{THEME['dim']}]")
        self.menu.get_key()
    
    async def configure_default_proxy(self):
        """Configure default proxy settings on all devices"""
        devices = self.device_manager.get_connected_devices()
        if not devices:
            self.console.print(f"\n[{THEME['error']}]No connected devices. Please connect devices first.[/{THEME['error']}]")
            self.console.print(f"\n[{THEME['dim']}]Press any key to continue...[/{THEME['dim']}]")
            self.menu.get_key()
            return
        
        # Default proxy configuration
        proxy_address = "192.53.65.133"
        proxy_port = 5134
        proxy_username = "ihiupcnd"
        proxy_password = "k9kfjqyq2bzw"
        
        self.menu.clear_screen()
        self.menu.display_header()
        self.console.print()
        
        self.console.print(f"[{THEME['primary']}]Configuring Default Proxy[/{THEME['primary']}]")
        self.console.print(f"[{THEME['dim']}]Address: {proxy_address}:{proxy_port}[/{THEME['dim']}]")
        self.console.print(f"[{THEME['dim']}]Username: {proxy_username}[/{THEME['dim']}]")
        self.console.print(f"[{THEME['dim']}]Devices: {len(devices)}[/{THEME['dim']}]")
        self.console.print()
        
        success_count = 0
        failed_count = 0
        
        for device in devices:
            try:
                # Configure proxy using broadcast command with all parameters
                cmd = ["adb", "-s", device.serial, "shell", "am", "broadcast", 
                       "-n", "com.android.systemui.helper/.ProxyControlReceiver", 
                       "-a", "com.android.systemui.helper.CONFIG",
                       "--es", "proxy_address", proxy_address,
                       "--ei", "proxy_port", str(proxy_port),
                       "--es", "proxy_username", proxy_username,
                       "--es", "proxy_password", proxy_password]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0 and "Broadcast completed" in result.stdout:
                    self.console.print(f"  [{THEME['success']}]✓[/{THEME['success']}] {device.serial}: Configured")
                    success_count += 1
                else:
                    self.console.print(f"  [{THEME['error']}]✗[/{THEME['error']}] {device.serial}: Failed to configure")
                    failed_count += 1
                    
            except Exception as e:
                self.console.print(f"  [{THEME['error']}]✗[/{THEME['error']}] {device.serial}: {str(e)[:50]}")
                failed_count += 1
        
        self.console.print()
        self.console.print(f"[{THEME['secondary']}]Configuration Complete[/{THEME['secondary']}]")
        self.console.print(f"[{THEME['success']}]Success: {success_count}[/{THEME['success']}] | [{THEME['error']}]Failed: {failed_count}[/{THEME['error']}]")
        self.console.print()
        self.console.print(f"[{THEME['dim']}]Note: You may need to start the proxy after configuration[/{THEME['dim']}]")
        self.console.print(f"[{THEME['dim']}]Press any key to continue...[/{THEME['dim']}]")
        self.menu.get_key()
    
    async def test_functions(self):
        """Test functions menu"""
        while True:
            self.menu.clear_screen()
            self.menu.display_header()
            self.console.print()
            
            self.console.print(f"[{THEME['secondary']}]Test Functions[/{THEME['secondary']}]")
            self.console.print()
            
            test_menu_items = [
                {
                    'icon': '[1]',
                    'label': 'Install DoubleSpeed App',
                    'action': 'install_doublespeed'
                },
                {
                    'icon': '[2]',
                    'label': 'Start Proxy (All Devices)',
                    'action': 'start_proxy'
                },
                {
                    'icon': '[3]',
                    'label': 'Stop Proxy (All Devices)',
                    'action': 'stop_proxy'
                },
                {
                    'icon': '[4]',
                    'label': 'Configure Default Proxy',
                    'action': 'config_proxy'
                },
                {
                    'icon': '[5]',
                    'label': 'Export Super Proxy Config',
                    'action': 'super_proxy_export'
                },
                {
                    'icon': '[B]',
                    'label': 'Back',
                    'action': 'back'
                }
            ]
            
            devices = list(self.device_manager.devices.values())
            connected = len([d for d in devices if d.status == "connected"])
            
            selection = self.menu.navigate_menu(test_menu_items, len(devices), connected, show_separators=False)
            
            if not selection or selection['action'] == 'back':
                break
            elif selection['action'] == 'install_doublespeed':
                await self.install_doublespeed_app()
            elif selection['action'] == 'start_proxy':
                await self.start_proxy_all_devices()
            elif selection['action'] == 'stop_proxy':
                await self.stop_proxy_all_devices()
            elif selection['action'] == 'config_proxy':
                await self.configure_default_proxy()
            elif selection['action'] == 'super_proxy_export':
                await self.export_super_proxy_config()
    
    async def export_super_proxy_config(self):
        """Export Super Proxy config to DoubleSpeed app"""
        devices = self.device_manager.get_connected_devices()
        if not devices:
            self.console.print(f"\n[{THEME['error']}]No connected devices. Please connect devices first.[/{THEME['error']}]")
            self.console.print(f"\n[{THEME['dim']}]Press any key to continue...[/{THEME['dim']}]")
            self.menu.get_key()
            return
        
        # Select devices
        selected_devices = await self.select_devices_for_install(devices, action="export Super Proxy config")
        
        if not selected_devices:
            self.console.print(f"\n[{THEME['warning']}]No devices selected[/{THEME['warning']}]")
            self.console.print(f"\n[{THEME['dim']}]Press any key to continue...[/{THEME['dim']}]")
            self.menu.get_key()
            return
        
        self.menu.clear_screen()
        self.menu.display_header()
        self.console.print()
        
        self.console.print(f"[{THEME['primary']}]Exporting Super Proxy Config to DoubleSpeed[/{THEME['primary']}]")
        self.console.print(f"[{THEME['dim']}]Devices: {len(selected_devices)}[/{THEME['dim']}]")
        self.console.print()
        
        success_count = 0
        failed_count = 0
        
        for device in selected_devices:
            try:
                self.console.print(f"[{THEME['text']}]Processing {device.serial}...[/{THEME['text']}]")
                
                # First, close any existing Super Proxy instance
                self.console.print(f"  [{THEME['dim']}]Closing any existing Super Proxy...[/{THEME['dim']}]")
                cmd = ["adb", "-s", device.serial, "shell", "am", "force-stop", "com.superproxy"]
                subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                
                await asyncio.sleep(1)
                
                # Launch Super Proxy app fresh
                self.console.print(f"  [{THEME['dim']}]Opening Super Proxy app...[/{THEME['dim']}]")
                # Try multiple launch methods
                cmd = ["adb", "-s", device.serial, "shell", "monkey", "-p", "com.superproxy", "-c", "android.intent.category.LAUNCHER", "1"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                
                if "No activities found" in result.stdout or result.returncode != 0:
                    # Try alternative launch
                    cmd = ["adb", "-s", device.serial, "shell", "am", "start", "-n", "com.superproxy/com.superproxy.MainActivity"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                    
                    if result.returncode != 0:
                        # Try with different activity name
                        cmd = ["adb", "-s", device.serial, "shell", "am", "start", "-n", "com.superproxy/.ui.MainActivity"]
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                
                # Wait for app to fully load
                await asyncio.sleep(3)
                
                # Check if we're on the proxy config screen (might see "Stop" button)
                self.console.print(f"  [{THEME['dim']}]Checking current screen state...[/{THEME['dim']}]")
                
                # Dump UI to check current state
                cmd = ["adb", "-s", device.serial, "shell", "uiautomator", "dump", "/sdcard/window_dump.xml"]
                subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                
                # Read the dump to check for Stop button
                cmd = ["adb", "-s", device.serial, "shell", "cat", "/sdcard/window_dump.xml"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                ui_content = result.stdout.lower() if result.returncode == 0 else ""
                
                # If we see "stop" or proxy is running, we need to stop it first
                if "stop" in ui_content and "proxy" in ui_content:
                    self.console.print(f"  [{THEME['dim']}]Proxy is running, stopping it first...[/{THEME['dim']}]")
                    # Click Stop button (usually in center of screen)
                    cmd = ["adb", "-s", device.serial, "shell", "input", "tap", "540", "960"]
                    subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                    await asyncio.sleep(2)
                    
                    # Click back arrow to return to main screen
                    self.console.print(f"  [{THEME['dim']}]Going back to main screen...[/{THEME['dim']}]")
                    cmd = ["adb", "-s", device.serial, "shell", "input", "keyevent", "KEYCODE_BACK"]
                    subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                    await asyncio.sleep(1)
                
                # Now we should be on the main screen - click the 3 dots menu
                self.console.print(f"  [{THEME['dim']}]Opening menu (3 dots in top right)...[/{THEME['dim']}]")
                # Try different positions for different screen sizes
                positions = [
                    (1000, 100),  # Top right for 1080p
                    (950, 100),   # Slightly left
                    (980, 150),   # Slightly lower
                ]
                
                for x, y in positions:
                    cmd = ["adb", "-s", device.serial, "shell", "input", "tap", str(x), str(y)]
                    subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                    await asyncio.sleep(0.5)
                    
                    # Check if menu opened by dumping UI again
                    cmd = ["adb", "-s", device.serial, "shell", "uiautomator", "dump", "/sdcard/window_dump.xml"]
                    subprocess.run(cmd, capture_output=True, text=True, timeout=2)
                    cmd = ["adb", "-s", device.serial, "shell", "cat", "/sdcard/window_dump.xml"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
                    
                    if "export" in result.stdout.lower():
                        break
                
                await asyncio.sleep(1)
                
                # Click on "Export Config" option
                self.console.print(f"  [{THEME['dim']}]Selecting 'Export Config'...[/{THEME['dim']}]")
                # Try to click on text "Export Config" using different Y positions
                export_positions = [
                    (850, 300),   # First menu item position
                    (850, 400),   # Second position
                    (850, 500),   # Third position
                ]
                
                for x, y in export_positions:
                    cmd = ["adb", "-s", device.serial, "shell", "input", "tap", str(x), str(y)]
                    subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                    await asyncio.sleep(0.5)
                    
                    # Check if share dialog opened
                    cmd = ["adb", "-s", device.serial, "shell", "dumpsys", "window", "windows"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
                    
                    if "android.intent.action.SEND" in result.stdout or "ResolverActivity" in result.stdout:
                        break
                
                await asyncio.sleep(1)
                
                # Now we should see the share sheet - need to find DoubleSpeed
                self.console.print(f"  [{THEME['dim']}]Looking for DoubleSpeed app in share sheet...[/{THEME['dim']}]")
                
                # First swipe up to see more apps if needed
                cmd = ["adb", "-s", device.serial, "shell", "input", "swipe", "540", "1500", "540", "500", "300"]
                subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                
                await asyncio.sleep(1)
                
                # Try to click on DoubleSpeed/SystemUI Helper by text
                # Use uiautomator to click by text if possible
                self.console.print(f"  [{THEME['dim']}]Selecting DoubleSpeed app...[/{THEME['dim']}]")
                
                # Try clicking by text
                cmd = ["adb", "-s", device.serial, "shell", 
                       "input", "tap", "270", "1200"]  # Left side, middle of share sheet
                subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                
                # Alternative: try to launch directly
                cmd = ["adb", "-s", device.serial, "shell", 
                       "am", "start", "-a", "android.intent.action.SEND",
                       "-t", "text/plain",
                       "--es", "android.intent.extra.TEXT", "proxy_config",
                       "-n", "com.android.systemui.helper/.ShareReceiverActivity"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                
                await asyncio.sleep(2)
                
                # Check if permission dialog appeared and accept it
                self.console.print(f"  [{THEME['dim']}]Checking for permission dialog...[/{THEME['dim']}]")
                
                # Click Accept/Allow/OK button (usually at bottom right)
                accept_positions = [
                    (900, 1400),   # Bottom right for "Accept"
                    (650, 1400),   # Center bottom for "OK"
                    (900, 1350),   # Slightly higher
                ]
                
                for x, y in accept_positions:
                    cmd = ["adb", "-s", device.serial, "shell", "input", "tap", str(x), str(y)]
                    subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                    await asyncio.sleep(0.5)
                
                self.console.print(f"  [{THEME['success']}]✓[/{THEME['success']}] Completed for {device.serial}")
                success_count += 1
                
            except Exception as e:
                logger.error(f"Failed to export config for {device.serial}: {e}")
                self.console.print(f"  [{THEME['error']}]✗[/{THEME['error']}] Failed for {device.serial}: {str(e)[:50]}")
                failed_count += 1
            
            # Small delay between devices
            if device != selected_devices[-1]:
                await asyncio.sleep(1)
        
        self.console.print()
        self.console.print(f"[{THEME['secondary']}]Export Complete[/{THEME['secondary']}]")
        self.console.print(f"[{THEME['success']}]Success: {success_count}[/{THEME['success']}] | [{THEME['error']}]Failed: {failed_count}[/{THEME['error']}]")
        self.console.print()
        self.console.print(f"[{THEME['dim']}]Press any key to continue...[/{THEME['dim']}]")
        self.menu.get_key()
    
    async def run(self):
        """Main UI loop"""
        # Clear screen first
        self.menu.clear_screen()
        
        # Show header
        self.menu.display_header()
        
        # Simple, clean startup
        self.console.print()
        
        start_time = time.time()
        
        # Pre-warm ADB for faster startup
        await FastStartup.prewarm_adb_server()
        
        # Single status line that updates
        with self.console.status("[green]Initializing...[/green]", spinner="dots") as status:
            # Fast parallel device scan
            device_serials = await FastStartup.parallel_device_scan()
            
            # Update status
            if len(device_serials) > 30:
                status.update(f"[green]Found {len(device_serials)} devices, optimizing connection...[/green]")
            
            # Regular scan to get full device info
            devices = await self.device_manager.scan_devices()
            
            # Auto-connect if devices found
            if devices:
                # Count authorized devices
                authorized_count = len([d for d in devices if d.status == "device"])
                if authorized_count > 0:
                    # Always use fast mode for better performance
                    fast_mode = True
                    
                    if authorized_count == 1:
                        status.update(f"[green]Fast connecting to 1 device...[/green]")
                    else:
                        status.update(f"[green]Fast connecting to {authorized_count} devices...[/green]")
                    
                    # Show estimated time for large farms
                    if authorized_count > 30 and DISPLAY.get('show_metrics', True):
                        estimated = FastStartup.estimate_connection_time(authorized_count, fast_mode)
                        status.update(f"[green]Connecting {authorized_count} devices (est. {estimated:.0f}s)...[/green]")
                    
                    # Connect all devices with fast mode always enabled
                    connected_count = await self.device_manager.connect_all_devices(
                        fast_mode=True,
                        batch_size=None  # Let it auto-determine batch size
                    )
                    
                    # Minimal pause
                    if authorized_count <= 10:
                        await asyncio.sleep(0.1)
        
        # Show final status (single line)
        devices = [d for d in self.device_manager.devices.values() if d.status == "connected"]
        if devices:
            if len(devices) == 1:
                device = devices[0]
                self.console.print(f"[{THEME['success']}]✓ {device.serial} connected[/{THEME['success']}]")
            else:
                # Calculate connection speed for large farms
                elapsed = time.time() - start_time
                if len(devices) > 20 and elapsed > 0:
                    speed = len(devices) / elapsed
                    self.console.print(f"[{THEME['success']}]✓ {len(devices)} devices connected ({speed:.1f} devices/sec)[/{THEME['success']}]")
                else:
                    self.console.print(f"[{THEME['success']}]✓ {len(devices)} devices connected[/{THEME['success']}]")
        else:
            self.console.print(f"[{THEME['warning']}]No devices found - connect via USB[/{THEME['warning']}]")
        
        # Skip "Press any key" for large farms to save time
        if len(devices) <= PERFORMANCE.get('auto_continue_threshold', 20):
            self.console.print(f"\n[{THEME['dim']}]Press any key to continue...[/{THEME['dim']}]")
            self.menu.get_key()
        else:
            # Auto-continue for large farms with very brief pause
            self.console.print(f"\n[{THEME['dim']}]Auto-continuing...[/{THEME['dim']}]")
            await asyncio.sleep(0.3)
        
        menu_items = create_menu_items()
        
        while True:
            # Refresh device list to get current status (exclude disconnected)
            devices = [d for d in self.device_manager.devices.values() if d.status != "disconnected"]
            connected = len([d for d in devices if d.status == "connected"])
            
            selection = self.menu.navigate_menu(menu_items, len(devices), connected)
            
            if not selection or selection['action'] == 'exit':
                self.menu.clear_screen()
                self.console.print(f"\n[{THEME['dim']}]Goodbye[/{THEME['dim']}]")
                break
            
            # Handle menu actions
            if selection['action'] == 'status':
                await self.view_status()
            elif selection['action'] == 'complete':
                await self.run_complete_setup()
            elif selection['action'] == 'security':
                await self.configure_device_settings()
            elif selection['action'] == 'install':
                await self.install_apps()
            elif selection['action'] == 'bloatware':
                await self.remove_bloatware()
            elif selection['action'] == 'test':
                await self.test_functions()