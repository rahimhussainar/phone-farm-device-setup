"""Bloatware package definitions - apps safe to remove/disable"""

# SAFE TO REMOVE - These apps are generally safe to uninstall
SAFE_TO_REMOVE = [
    # Facebook
    "com.facebook.katana",
    "com.facebook.system",
    "com.facebook.appmanager",
    "com.facebook.services",
    "com.instagram.android",
    
    # Microsoft
    "com.microsoft.skydrive",  # OneDrive
    "com.microsoft.skydrive.content.external",  # OneDrive
    "com.microsoft.office.excel",
    "com.microsoft.office.word",
    "com.microsoft.office.powerpoint",
    "com.microsoft.office.outlook",
    "com.skype.raider",
    "com.microsoft.office.officehubrow",
    
    # Google Apps (optional - keep only what you need)
    "com.google.android.youtube",
    "com.google.android.videos",
    "com.google.android.music",
    "com.google.android.apps.youtube.music",  # YouTube Music
    "com.google.android.apps.magazines",
    "com.google.android.apps.books",
    "com.google.android.apps.tachyon",  # Google Duo
    "com.google.android.apps.podcasts",
    "com.google.android.apps.googleassistant",
    "com.google.android.googlequicksearchbox",  # Google App
    "com.google.android.apps.bard",  # Google Gemini/Bard
    "com.google.android.apps.gemini.android",  # Google Gemini
    
    # Samsung Bloatware
    "com.samsung.android.game.gamehome",
    "com.samsung.android.game.gametools",
    "com.samsung.android.game.gos",
    "com.samsung.android.ardrawing",
    "com.samsung.android.aremoji",
    "com.samsung.android.bixby.agent",
    "com.samsung.android.bixby.service",
    "com.samsung.android.bixvision.framework",
    "com.samsung.android.svoiceime",
    "com.samsung.android.app.tips",
    "com.samsung.android.scloud",
    "com.samsung.android.spayfw",
    "com.samsung.android.kidsinstaller",
    "com.samsung.android.app.social",
    
    # Carrier Apps (Verizon, AT&T, T-Mobile, Sprint)
    "com.verizon.mips.services",
    "com.verizon.services",
    "com.verizon.vzwavs",
    "com.vzw.hss.myverizon",
    "com.att.android.attsmartwifi",
    "com.att.myWireless",
    "com.att.tv",
    "com.tmobile.services.nameid",
    "com.tmobile.tmo",
    
    # Social Media
    "com.twitter.android",
    "com.snapchat.android",
    "com.zhiliaoapp.musically",  # TikTok
    "com.whatsapp",
    "com.linkedin.android",
    "com.pinterest",
    
    # Games
    "com.king.candycrushsaga",
    "com.rovio.angrybirds",
    "com.supercell.clashofclans",
    "com.scopely.monopolygo",
    "com.tripledot.solitaire",
    "com.tripledot.woodoku",
    "com.pixel.art.coloring.color.number",
    "com.vitastudio.mahjong",
    "com.block.juggle",  # Block Blast
    "com.dreamgames.royalkingdom",  # Royal Kingdom
    "com.bubbleshooter.popbubbles.collectcards",  # Bubble Shooter
    "com.mobilityware.solitaire",  # Solitaire
    
    # Shopping/Services
    "com.amazon.mShop.android.shopping",
    "com.amazon.kindle",
    "com.amazon.mp3",  # Amazon Music
    "com.ebay.mobile",
    "com.alibaba.aliexpresshd",
    "com.squareup.cash",
    "com.booking",  # Booking.com
    
    # Job/Finance Apps
    "com.indeed.android.jobsearch",  # Indeed Job Search
    "com.onedebit.chime",  # Chime Banking
    
    # News/Media
    "flipboard.app",
    "com.cnn.mobile.android.phone",
    "com.foxnews.android",
    "com.localweather.radar.climate",
    
    # AT&T Bloatware
    "com.att.csoiam.mobilekey",
    "com.att.deviceunlock",
    "com.att.dh",
    "com.att.iqi",
    "com.att.mobilesecurity",
    "com.att.personalcloud",
    "com.aura.jet.att",
    "com.aura.oobe.att",
    
    # Remote Support/Access Apps
    "com.rsupport.rs.activity.rsupport.aas2",  # RSupport Remote Access
    
    # Additional Samsung Bloatware
    "com.samsung.android.tvplus",
    "com.samsung.android.themestore",
    "com.samsung.android.themecenter",
    "com.samsung.android.stickercenter",
    "com.samsung.android.aremojieditor",
    "com.samsung.android.app.dressroom",
    "com.samsung.android.forest",
]

