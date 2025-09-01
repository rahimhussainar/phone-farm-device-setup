#!/usr/bin/env python3
"""Standalone bloatware removal script - no dependencies"""

import subprocess
import sys
import time

# Comprehensive bloatware list
SAFE_TO_REMOVE = [
    # Facebook
    "com.facebook.katana",
    "com.facebook.system",
    "com.facebook.appmanager",
    "com.facebook.services",
    "com.instagram.android",
    
    # Games - comprehensive list
    "com.king.candycrushsaga",
    "com.rovio.angrybirds",
    "com.supercell.clashofclans",
    "com.scopely.monopolygo",
    "com.tripledot.solitaire",
    "com.tripledot.woodoku",
    "com.pixel.art.coloring.color.number",
    "com.vitastudio.mahjong",
    "com.block.juggle",
    
    # Microsoft
    "com.microsoft.skydrive",
    "com.microsoft.office.excel",
    "com.microsoft.office.word",
    "com.microsoft.office.powerpoint",
    "com.microsoft.office.outlook",
    "com.skype.raider",
    
    # Shopping/Services
    "com.amazon.mShop.android.shopping",
    "com.amazon.kindle",
    "com.amazon.mp3",
    "com.ebay.mobile",
    "com.squareup.cash",
    
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
    
    # Samsung Bloatware
    "com.samsung.android.tvplus",
    "com.samsung.android.themestore",
    "com.samsung.android.themecenter",
    "com.samsung.android.stickercenter",
    "com.samsung.android.aremojieditor",
    "com.samsung.android.app.dressroom",
    "com.samsung.android.forest",
    "com.samsung.android.game.gamehome",
    "com.samsung.android.game.gametools",
    "com.samsung.android.game.gos",
]

def run_command(cmd):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def get_device_packages():
    """Get all installed packages on the device"""
    success, stdout, stderr = run_command("adb shell pm list packages")
    if success:
        packages = []
        for line in stdout.strip().split('\n'):
            if line.startswith('package:'):
                packages.append(line.replace('package:', ''))
        return packages
    else:
        print(f"Error getting packages: {stderr}")
        return []

def uninstall_package(package):
    """Attempt to uninstall a package"""
    # Try uninstall for user 0
    success, stdout, stderr = run_command(f"adb shell pm uninstall --user 0 {package}")
    if success:
        return True, "uninstalled"
    
    # Try to disable
    success, stdout, stderr = run_command(f"adb shell pm disable-user --user 0 {package}")
    if success:
        return True, "disabled"
    
    # Try to hide
    success, stdout, stderr = run_command(f"adb shell pm hide {package}")
    if success:
        return True, "hidden"
    
    return False, "failed"

def main():
    print("=" * 60)
    print("STANDALONE BLOATWARE REMOVAL SCRIPT")
    print("=" * 60)
    
    # Check if device is connected
    success, stdout, stderr = run_command("adb devices")
    if not success or "device" not in stdout:
        print("❌ No device connected. Please connect a device first.")
        sys.exit(1)
    
    print("✅ Device connected. Getting installed packages...")
    
    # Get all installed packages
    installed_packages = get_device_packages()
    if not installed_packages:
        print("❌ Could not get installed packages")
        sys.exit(1)
    
    print(f"Found {len(installed_packages)} installed packages")
    
    # Identify bloatware
    bloatware_found = []
    for package in installed_packages:
        if package in SAFE_TO_REMOVE:
            bloatware_found.append(package)
    
    print(f"\n📦 Found {len(bloatware_found)} bloatware packages to remove:")
    for i, pkg in enumerate(bloatware_found, 1):
        print(f"  {i:2}. {pkg}")
    
    if not bloatware_found:
        print("\n✅ No known bloatware found on this device!")
        return
    
    # Confirm before proceeding
    print("\n" + "=" * 60)
    response = input("Proceed with removal? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("❌ Aborted by user")
        return
    
    # Remove bloatware
    print("\n" + "=" * 60)
    print("REMOVING BLOATWARE...")
    print("=" * 60)
    
    success_count = 0
    failed_count = 0
    
    for package in bloatware_found:
        print(f"\nProcessing: {package}")
        success, status = uninstall_package(package)
        if success:
            print(f"  ✅ Successfully {status}: {package}")
            success_count += 1
        else:
            print(f"  ❌ Failed to remove: {package}")
            failed_count += 1
        time.sleep(0.2)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✅ Successfully processed: {success_count} packages")
    print(f"❌ Failed: {failed_count} packages")
    
    # Check for remaining gaming apps
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    print("Checking for remaining gaming apps...")
    
    remaining_packages = get_device_packages()
    gaming_keywords = ["game", "solitaire", "puzzle", "candy", "crush", 
                      "monopoly", "woodoku", "mahjong", "juggle", "pixel.art",
                      "tetris", "casino", "slots", "poker"]
    
    remaining_games = []
    for package in remaining_packages:
        package_lower = package.lower()
        for keyword in gaming_keywords:
            if keyword in package_lower:
                # Skip system packages
                if not any(sys_pkg in package for sys_pkg in ["com.android.systemui", "com.android.settings", "com.google.android.gms"]):
                    remaining_games.append(package)
                    break
    
    if remaining_games:
        print(f"\n⚠️  Found {len(remaining_games)} potential gaming apps still installed:")
        for game in remaining_games:
            print(f"  • {game}")
    else:
        print("✅ No gaming apps detected!")
    
    print("\n" + "=" * 60)
    print("✅ Script completed!")

if __name__ == "__main__":
    main()