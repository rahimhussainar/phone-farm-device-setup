"""Allowlist configuration - Only these apps should remain on the device"""

from config.samsung_critical import SAMSUNG_CRITICAL_NEVER_REMOVE

# CRITICAL SYSTEM APPS - Never remove these
SYSTEM_CRITICAL = [
    # Core Android System
    "android",
    "com.android.systemui",
    "com.android.settings",
    "com.android.phone",
    "com.android.server.telecom",
    "com.android.providers.telephony",
    "com.android.providers.settings",
    "com.android.providers.media",
    "com.android.providers.downloads",
    "com.android.providers.contacts",
    "com.android.providers.calendar",
    "com.android.providers.blockednumber",
    "com.android.providers.userdictionary",
    "com.android.packageinstaller",
    "com.android.permissioncontroller",
    "com.android.keychain",
    "com.android.certinstaller",
    "com.android.carrierconfig",
    "com.android.carrierdefaultapp",
    "com.android.localtransport",
    "com.android.location.fused",
    "com.android.inputdevices",
    "com.android.bluetooth",
    "com.android.bluetoothmidiservice",
    "com.android.wifi.resources",
    "com.android.shell",
    "com.android.mms.service",
    "com.android.mtp",
    "com.android.nfc",
    "com.android.se",
    "com.android.ons",
    "com.android.companiondevicemanager",
    "com.android.intentresolver",
    "com.android.backupconfirm",
    "com.android.sharedstoragebackup",
    "com.android.storagemanager",
    "com.android.externalstorage",
    "com.android.cellbroadcastservice",
    "com.android.cellbroadcastreceiver",
    
    # Google Play Services (required for most apps)
    "com.google.android.gms",
    "com.google.android.gsf",
    "com.android.vending",  # Google Play Store
    "com.google.android.webview",
    "com.google.android.packageinstaller",
    "com.google.android.permissioncontroller",
    "com.google.android.ext.services",
    "com.google.android.ext.shared",
    "com.google.android.configupdater",
    "com.google.android.networkstack",
    "com.google.android.networkstack.tethering",
    
    # Samsung Core System (for Samsung devices)
    "com.samsung.android.providers.contacts",
    "com.samsung.android.providers.media",
    "com.samsung.android.providers.factory",
    "com.samsung.android.incallui",
    "com.samsung.android.dialer",
    "com.sec.android.app.launcher",  # Samsung launcher
    "com.samsung.android.messaging",
    "com.samsung.android.settings.bixby",
    "com.sec.android.emergencylauncher",
    "com.samsung.android.emergency",
    
    # Essential Samsung services
    "com.samsung.android.connectivity",
    "com.samsung.android.mdecservice",
    "com.samsung.android.mobileservice",
    "com.samsung.android.authfw",
    "com.samsung.android.knox.containercore",
    "com.samsung.android.knox.attestation",
    "com.sec.android.provider.badge",
    
    # Basic functionality
    "com.android.chrome",  # Chrome browser (or keep Samsung browser below)
    # "com.sec.android.app.sbrowser",  # Samsung Internet (alternative to Chrome)
]

# OPTIONAL APPS - Include these based on requirements
OPTIONAL_APPS = [
    # Google Apps (choose what you need)
    "com.google.android.apps.maps",
    "com.google.android.gm",  # Gmail
    "com.google.android.apps.docs",
    "com.google.android.apps.photos",
    "com.google.android.apps.messaging",
    "com.google.android.calculator",
    "com.google.android.calendar",
    "com.google.android.contacts",
    
    # Samsung Apps (choose what you need)
    "com.samsung.android.calendar",
    "com.samsung.android.app.contacts",
    "com.sec.android.gallery3d",
    "com.sec.android.app.camera",
    "com.sec.android.app.myfiles",
    "com.sec.android.app.popupcalculator",
    "com.sec.android.app.clockpackage",
    "com.samsung.android.app.notes",
]

# PHONE FARM SPECIFIC APPS - Apps needed for phone farm operation
PHONE_FARM_APPS = [
    "com.zhiliaoapp.musically",  # TikTok
    # Add your other phone farm apps here
]

def get_full_allowlist(include_optional=False, include_phone_farm=True):
    """Get the complete allowlist based on configuration"""
    allowlist = SYSTEM_CRITICAL.copy()
    
    # ALWAYS include Samsung critical apps to prevent bricking
    allowlist.extend(SAMSUNG_CRITICAL_NEVER_REMOVE)
    
    if include_optional:
        allowlist.extend(OPTIONAL_APPS)
    
    if include_phone_farm:
        allowlist.extend(PHONE_FARM_APPS)
    
    # Remove duplicates
    return list(set(allowlist))

def is_allowed(package_name, allowlist=None):
    """Check if a package is in the allowlist"""
    if allowlist is None:
        allowlist = get_full_allowlist()
    
    # Direct match
    if package_name in allowlist:
        return True
    
    # Check for critical system prefixes that should always be allowed
    critical_prefixes = [
        "android.auto_generated",
        "com.android.cts",
        "com.android.internal",
        "com.android.overlay",
        "com.samsung.internal",
        "com.samsung.android.overlay",
        "com.google.android.overlay",
        "com.sec.factory",
        "com.sec.android.Ril",
        "com.sec.imsservice",
        "com.samsung.ipservice",
        "com.samsung.klmsagent",
    ]
    
    for prefix in critical_prefixes:
        if package_name.startswith(prefix):
            return True
    
    return False

def should_remove(package_name, allowlist=None):
    """Determine if a package should be removed"""
    return not is_allowed(package_name, allowlist)