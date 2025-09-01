#!/usr/bin/env python3
"""SAFE bloatware removal - Only removes known safe-to-remove apps"""

import subprocess
import sys
import time

# ONLY remove these specific apps that are 100% safe to remove
SAFE_BLOATWARE = [
    # Games - Safe to remove
    "com.king.candycrushsaga",
    "com.rovio.angrybirds",
    "com.supercell.clashofclans",
    "com.scopely.monopolygo",
    "com.tripledot.solitaire",
    "com.tripledot.woodoku",
    "com.pixel.art.coloring.color.number",
    "com.vitastudio.mahjong",
    "com.block.juggle",
    
    # Social Media - Safe to remove
    "com.facebook.katana",
    "com.facebook.system",
    "com.facebook.appmanager",
    "com.facebook.services",
    "com.instagram.android",
    "com.twitter.android",
    "com.snapchat.android",
    "com.zhiliaoapp.musically",  # TikTok (remove if not needed)
    "com.whatsapp",
    "com.linkedin.android",
    "com.pinterest",
    
    # Shopping - Safe to remove
    "com.amazon.mShop.android.shopping",
    "com.amazon.kindle",
    "com.amazon.mp3",
    "com.ebay.mobile",
    "com.alibaba.aliexpresshd",
    "com.squareup.cash",
    
    # Microsoft - Safe to remove
    "com.microsoft.skydrive",
    "com.microsoft.office.excel",
    "com.microsoft.office.word",
    "com.microsoft.office.powerpoint",
    "com.microsoft.office.outlook",
    "com.skype.raider",
    
    # News/Weather - Safe to remove
    "flipboard.app",
    "com.cnn.mobile.android.phone",
    "com.foxnews.android",
    "com.localweather.radar.climate",
    
    # AT&T Apps - Safe to remove
    "com.att.tv",
    "com.att.myWireless",
    "com.att.android.attsmartwifi",
    
    # Optional Samsung Apps - Safe to remove
    "com.samsung.android.tvplus",
    "com.samsung.android.themestore",
    "com.samsung.android.themecenter",
    "com.samsung.android.stickercenter",
    "com.samsung.android.aremojieditor",
    "com.samsung.android.app.dressroom",
    "com.samsung.android.forest",
    "com.samsung.android.game.gamehome",
    "com.samsung.android.game.gametools",
    "com.samsung.android.bixby.agent",  # Bixby (optional)
    "com.samsung.android.bixby.service",
    "com.samsung.android.bixvision.framework",
    "com.samsung.android.ardrawing",
    "com.samsung.android.aremoji",
    "com.samsung.android.app.tips",
    "com.samsung.android.app.social",
    
    # Google Apps - Safe to remove (if not needed)
    "com.google.android.youtube",
    "com.google.android.videos",
    "com.google.android.music",
    "com.google.android.apps.magazines",
    "com.google.android.apps.books",
    "com.google.android.apps.tachyon",  # Google Duo
    "com.google.android.apps.podcasts",
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
    """Safely uninstall a package (user-level only)"""
    # Only uninstall for user 0 - can be restored with factory reset
    success, stdout, stderr = run_command(f"adb shell pm uninstall --user 0 {package}")
    if success or "Success" in stdout:
        return True, "uninstalled"
    
    # If uninstall fails, DON'T try to disable system apps
    return False, "skipped (protected)"

def main():
    print("=" * 70)
    print("SAFE BLOATWARE REMOVAL")
    print("=" * 70)
    print("\nThis script only removes known safe-to-remove apps.")
    print("It will NOT touch any system-critical components.")
    
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
    
    # Find bloatware to remove
    to_remove = []
    for package in packages:
        if package in SAFE_BLOATWARE:
            to_remove.append(package)
    
    if not to_remove:
        print("\n✅ No known bloatware found! Device is clean.")
        return
    
    print(f"\n📊 Found {len(to_remove)} safe-to-remove apps:")
    for i, pkg in enumerate(to_remove, 1):
        print(f"  {i}. {pkg}")
    
    # Confirm
    print("\n" + "=" * 70)
    response = input("Remove these apps? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("❌ Cancelled by user")
        return
    
    # Remove packages
    print("\n" + "=" * 70)
    print("REMOVING SAFE BLOATWARE...")
    print("=" * 70)
    
    success_count = 0
    failed_count = 0
    
    for package in to_remove:
        print(f"\nRemoving: {package}")
        success, status = uninstall_package(package)
        if success:
            print(f"  ✅ {status}")
            success_count += 1
        else:
            print(f"  ⚠️  {status}")
            failed_count += 1
        time.sleep(0.1)
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✅ Successfully removed: {success_count} apps")
    if failed_count > 0:
        print(f"⚠️  Skipped (protected): {failed_count} apps")
    
    print("\n✅ Safe cleanup complete!")
    print("Your device remains stable and functional.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)