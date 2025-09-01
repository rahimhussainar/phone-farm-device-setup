#!/usr/bin/env python3
"""Batch setup script for phone farm - non-interactive mode"""

import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
import click

sys.path.insert(0, str(Path(__file__).parent))

from core.device_manager import DeviceManager
from core.device_configurator import DeviceConfigurator  
from core.app_manager import AppManager

console = Console()

async def run_complete_setup():
    """Run complete setup on all connected devices"""
    
    console.print("\n[bold cyan]📱 Phone Farm Batch Setup[/bold cyan]\n")
    
    # Initialize managers
    device_manager = DeviceManager()
    configurator = DeviceConfigurator()
    app_manager = AppManager()
    
    # Scan for devices
    console.print("[yellow]Scanning for devices...[/yellow]")
    devices = await device_manager.scan_devices()
    
    if not devices:
        console.print("[red]No devices found! Please connect devices and enable USB debugging.[/red]")
        return
    
    console.print(f"[green]Found {len(devices)} device(s)[/green]\n")
    
    # Connect to all devices
    console.print("[yellow]Connecting to devices...[/yellow]")
    connected_count = await device_manager.connect_all_devices()
    
    if connected_count == 0:
        console.print("[red]Failed to connect to any devices[/red]")
        return
        
    console.print(f"[green]Connected to {connected_count} device(s)[/green]\n")
    
    connected_devices = device_manager.get_connected_devices()
    
    # Step 1: Configure Security
    console.rule("[bold]Step 1: Security Configuration[/bold]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        
        main_task = progress.add_task("[cyan]Configuring security...", total=len(connected_devices))
        
        for device in connected_devices:
            device_task = progress.add_task(f"[yellow]{device.serial}", total=9)
            
            # Run security configurations
            results = await configurator.configure_device_security(device)
            
            for setting, success in results.items():
                progress.update(device_task, advance=1)
                status = "✓" if success else "✗"
                color = "green" if success else "red"
                console.print(f"  [{color}]{status}[/{color}] {setting}")
            
            progress.update(main_task, advance=1)
            progress.remove_task(device_task)
    
    # Step 2: Disable Auto-Updates
    console.rule("[bold]Step 2: Disable Auto-Updates[/bold]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        
        task = progress.add_task("[cyan]Disabling auto-updates...", total=len(connected_devices))
        
        for device in connected_devices:
            try:
                await app_manager.disable_app_auto_update(device)
                console.print(f"  [green]✓[/green] {device.serial}")
            except Exception as e:
                console.print(f"  [red]✗[/red] {device.serial}: {e}")
            
            progress.update(task, advance=1)
    
    # Step 3: Install Super Proxy
    console.rule("[bold]Step 3: Install Super Proxy[/bold]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        
        task = progress.add_task("[cyan]Installing Super Proxy...", total=len(connected_devices))
        
        for device in connected_devices:
            try:
                success = await app_manager.install_super_proxy(device)
                if success:
                    console.print(f"  [green]✓[/green] {device.serial}")
                else:
                    console.print(f"  [red]✗[/red] {device.serial}: Installation failed")
            except Exception as e:
                console.print(f"  [red]✗[/red] {device.serial}: {e}")
            
            progress.update(task, advance=1)
    
    # Summary
    console.rule("[bold]Setup Complete[/bold]")
    console.print(f"\n[bold green]✓ Setup completed for {connected_count} device(s)![/bold green]")
    console.print("\n[yellow]Note: Proxy configuration pending - update configure_super_proxy() with proxy details[/yellow]")


@click.command()
@click.option('--security-only', is_flag=True, help='Only configure security settings')
@click.option('--apps-only', is_flag=True, help='Only install apps')
def main(security_only, apps_only):
    """Run batch setup on all connected devices"""
    
    if security_only:
        console.print("[cyan]Running security configuration only...[/cyan]")
    elif apps_only:
        console.print("[cyan]Running app installation only...[/cyan]")
    else:
        console.print("[cyan]Running complete setup...[/cyan]")
    
    try:
        asyncio.run(run_complete_setup())
    except KeyboardInterrupt:
        console.print("\n[yellow]Setup interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()