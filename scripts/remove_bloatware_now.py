#!/usr/bin/env python3
"""Enhanced bloatware removal script with comprehensive detection and removal"""

import subprocess
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.bloatware import SAFE_TO_REMOVE, SAFE_TO_DISABLE, DO_NOT_REMOVE
from core.utils import run_adb_command

def get_device_packages():
    """Get all installed packages on the device"""
    try:
        result = run_adb_command(["shell", "pm", "list", "packages"])
        if result.returncode == 0:
            packages = []
            for line in result.stdout.strip().split('\n'):
                if line.startswith('package:'):
                    packages.append(line.replace('package:', ''))
            return packages
        else:
            print(f"Error getting packages: {result.stderr}")
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []

def uninstall_package(package, user=0):
    """Attempt to uninstall a package for a specific user"""
    try:
        # Try uninstall for user
        result = run_adb_command(["shell", "pm", "uninstall", "--user", str(user), package])
        if result.returncode == 0:
            return True, "uninstalled"
        
        # If uninstall fails, try to disable
        result = run_adb_command(["shell", "pm", "disable-user", "--user", str(user), package])
        if result.returncode == 0:
            return True, "disabled"
        
        # Last resort - hide the package
        result = run_adb_command(["shell", "pm", "hide", package])
        if result.returncode == 0:
            return True, "hidden"
        
        return False, "failed"
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 60)
    print("ENHANCED BLOATWARE REMOVAL SCRIPT")
    print("=" * 60)
    
    # Check if device is connected
    result = run_adb_command(["devices"])
    if "device" not in result.stdout:
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
    bloatware_to_remove = []
    bloatware_to_disable = []
    
    for package in installed_packages:
        if package in DO_NOT_REMOVE:
            continue
        elif package in SAFE_TO_REMOVE:
            bloatware_to_remove.append(package)
        elif package in SAFE_TO_DISABLE:
            bloatware_to_disable.append(package)
    
    print(f"\nIdentified bloatware:")
    print(f"  • {len(bloatware_to_remove)} packages to remove")
    print(f"  • {len(bloatware_to_disable)} packages to disable")
    
    if not bloatware_to_remove and not bloatware_to_disable:
        print("\n✅ No bloatware found on this device!")
        return
    
    # Show what will be removed
    print("\n" + "=" * 60)
    print("PACKAGES TO REMOVE/DISABLE:")
    print("=" * 60)
    
    if bloatware_to_remove:
        print("\n📦 Will attempt to REMOVE:")
        for i, pkg in enumerate(bloatware_to_remove, 1):
            print(f"  {i:2}. {pkg}")
    
    if bloatware_to_disable:
        print("\n📦 Will attempt to DISABLE:")
        for i, pkg in enumerate(bloatware_to_disable, 1):
            print(f"  {i:2}. {pkg}")
    
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
    results = []
    
    # Process removals
    for package in bloatware_to_remove:
        print(f"\nRemoving: {package}")
        success, status = uninstall_package(package)
        if success:
            print(f"  ✅ Successfully {status}: {package}")
            success_count += 1
            results.append((package, status, True))
        else:
            print(f"  ❌ Failed to remove: {package} ({status})")
            failed_count += 1
            results.append((package, status, False))
        time.sleep(0.1)  # Small delay between operations
    
    # Process disables
    for package in bloatware_to_disable:
        print(f"\nDisabling: {package}")
        success, status = uninstall_package(package)
        if success:
            print(f"  ✅ Successfully {status}: {package}")
            success_count += 1
            results.append((package, status, True))
        else:
            print(f"  ❌ Failed to disable: {package} ({status})")
            failed_count += 1
            results.append((package, status, False))
        time.sleep(0.1)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✅ Successfully processed: {success_count} packages")
    print(f"❌ Failed: {failed_count} packages")
    
    # Show detailed results
    if failed_count > 0:
        print("\nFailed packages:")
        for pkg, status, success in results:
            if not success:
                print(f"  • {pkg}: {status}")
    
    print("\n✅ Bloatware removal completed!")
    
    # Verify remaining packages
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    print("Checking for remaining gaming/bloatware apps...")
    
    remaining_packages = get_device_packages()
    gaming_patterns = ["game", "solitaire", "puzzle", "candy", "crush", "monopoly", "woodoku", "mahjong", "juggle", "pixel.art"]
    
    remaining_games = []
    for package in remaining_packages:
        package_lower = package.lower()
        for pattern in gaming_patterns:
            if pattern in package_lower and package not in DO_NOT_REMOVE:
                remaining_games.append(package)
                break
    
    if remaining_games:
        print(f"\n⚠️  Found {len(remaining_games)} gaming apps still installed:")
        for game in remaining_games:
            print(f"  • {game}")
        print("\nThese may require manual removal or different methods.")
    else:
        print("✅ No gaming apps detected!")
    
    print("\n" + "=" * 60)
    print("Script completed!")

if __name__ == "__main__":
    main()