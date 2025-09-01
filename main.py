#!/usr/bin/env python3
# If running directly, use: source venv/bin/activate && python main.py run

import asyncio
import sys
import os
import signal
import atexit
import subprocess
from pathlib import Path
from loguru import logger
from rich.console import Console
import click

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ui.terminal_interface_v2 import EnhancedTerminalInterface

# Global variable to track running tasks
_running_tasks = set()

def cleanup_on_exit():
    """Cleanup function to kill ADB server and cancel tasks"""
    try:
        # Kill ADB server
        subprocess.run(["adb", "kill-server"], capture_output=True, timeout=5)
        logger.info("ADB server stopped")
    except:
        pass
    
    # Cancel all running asyncio tasks
    for task in _running_tasks:
        if not task.done():
            task.cancel()
    
    logger.info("Cleanup completed")

# Register cleanup function
atexit.register(cleanup_on_exit)

def signal_handler(signum, frame):
    """Handle termination signals"""
    logger.info(f"Received signal {signum}, cleaning up...")
    cleanup_on_exit()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


# Configure logging
logger.remove()  # Remove default handler
logger.add(
    "logs/phone_farm_{time}.log",
    rotation="1 day",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} - {message}"
)
logger.add(sys.stdout, level="WARNING", format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>")


console = Console()


def check_requirements():
    """Check if all requirements are installed"""
    try:
        import uiautomator2
        import adb_shell
        import rich
    except ImportError as e:
        console.print(f"[red]Missing required packages. Please run:[/red]")
        console.print("[yellow]pip install -r requirements.txt[/yellow]")
        sys.exit(1)
    
    # Check if ADB is installed
    try:
        import shutil
        if not shutil.which("adb"):
            console.print("[red]ADB is not installed or not in PATH[/red]")
            console.print("[yellow]Please install Android SDK Platform Tools[/yellow]")
            console.print("Download from: https://developer.android.com/studio/releases/platform-tools")
            sys.exit(1)
    except Exception as e:
        # If we can't check, assume it's available and let it fail later if not
        logger.warning(f"Could not verify ADB installation: {e}")


@click.group()
def cli():
    """Phone Farm Device Manager - Manage 100+ Android devices with ease"""
    pass


@cli.command()
def setup():
    """Run interactive setup wizard"""
    console.print("[cyan]Welcome to Phone Farm Device Manager Setup![/cyan]")
    console.print()
    
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("config", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    console.print("[green]✓[/green] Created necessary directories")
    
    # Check requirements
    check_requirements()
    console.print("[green]✓[/green] All requirements satisfied")
    
    # Start ADB server
    console.print("[yellow]Starting ADB server...[/yellow]")
    try:
        import subprocess
        result = subprocess.run(["adb", "start-server"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            console.print("[green]✓[/green] ADB server started")
        else:
            console.print(f"[yellow]⚠[/yellow] ADB server may already be running")
    except Exception as e:
        console.print(f"[yellow]⚠[/yellow] Could not start ADB server: {e}")
    
    console.print()
    console.print("[bold green]Setup complete! Run 'python main.py run' to start the manager.[/bold green]")


@cli.command()
def run():
    """Run the phone farm manager"""
    check_requirements()
    
    # Create UI and run
    ui = EnhancedTerminalInterface()
    
    try:
        asyncio.run(ui.run())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user, cleaning up...[/yellow]")
        cleanup_on_exit()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        console.print(f"\n[red]Fatal error: {e}[/red]")
        cleanup_on_exit()
        sys.exit(1)


@cli.command()
@click.argument('device_serial', required=False)
def devices(device_serial):
    """List connected devices or show info for specific device"""
    import subprocess
    
    if device_serial:
        # Show specific device info
        result = subprocess.run(
            ["adb", "-s", device_serial, "shell", "getprop"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            props = {}
            for line in result.stdout.split('\n'):
                if ':' in line:
                    key, value = line.strip().replace('[', '').replace(']', '').split(': ')
                    props[key] = value
            
            console.print(f"\n[bold cyan]Device: {device_serial}[/bold cyan]")
            console.print(f"Model: {props.get('ro.product.model', 'Unknown')}")
            console.print(f"Brand: {props.get('ro.product.brand', 'Unknown')}")
            console.print(f"Android: {props.get('ro.build.version.release', 'Unknown')}")
            console.print(f"SDK: {props.get('ro.build.version.sdk', 'Unknown')}")
        else:
            console.print(f"[red]Failed to get info for device {device_serial}[/red]")
    else:
        # List all devices
        result = subprocess.run(["adb", "devices", "-l"], capture_output=True, text=True)
        console.print("\n[bold cyan]Connected Devices:[/bold cyan]")
        
        lines = result.stdout.strip().split('\n')[1:]
        if not lines or not lines[0]:
            console.print("[yellow]No devices connected[/yellow]")
        else:
            for line in lines:
                if line.strip():
                    console.print(f"  • {line}")


@cli.command()
@click.option('--serial', '-s', help='Target specific device')
def test(serial):
    """Test connection to device(s)"""
    import subprocess
    
    console.print("[cyan]Testing device connection...[/cyan]")
    
    cmd = ["adb"]
    if serial:
        cmd.extend(["-s", serial])
    cmd.extend(["shell", "echo", "Connection successful"])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        console.print(f"[green]✓ {result.stdout.strip()}[/green]")
    else:
        console.print(f"[red]✗ Connection failed: {result.stderr}[/red]")


if __name__ == "__main__":
    cli()