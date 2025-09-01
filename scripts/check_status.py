#!/usr/bin/env python3
"""Check the status of security settings on connected devices"""

import asyncio
import subprocess
from rich.console import Console
from rich.table import Table
from core.device_manager import DeviceManager

console = Console()

async def check_device_status():
    """Check security settings status"""
    
    console.print("\n[bold cyan]📱 Device Security Status Check[/bold cyan]\n")
    
    # Initialize device manager
    manager = DeviceManager()
    devices = await manager.scan_devices()
    
    if not devices:
        console.print("[red]No devices found[/red]")
        return
    
    # Connect to devices
    await manager.connect_all_devices()
    connected = manager.get_connected_devices()
    
    for device in connected:
        console.print(f"\n[bold yellow]Device: {device.serial} ({device.model})[/bold yellow]")
        
        # Check various settings
        checks = {
            "Bluetooth": "settings get global bluetooth_on",
            "Mobile Data": "settings get global mobile_data",
            "WiFi Direct": "settings get global wifi_direct_auto_accept",
            "NFC": "settings get secure nfc_on",
            "Location": "settings get secure location_mode",
            "Backup": "settings get secure backup_enabled",
            "Ad Tracking": "settings get secure limit_ad_tracking",
            "Auto Update": "settings get global auto_update_policy"
        }
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Setting", width=20)
        table.add_column("Status", width=15)
        table.add_column("Value", width=10)
        
        for setting, command in checks.items():
            try:
                result = await manager.execute_adb_command(device, command)
                if result:
                    value = result.strip()
                    
                    # Interpret the value
                    if setting in ["Bluetooth", "Mobile Data", "WiFi Direct", "NFC", "Location", "Backup"]:
                        status = "✓ Disabled" if value in ["0", "null", ""] else f"⚠️ Enabled"
                        color = "green" if "Disabled" in status else "yellow"
                    elif setting == "Ad Tracking":
                        status = "✓ Limited" if value == "1" else "⚠️ Not Limited"
                        color = "green" if "Limited" in status else "yellow"
                    elif setting == "Auto Update":
                        status = "✓ Disabled" if value == "2" else "⚠️ Enabled"
                        color = "green" if "Disabled" in status else "yellow"
                    else:
                        status = "Unknown"
                        color = "dim"
                    
                    table.add_row(setting, f"[{color}]{status}[/{color}]", value or "null")
                else:
                    table.add_row(setting, "[red]Error[/red]", "-")
            except Exception as e:
                table.add_row(setting, "[red]Error[/red]", str(e)[:10])
        
        console.print(table)
        
        # Check installed apps
        console.print("\n[cyan]Checking for Super Proxy app...[/cyan]")
        result = await manager.execute_adb_command(device, "pm list packages | grep -i proxy")
        if result:
            console.print("[green]✓ Proxy-related packages found:[/green]")
            for line in result.strip().split('\n'):
                if line:
                    console.print(f"  • {line}")
        else:
            console.print("[yellow]⚠️ No proxy packages found[/yellow]")

if __name__ == "__main__":
    try:
        asyncio.run(check_device_status())
    except KeyboardInterrupt:
        console.print("\n[yellow]Check interrupted[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")