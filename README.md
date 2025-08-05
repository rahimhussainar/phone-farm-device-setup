# Phone Farm Setup Tool

Simple, automated setup for Android phone farms with proxy support.

## Quick Start

1. **Setup Python environment:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Connect phones and run setup:**
```bash
python setup_phones_force.py
```

3. **Verify after reboot (wait 2-3 minutes):**
```bash
python setup_phones_force.py --verify
```

## What It Does

- ✅ Renames devices to serial numbers (e.g., "Moto G" → "ZY22LFDK28")
- ✅ Disables Bluetooth completely
- ✅ Mutes all volumes and enables silent mode
- ✅ Disables auto-rotate
- ✅ Disables automatic updates
- ✅ Disables animations for performance
- ✅ Keeps WiFi always on
- ✅ **Keeps Play Store functional** (for app installation)

## Files in This Project

- `setup_phones_force.py` - Main setup script
- `proxy_manager.py` - Google Sheets integration for proxy management
- `collect_serials.py` - Collects device serial numbers
- `baseline_setup.sh` - Legacy bash setup script
- `requirements.txt` - Python dependencies
- `sa_key.json` - Google service account (for Sheets integration)
- `vpn_config.csv` - Local device/proxy tracking

## Google Sheets Integration (Optional)

To manage proxies via Google Sheets:

1. Enable Google Drive & Sheets APIs:
   - https://console.developers.google.com/apis/api/drive.googleapis.com
   - https://console.developers.google.com/apis/api/sheets.googleapis.com

2. Create sheet "Phone Farm Proxies" with columns:
   - proxy_host, proxy_port, proxy_username, proxy_password, status

3. Share sheet with service account email from `sa_key.json`

## Proxy Setup

Since you need a VPN app for SOCKS5 proxies:

1. Install from Play Store:
   - **Shadowsocks** (free, recommended)
   - **Postern** (paid)
   - **SocksDroid** (free)

2. Configure with your SOCKS5 credentials

3. Enable Always-on VPN in Settings

## Troubleshooting

**"No devices found"**
- Enable USB debugging on phones
- Trust computer when prompted
- Check: `adb devices`

**Settings not applying**
- Wait for reboot to complete
- Run verify command
- Some settings need manual confirmation on first run