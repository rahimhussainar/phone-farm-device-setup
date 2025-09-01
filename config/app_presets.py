"""Common app presets for phone farms"""

# Popular apps for phone farms with their Play Store URLs
APP_PRESETS = {
    "Auto Clicker": {
        "package": "com.truedevelopersstudio.automatictap.autoclicker",
        "url": "https://play.google.com/store/apps/details?id=com.truedevelopersstudio.automatictap.autoclicker",
        "description": "Automation tool"
    },
    "Phone Clone": {
        "package": "com.coloros.backuprestore",
        "url": "https://play.google.com/store/apps/details?id=com.coloros.backuprestore",
        "description": "Device cloning"
    },
    "TeamViewer": {
        "package": "com.teamviewer.quicksupport.market",
        "url": "https://play.google.com/store/apps/details?id=com.teamviewer.quicksupport.market",
        "description": "Remote control"
    },
    "AnyDesk": {
        "package": "com.anydesk.anydeskandroid",
        "url": "https://play.google.com/store/apps/details?id=com.anydesk.anydeskandroid",
        "description": "Remote desktop"
    },
    "Termux": {
        "package": "com.termux",
        "url": "https://play.google.com/store/apps/details?id=com.termux",
        "description": "Linux terminal"
    }
}

def get_app_url(app_name: str) -> str:
    """Get Play Store URL for a preset app"""
    if app_name in APP_PRESETS:
        return APP_PRESETS[app_name]["url"]
    return None

def get_app_package(app_name: str) -> str:
    """Get package name for a preset app"""
    if app_name in APP_PRESETS:
        return APP_PRESETS[app_name]["package"]
    return None