#!/usr/bin/env python3
"""Non-interactive allowlist cleanup - Automatically removes all non-essential apps"""

import subprocess
import sys
import time

# ESSENTIAL APPS ONLY - Minimal set for a working phone
ESSENTIAL_ALLOWLIST = [
    # Core Android System - NEVER REMOVE
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
    "com.android.packageinstaller",
    "com.android.permissioncontroller",
    "com.android.keychain",
    "com.android.certinstaller",
    "com.android.carrierconfig",
    "com.android.localtransport",
    "com.android.location.fused",
    "com.android.inputdevices",
    "com.android.bluetooth",
    "com.android.shell",
    "com.android.mms.service",
    "com.android.mtp",
    "com.android.externalstorage",
    "com.android.storagemanager",
    "com.android.cellbroadcastservice",
    "com.android.cellbroadcastreceiver",
    "com.android.intentresolver",
    "com.android.backupconfirm",
    
    # Google Play Services - Required for most functionality
    "com.google.android.gms",
    "com.google.android.gsf",
    "com.android.vending",  # Play Store
    "com.google.android.webview",
    "com.google.android.packageinstaller",
    "com.google.android.permissioncontroller",
    "com.google.android.ext.services",
    "com.google.android.ext.shared",
    "com.google.android.networkstack",
    "com.google.android.networkstack.tethering",
    
    # Samsung Core (for Samsung devices)
    "com.samsung.android.providers.contacts",
    "com.samsung.android.providers.media",
    "com.samsung.android.incallui",
    "com.samsung.android.dialer",
    "com.sec.android.app.launcher",
    "com.samsung.android.messaging",
    "com.samsung.android.emergency",
    "com.samsung.android.mobileservice",
    "com.samsung.android.authfw",
    
    # Browser (keep one)
    "com.android.chrome",
]

def run_command(cmd):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def get_device_packages():
    """Get all installed packages on the device"""
    success, stdout, stderr = run_command("adb shell pm list packages")
    if success:
        packages = []
        for line in stdout.strip().split('\n'):
            if line.startswith('package:'):
                packages.append(line.replace('package:', '').strip())
        return packages
    return []

def uninstall_package(package):
    """Attempt to uninstall a package"""
    # Try uninstall for user 0
    success, stdout, stderr = run_command(f"adb shell pm uninstall --user 0 {package}")
    if success or "Success" in stdout:
        return True, "uninstalled"
    
    # Try to disable
    success, stdout, stderr = run_command(f"adb shell pm disable-user --user 0 {package}")
    if success or "disabled" in stdout.lower():
        return True, "disabled"
    
    return False, "failed"

def is_system_critical(package):
    """Check if package is absolutely critical"""
    critical_prefixes = [
        "android.auto_generated",
        "com.android.cts",
        "com.android.internal",
        "com.android.overlay",
        "com.samsung.internal",
        "com.google.android.overlay",
        "com.sec.factory",
        "com.sec.imsservice",
        "com.samsung.ipservice",
    ]
    
    for prefix in critical_prefixes:
        if package.startswith(prefix):
            return True
    return False

def main():
    print("=" * 70)
    print("AGGRESSIVE DEVICE CLEANUP - ALLOWLIST MODE")
    print("=" * 70)
    print("\n⚠️  This will remove ALL apps except essential system apps!")
    
    # Check device connection
    success, stdout, stderr = run_command("adb devices")
    if not success or "device" not in stdout:
        print("\n❌ No device connected.")
        sys.exit(1)
    
    print("\n✅ Device connected. Analyzing packages...")
    
    # Get installed packages
    packages = get_device_packages()
    if not packages:
        print("❌ Could not get packages")
        sys.exit(1)
    
    print(f"📦 Found {len(packages)} total packages")
    
    # Determine what to remove
    to_remove = []
    to_keep = []
    
    for package in packages:
        if package in ESSENTIAL_ALLOWLIST or is_system_critical(package):
            to_keep.append(package)
        else:
            to_remove.append(package)
    
    print(f"\n📊 Analysis complete:")
    print(f"  • Will KEEP: {len(to_keep)} essential packages")
    print(f"  • Will REMOVE: {len(to_remove)} packages")
    
    # Show categories of what will be removed
    games = [p for p in to_remove if any(g in p.lower() for g in ["game", "solitaire", "puzzle", "monopoly", "candy"])]
    social = [p for p in to_remove if any(s in p.lower() for s in ["facebook", "instagram", "twitter", "tiktok"])]
    samsung = [p for p in to_remove if "samsung" in p.lower()]
    google = [p for p in to_remove if "google" in p.lower()]
    att = [p for p in to_remove if "att" in p.lower()]
    
    if games:
        print(f"\n🎮 Games to remove: {len(games)}")
        for g in games[:5]:
            print(f"   • {g}")
        if len(games) > 5:
            print(f"   ... and {len(games)-5} more")
    
    if social:
        print(f"\n💬 Social media to remove: {len(social)}")
        for s in social:
            print(f"   • {s}")
    
    if samsung:
        print(f"\n📱 Samsung apps to remove: {len(samsung)}")
    
    if google:
        print(f"\n🔍 Google apps to remove: {len(google)}")
    
    if att:
        print(f"\n📡 AT&T apps to remove: {len(att)}")
    
    # Countdown before starting
    print("\n" + "=" * 70)
    print("Starting removal in 5 seconds... Press Ctrl+C to cancel")
    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)
    
    # Remove packages
    print("\n" + "=" * 70)
    print("REMOVING PACKAGES...")
    print("=" * 70)
    
    success_count = 0
    failed_count = 0
    
    for i, package in enumerate(to_remove, 1):
        # Show progress every 10 packages
        if i % 10 == 0:
            print(f"\nProgress: {i}/{len(to_remove)} ({i*100//len(to_remove)}%)")
        
        success, status = uninstall_package(package)
        if success:
            success_count += 1
            # Only show important removals
            if any(x in package.lower() for x in ["game", "facebook", "instagram", "cash", "monopoly"]):
                print(f"  ✅ Removed: {package}")
        else:
            failed_count += 1
        
        time.sleep(0.05)  # Small delay
    
    # Summary
    print("\n" + "=" * 70)
    print("CLEANUP COMPLETE!")
    print("=" * 70)
    print(f"✅ Successfully removed: {success_count} packages")
    print(f"⚠️  Could not remove: {failed_count} packages (likely system-protected)")
    
    # Final check for games
    print("\n🔍 Final verification...")
    remaining = get_device_packages()
    remaining_games = [p for p in remaining if any(g in p.lower() for g in ["game", "solitaire", "monopoly", "candy"])]
    
    if remaining_games:
        print(f"\n⚠️  Still found {len(remaining_games)} gaming apps:")
        for game in remaining_games:
            print(f"  • {game}")
    else:
        print("\n✅ All gaming apps removed!")
    
    print(f"\n📦 Final package count: {len(remaining)} (was {len(packages)})")
    print("✅ Device cleanup complete!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)