"""Samsung-specific critical system apps - NEVER REMOVE THESE"""

# These Samsung apps are CRITICAL for boot and system stability
SAMSUNG_CRITICAL_NEVER_REMOVE = [
    # Boot-critical Samsung services
    "com.samsung.android.app.telephonyui",
    "com.samsung.android.bootanimation",
    "com.samsung.android.server.wifi.mobilewips",
    "com.samsung.android.wifi.ai",
    "com.samsung.android.wifi.resources",
    "com.samsung.android.wifi.softap.resources",
    "com.samsung.android.wallpaper.res",
    
    # Samsung UI Framework - CRITICAL
    "com.samsung.android.app.settings.bixby",
    "com.samsung.systemui.bixby2",
    "com.samsung.android.settingsreceiver",
    "com.samsung.android.dynamiclock",
    "com.samsung.android.bluelightfilter",
    
    # Samsung Core Services
    "com.samsung.android.providers.contacts",
    "com.samsung.android.providers.factory",
    "com.samsung.android.providers.media",
    "com.samsung.android.provider.filterprovider",
    "com.samsung.android.providers.trash",
    
    # Samsung Framework
    "com.samsung.android.authfw",
    "com.samsung.android.samsungpass",
    "com.samsung.android.samsungpassautofill",
    "com.samsung.android.container",
    "com.samsung.android.ipsgeofence",
    "com.samsung.android.location",
    "com.samsung.android.samsungpositioning",
    
    # Samsung System Services  
    "com.samsung.android.mdecservice",
    "com.samsung.android.mobileservice",
    "com.samsung.android.mcfserver",
    "com.samsung.android.mcfds",
    "com.samsung.android.networkstack",
    "com.samsung.android.networkdiagnostic",
    "com.samsung.android.connectivity",
    "com.samsung.android.ConnectivityOverlay",
    "com.samsung.android.ConnectivityUxOverlay",
    
    # Samsung Telephony - CRITICAL FOR BOOT
    "com.samsung.android.app.telephonyui",
    "com.samsung.android.app.telephonyui.esimclient",
    "com.samsung.android.app.esimkeystring",
    "com.samsung.android.dialer",
    "com.samsung.android.incallui",
    "com.samsung.android.messaging",
    "com.samsung.android.callbgprovider",
    "com.samsung.android.callassistant",
    "com.samsung.android.incall.contentprovider",
    "com.samsung.android.cidmanager",
    "com.samsung.android.smartcallprovider",
    
    # Samsung Settings - CRITICAL
    "com.samsung.android.settingshelper",
    "com.samsung.android.setting.multisound",
    "com.samsung.android.appseparation",
    "com.samsung.android.app.settings.bixby",
    
    # Samsung Security/Knox - CRITICAL
    "com.samsung.android.knox.analytics.uploader",
    "com.samsung.android.knox.app.networkfilter", 
    "com.samsung.android.knox.attestation",
    "com.samsung.android.knox.containercore",
    "com.samsung.android.knox.er",
    "com.samsung.android.knox.kfbp",
    "com.samsung.android.knox.knnr",
    "com.samsung.android.knox.kpecore",
    "com.samsung.android.knox.pushmanager",
    "com.samsung.android.knox.sandbox",
    "com.samsung.android.knox.zt.framework",
    
    # Samsung Hardware/Radio
    "com.samsung.android.hdmapp",
    "com.samsung.android.app.earphonetypec",
    "com.samsung.android.mtp",
    "com.samsung.android.nfc.resources.usa",
    
    # Samsung Accessibility
    "com.samsung.accessibility",
    "com.samsung.android.accessibility.talkback",
    
    # Samsung Emergency
    "com.samsung.android.emergency",
    "com.sec.android.emergencylauncher",
    
    # Samsung Launcher - CRITICAL
    "com.sec.android.app.launcher",
    
    # Samsung Core Components
    "com.samsung.android.rubin.app",
    "com.samsung.android.scpm",
    "com.samsung.android.scs",
    "com.samsung.android.sdm.config",
    "com.samsung.android.svcagent",
    "com.samsung.android.visual.cloudcore",
    "com.samsung.android.voc",
    "com.samsung.android.wcmurlsnetworkstack",
    
    # Samsung System UI Components
    "com.samsung.android.app.soundpicker",
    "com.samsung.android.secsoundpicker",
    "com.samsung.android.brightnessbackupservice",
    "com.samsung.android.shortcutbackupservice",
    
    # Samsung IMS/RCS Services - CRITICAL FOR CELLULAR
    "com.samsung.ims.smk",
    "com.samsung.ipservice",
    "com.samsung.advp.imssettings",
    "com.samsung.ts43authservice",
    "com.samsung.vvm",
    
    # Samsung System Core
    "com.samsung.android.bbc.bbcagent",
    "com.samsung.android.beaconmanager",
    "com.samsung.android.biometrics.app.setting",
    "com.samsung.android.da.daagent",
    "com.samsung.android.dbsc",
    "com.samsung.android.dqagent",
    "com.samsung.android.dsms",
    "com.samsung.android.fmm",
    "com.samsung.android.gru",
    "com.samsung.android.inputshare",
    "com.samsung.android.intellivoiceservice",
    "com.samsung.android.kgclient",
    "com.samsung.android.kmxservice",
    "com.samsung.android.lool",
    "com.samsung.android.mdm",
    "com.samsung.android.mdx.kit",
    "com.samsung.android.oneconnect",
    "com.samsung.android.privacydashboard",
    "com.samsung.android.privateaccesstokens",
    "com.samsung.android.rampart",
    
    # Samsung Factory/Service Mode
    "com.samsung.android.providers.factory",
    "com.sec.factory.camera",
    "com.sec.facatfunction",
    
    # Samsung Audio
    "com.samsung.android.audiomirroring",
    "com.sec.android.app.soundalive",
    "com.sec.android.app.volumemonitorprovider",
    
    # SEC (Samsung Electronics Corp) Critical
    "com.sec.android.app.SecSetupWizard",
    "com.sec.android.app.setupwizard",
    "com.sec.android.app.setupwizardlegalprovider",
    "com.sec.android.app.factorykeystring",
    "com.sec.android.app.hwmoduletest",
    "com.sec.android.app.parser",
    "com.sec.android.app.personalization",
    "com.sec.android.app.safetyassurance",
    "com.sec.android.app.servicemodeapp",
    "com.sec.android.autodoodle.service",
    "com.sec.android.CcInfo",
    "com.sec.android.Cdfs",
    "com.sec.android.diagmonagent",
    "com.sec.android.easyonehand",
    "com.sec.android.iaft",
    "com.sec.android.provider.badge",
    "com.sec.android.RilServiceModeApp",
    "com.sec.android.sdhms",
    "com.sec.android.smartfpsadjuster",
    "com.sec.android.soagent",
    "com.sec.app.RilErrorNotifier",
    "com.sec.automation",
    "com.sec.bcservice",
    "com.sec.enterprise.knox.cloudmdm.smdms",
    "com.sec.epdg",
    "com.sec.epdgtestapp",
    "com.sec.hiddenmenu",
    "com.sec.imslogger",
    "com.sec.imsservice",
    "com.sec.location.nfwlocationprivacy",
    "com.sec.location.nsflp2",
    "com.sec.mhs.smarttethering",
    "com.sec.modem.settings",
    "com.sec.phone",
    "com.sec.providers.assisteddialing",
    "com.sec.spp.push",
    "com.sec.sve",
    "com.sec.tasmanager",
    "com.sec.unifiedwfc",
    "com.sec.usbsettings",
    "com.sec.vsim.ericssonnsds.webapp",
    
    # Additional Samsung Core
    "com.samsung.aasaservice",
    "com.samsung.android.aircommandmanager",
    "com.samsung.android.allshare.service.mediashare",
    "com.samsung.android.app.clipboardedge",
    "com.samsung.android.app.clockpack",
    "com.samsung.android.app.contacts",
    "com.samsung.android.app.find",
    "com.samsung.android.app.omcagent",
    "com.samsung.android.app.parentalcare",
    "com.samsung.android.app.routines",
    "com.samsung.android.app.sharelive",
    "com.samsung.android.app.smartcapture",
    "com.samsung.android.app.spage",
    "com.samsung.android.app.taskedge",
    "com.samsung.android.app.updatecenter",
    "com.samsung.android.aware.service",
    "com.samsung.android.easysetup",
    "com.samsung.android.fast",
    "com.samsung.android.honeyboard",
    "com.samsung.android.internal.overlay.config.default_contextual_search",
    "com.samsung.android.sdk.handwriting",
    "com.samsung.android.service.peoplestripe",
    "com.samsung.android.service.stplatform",
    "com.samsung.android.service.tagservice",
    "com.samsung.android.smartface",
    "com.samsung.android.smartface.overlay",
    "com.samsung.android.smartmirroring",
    "com.samsung.android.smartswitchassistant",
    "com.samsung.android.spayfw",
    "com.samsung.android.widget.pictureframe",
    
    # Additional critical system components
    "com.samsung.cmh",
    "com.samsung.crane",
    "com.samsung.euicc",
    "com.samsung.faceservice",
    "com.samsung.gpuwatchapp",
    "com.samsung.InputEventApp",
    "com.samsung.internal.systemui.navbar.gestural_no_hint",
    "com.samsung.internal.systemui.navbar.sec_gestural",
    "com.samsung.internal.systemui.navbar.sec_gestural_no_hint",
    "com.samsung.klmsagent",
    "com.samsung.knox.securefolder",
    "com.samsung.oda.service",
    "com.samsung.safetyinformation",
    "com.samsung.sait.sohservice",
    "com.samsung.sdm",
    "com.samsung.sec.android.application.csc",
    "com.samsung.sec.android.teegris.tui_service",
    "com.samsung.slsi.telephony.silentlogging",
    "com.samsung.SMT",
    "com.samsung.SMT.lang_en_us_l03",
    "com.samsung.SMT.lang_es_us_l01",
    "com.samsung.sree",
    "com.samsung.ssu",
    "com.samsung.storyservice",
    "com.samsung.unifiedtp",
    
    # SKMS
    "com.skms.android.agent",
    
    # WSS
    "com.wsomacp",
    "com.wssyncmldm",
    
    # Monotype fonts - Required for UI
    "com.monotype.android.font.foundation",
    "com.monotype.android.font.roboto",
    "com.monotype.android.font.samsungone",
    
    # OSP
    "com.osp.app.signin",
    
    # Hiya (caller ID)
    "com.hiya.star",
    
    # Test apps - May be needed for hardware
    "com.test.LTEfunctionality",
]

def is_samsung_critical(package_name: str) -> bool:
    """Check if a package is critical for Samsung devices"""
    return package_name in SAMSUNG_CRITICAL_NEVER_REMOVE