# SAFE TO DISABLE - These system apps can be safely disabled but not uninstalled
SAFE_TO_DISABLE = [
    # Google Services (disable if not using Google services)
    "com.google.android.feedback",
    "com.google.android.printservice.recommendation",
    "com.google.android.apps.wellbeing",
    "com.google.android.marvin.talkback",
    
    # Samsung System Apps
    "com.samsung.android.email.provider",
    "com.samsung.android.app.notes",
    "com.samsung.android.calendar",
    "com.samsung.android.contacts",
    "com.sec.android.app.sbrowser",  # Samsung Internet
    "com.samsung.android.messaging",
    "com.samsung.android.dialer",
    
    # System Features
    "com.android.dreams.basic",
    "com.android.dreams.phototable",
    "com.android.printspooler",
    "com.android.bips",
    "com.android.bookmarkprovider",
    "com.android.browser",
    "com.android.calendar",
    "com.android.cellbroadcastreceiver",
    "com.android.emergency",
    "com.android.hotwordenrollment.okgoogle",
    "com.android.stk",
    "com.android.wallpaper.livepicker",
    "com.android.wallpaperbackup",
    "com.android.wallpapercropper",
]

# DANGEROUS - DO NOT REMOVE (System critical)
DO_NOT_REMOVE = [
    "com.android.systemui",
    "com.android.settings",
    "com.android.phone",
    "com.android.server.telecom",
    "com.android.providers.telephony",
    "com.android.providers.settings",
    "com.android.providers.media",
    "com.android.providers.downloads",
    "com.android.providers.contacts",
    "com.android.packageinstaller",
    "com.android.keychain",
    "com.android.inputdevices",
    "com.android.bluetooth",
    "com.google.android.gms",  # Google Play Services
    "com.google.android.gsf",  # Google Services Framework
    "com.android.vending",  # Google Play Store
]

# Patterns to identify bloatware
BLOATWARE_PATTERNS = [
    "com.facebook.",
    "com.instagram.",
    "com.whatsapp.",
    "com.twitter.",
    "com.snapchat.",
    "com.tiktok.",
    "com.microsoft.",
    "com.linkedin.",
    "com.netflix.",
    "com.spotify.",
    "com.amazon.",
    ".games.",
    ".game.",
    "candy",
    "crush",
]

def is_bloatware(package_name: str) -> bool:
    """Check if a package is likely bloatware"""
    package_lower = package_name.lower()
    
    # Check if in safe to remove list
    if package_name in SAFE_TO_REMOVE:
        return True
    
    # Check patterns
    for pattern in BLOATWARE_PATTERNS:
        if pattern in package_lower:
            # Make sure it's not a critical package
            if package_name not in DO_NOT_REMOVE:
                return True
    
    return False

def is_safe_to_disable(package_name: str) -> bool:
    """Check if a package is safe to disable"""
    return package_name in SAFE_TO_DISABLE

def is_critical(package_name: str) -> bool:
    """Check if a package is critical and should not be touched"""
    return package_name in DO_NOT_REMOVE or \
           any(critical in package_name for critical in [
               "com.android.systemui",
               "com.android.settings",
               "com.android.phone",
               "launcher"
           ])