"""Interactive menu with arrow key navigation and forest green theme"""

import os
import sys
import termios
import tty
from typing import List, Optional, Callable
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.columns import Columns
from rich.table import Table
from rich import box


# Refined theme with less overwhelming green
THEME = {
    'primary': 'green',           # Primary accent
    'secondary': 'bright_white',  # Secondary text
    'accent': 'cyan',            # Accent elements
    'highlight': 'bold white',    # Selected items
    'success': 'green',          # Success states
    'warning': 'yellow',         # Warning states
    'error': 'red',              # Error states
    'text': 'white',             # Normal text
    'dim': 'bright_black'        # Dimmed elements
}


class InteractiveMenu:
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.selected_index = 0
        
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def get_key(self):
        """Get single key press"""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            while True:
                key = sys.stdin.read(1)
                if key == '\x1b':  # ESC sequence
                    # Read next 2 chars to check if it's an arrow key
                    next_chars = sys.stdin.read(2)
                    if next_chars in ['[A', '[B', '[C', '[D']:  # Arrow keys
                        return key + next_chars
                    # Ignore standalone ESC - continue reading
                    continue
                else:
                    return key
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    def display_header(self):
        """Display simple, clean header"""
        header_text = Text("PHONE FARM MANAGER", style=f"bold {THEME['primary']}")
        header_text.justify = "center"
        
        header = Panel(
            header_text,
            border_style=THEME['primary'],
            box=box.DOUBLE_EDGE,
            padding=(0, 0),
            style="on black"
        )
        
        self.console.print(header)
    
    def display_menu(self, items: List[dict], title: str = "Main Menu", show_separators: bool = True):
        """Display clean, aligned menu"""
        menu_text = Text()
        
        for idx, item in enumerate(items):
            label = item.get('label', '')
            
            # Simple selection with arrow
            if idx == self.selected_index:
                menu_text.append("  ▶  ", style=THEME['primary'])
                menu_text.append(label, style=f"bold {THEME['highlight']}")
            else:
                menu_text.append("     ", style="")
                if item.get('action') in ['exit', 'back']:
                    menu_text.append(label, style=THEME['dim'])
                else:
                    menu_text.append(label, style=THEME['text'])
            
            # Only add separators for main menu
            if show_separators and idx in [0, 1, 4]:
                menu_text.append("\n     ─────────────────────────────", style=THEME['dim'])
            
            if idx < len(items) - 1:
                menu_text.append("\n")
        
        # Simple controls line
        menu_text.append("\n\n  ↑↓ Navigate   Enter Select   Q Exit", style=THEME['dim'])
        
        # Clean panel
        panel = Panel(
            menu_text,
            border_style=THEME['primary'],
            box=box.ROUNDED,
            width=45,
            padding=(1, 2),
            style="on black"
        )
        
        self.console.print(panel)
    
    def display_status(self, devices_count: int = 0, connected_count: int = 0):
        """Display simple status line"""
        status_text = Text()
        status_text.append("Devices: ", style=THEME['dim'])
        status_text.append(f"{devices_count}", style=THEME['secondary'])
        status_text.append("  │  ", style=THEME['dim'])
        status_text.append("Connected: ", style=THEME['dim'])
        color = THEME['success'] if connected_count > 0 else THEME['dim']
        status_text.append(f"{connected_count}", style=color)
        
        status_text.justify = "center"
        self.console.print(status_text)
        self.console.print()
    
    def navigate_menu(self, menu_items: List[dict], devices_count: int = 0, connected_count: int = 0, show_separators: bool = True) -> Optional[dict]:
        """Navigate menu with arrow keys"""
        while True:
            self.clear_screen()
            self.display_header()
            self.console.print()  # Space after header
            self.display_status(devices_count, connected_count)
            self.console.print()  # Space before menu
            self.display_menu(menu_items, show_separators=show_separators)
            
            key = self.get_key()
            
            # Arrow navigation
            if key == '\x1b[A':  # Up arrow
                self.selected_index = (self.selected_index - 1) % len(menu_items)
            elif key == '\x1b[B':  # Down arrow
                self.selected_index = (self.selected_index + 1) % len(menu_items)
            elif key in ['\r', '\n']:  # Enter
                return menu_items[self.selected_index]
            elif key in ['\x03', 'q', 'Q']:  # Ctrl+C, q (ESC is ignored)
                return None
            
            # Number shortcuts (1-7 for menu items)
            elif key.isdigit():
                num = int(key) - 1
                if 0 <= num < len(menu_items):
                    self.selected_index = num
                    return menu_items[num]
    
    def show_loading(self, message: str):
        """Display loading animation"""
        self.clear_screen()
        self.display_header()
        
        loading_text = Text()
        loading_text.append("⠋ ", style=THEME['accent'])
        loading_text.append(message, style=THEME['text'])
        
        panel = Panel(
            Align.center(loading_text),
            border_style=THEME['primary'],
            box=box.ROUNDED
        )
        
        self.console.print(panel)
    
    def display_device_table(self, devices: List):
        """Display devices in a clean table"""
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
        table.add_column("Interface", style=THEME['text'], justify="left")
        table.add_column("IP Address", style=THEME['text'])
        table.add_column("Proxy", justify="center")
        table.add_column("Status", justify="center")
        
        for idx, device in enumerate(devices, 1):
            if device.status == "connected":
                status_color = THEME['success']
                status_icon = "▸"  # Filled chevron for connected
            elif device.status == "device":
                status_color = THEME['warning']
                status_icon = "›"  # Single chevron for authorized
            elif device.status == "unauthorized":
                status_color = THEME['error']
                status_icon = "‹"  # Left chevron for unauthorized
            elif device.status == "disconnected":
                status_color = THEME['dim']
                status_icon = "·"  # Small dot for disconnected
            else:
                status_color = THEME['text']
                status_icon = "?"
            
            # Format network info
            interface_display = "-"
            ip_display = "-"
            
            if hasattr(device, 'network_info') and device.network_info and device.network_info.get('primary_ip'):
                ip_display = device.network_info['primary_ip']
                interface = device.network_info['primary_interface']
                
                # Get interface type
                interface_type = ""
                for iface in device.network_info.get('interfaces', []):
                    if iface['name'] == interface:
                        interface_type = iface['type']
                        break
                
                # Format interface display - interface name in white, type can be subtle
                interface_display = f"{interface} ({interface_type})"
            
            # Format proxy status with color coding
            proxy_display = "-"
            proxy_color = THEME['dim']
            
            if hasattr(device, 'proxy_status') and device.proxy_status:
                if device.proxy_status == "Running":
                    proxy_display = "▶ Running"
                    proxy_color = THEME['success']
                elif device.proxy_status == "App Open":
                    proxy_display = "◐ App Open"
                    proxy_color = THEME['warning']
                elif device.proxy_status == "Set (No App)":
                    proxy_display = "⚠ Set (No App)"
                    proxy_color = THEME['warning']
                elif device.proxy_status == "Stopped":
                    proxy_display = "◼ Stopped"
                    proxy_color = THEME['dim']
                else:
                    proxy_display = device.proxy_status
                    proxy_color = THEME['dim']
            
            table.add_row(
                str(idx),
                device.serial,
                device.model,
                interface_display,
                ip_display,
                Text(proxy_display, style=proxy_color),
                Text(f"{status_icon} {device.status}", style=status_color)
            )
        
        self.console.print(table)
        self.console.print()


def create_menu_items():
    """Create clean menu items"""
    return [
        {
            'label': '[1] View Device Status',
            'action': 'status'
        },
        {
            'label': '[2] Run Complete Setup',
            'action': 'complete'
        },
        {
            'label': '[3] Configure Device Settings',
            'action': 'security'
        },
        {
            'label': '[4] Install Applications',
            'action': 'install'
        },
        {
            'label': '[5] Remove Bloatware',
            'action': 'bloatware'
        },
        {
            'label': '[6] Test Functions',
            'action': 'test'
        },
        {
            'label': '[Q] Exit',
            'action': 'exit'
        }
    ]