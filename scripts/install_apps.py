#!/usr/bin/env python3
"""Manual app installation helper"""

import os
import subprocess
import asyncio
from rich.console import Console
from rich.table import Table
from core.device_manager import DeviceManager

console = Console()

# Common apps for phone farms with their package names and APK download links
PHONE_FARM_APPS = {
    "Phone Clone": {
        "package": "com.coloros.backuprestore",
        "apk_url": "https://apkpure.com/phone-clone/com.coloros.backuprestore",
        "description": "Device cloning app"
    },
    "Auto Clicker": {
        "package": "com.truedevelopersstudio.automatictap.autoclicker",
        "apk_url": "https://apkpure.com/auto-clicker/com.truedevelopersstudio.automatictap.autoclicker",
        "description": "Automation tool"
    }
}

def check_adb():
    """Check if ADB is available"""
    try:
        result = subprocess.run(["adb", "version"], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def get_connected_devices():
    """Get list of connected devices"""
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=10)
        devices = []
        lines = result.stdout.strip().split('\n')[1:]
        for line in lines:
            if '\t' in line:
                serial = line.split('\t')[0]
                status = line.split('\t')[1]
                if status == "device":
                    devices.append(serial)
        return devices
    except:
        return []

def install_apk(device_serial: str, apk_path: str) -> bool:
    """Install APK on device"""
    try:
        console.print(f"[yellow]Installing {apk_path} on {device_serial}...[/yellow]")
        result = subprocess.run(
            ["adb", "-s", device_serial, "install", "-r", "-g", apk_path],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if "Success" in result.stdout:
            console.print(f"[green]✓ Successfully installed on {device_serial}[/green]")
            return True
        else:
            console.print(f"[red]✗ Failed to install on {device_serial}: {result.stderr}[/red]")
            return False
    except subprocess.TimeoutExpired:
        console.print(f"[red]✗ Installation timeout on {device_serial}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]✗ Error installing on {device_serial}: {e}[/red]")
        return False

def check_installed_apps(device_serial: str):
    """Check which apps are installed on device"""
    installed = {}
    for app_name, app_info in PHONE_FARM_APPS.items():
        try:
            result = subprocess.run(
                ["adb", "-s", device_serial, "shell", f"pm list packages | grep {app_info['package']}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            installed[app_name] = app_info['package'] in result.stdout
        except:
            installed[app_name] = False
    return installed

def main():
    """Main installation helper"""
    console.print("\n[bold cyan]📱 Phone Farm App Installer[/bold cyan]\n")
    
    if not check_adb():
        console.print("[red]ADB not found! Please install Android SDK Platform Tools[/red]")
        return
    
    devices = get_connected_devices()
    if not devices:
        console.print("[red]No authorized devices connected![/red]")
        console.print("[yellow]Please connect devices and authorize USB debugging[/yellow]")
        return
    
    console.print(f"[green]Found {len(devices)} device(s)[/green]\n")
    
    # Create APK directory
    apk_dir = "apks"
    os.makedirs(apk_dir, exist_ok=True)
    
    # Check installed apps on each device
    for device in devices:
        console.print(f"\n[bold]Device: {device}[/bold]")
        installed = check_installed_apps(device)
        
        table = Table(title="App Status", show_header=True)
        table.add_column("App", style="cyan")
        table.add_column("Package", style="dim")
        table.add_column("Status", style="white")
        
        for app_name, app_info in PHONE_FARM_APPS.items():
            status = "✓ Installed" if installed[app_name] else "✗ Not Installed"
            status_style = "green" if installed[app_name] else "red"
            table.add_row(app_name, app_info['package'], f"[{status_style}]{status}[/{status_style}]")
        
        console.print(table)
    
    # Installation instructions
    console.print("\n[bold yellow]Installation Options:[/bold yellow]")
    console.print("\n1. [cyan]Automatic Installation (APK required):[/cyan]")
    console.print("   - Download APKs from APKPure or APKMirror")
    console.print(f"   - Place APK files in the '{apk_dir}' folder")
    console.print("   - Name them: packagename.apk (e.g., com.example.app.apk)")
    console.print("   - Run this script again to install")
    
    console.print("\n2. [cyan]Manual Installation:[/cyan]")
    console.print("   adb -s DEVICE_SERIAL install -r -g path/to/app.apk")
    
    console.print("\n3. [cyan]Direct Download Links:[/cyan]")
    for app_name, app_info in PHONE_FARM_APPS.items():
        console.print(f"   {app_name}: {app_info['apk_url']}")
    
    # Check for APKs in the directory
    console.print(f"\n[yellow]Checking for APKs in '{apk_dir}' folder...[/yellow]")
    apk_files = [f for f in os.listdir(apk_dir) if f.endswith('.apk')] if os.path.exists(apk_dir) else []
    
    if apk_files:
        console.print(f"[green]Found {len(apk_files)} APK(s):[/green]")
        for apk in apk_files:
            console.print(f"  • {apk}")
        
        if Confirm.ask("\nInstall these APKs on all devices?"):
            for device in devices:
                console.print(f"\n[bold]Installing on {device}:[/bold]")
                for apk in apk_files:
                    apk_path = os.path.join(apk_dir, apk)
                    install_apk(device, apk_path)
    else:
        console.print(f"[yellow]No APKs found in '{apk_dir}' folder[/yellow]")
        console.print("\n[dim]Download APKs and place them in the 'apks' folder, then run this script again[/dim]")

if __name__ == "__main__":
    from rich.prompt import Confirm
    main()