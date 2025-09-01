#!/usr/bin/env python3
"""Allowlist-based cleanup - Remove everything NOT on the allowlist"""

import subprocess
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.allowlist import get_full_allowlist, should_remove

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
                packages.append(line.replace('package:', '').strip())
        return packages
    else:
        print(f"Error getting packages: {stderr}")
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
    
    # Try to hide
    success, stdout, stderr = run_command(f"adb shell pm hide {package}")
    if success or "hidden" in stdout.lower():
        return True, "hidden"
    
    return False, stderr if stderr else "failed"

def categorize_packages(packages, allowlist):
    """Categorize packages into keep and remove lists"""
    to_keep = []
    to_remove = []
    
    for package in packages:
        if should_remove(package, allowlist):
            to_remove.append(package)
        else:
            to_keep.append(package)
    
    return to_keep, to_remove

def main():
    print("=" * 70)
    print("ALLOWLIST-BASED CLEANUP SCRIPT")
    print("=" * 70)
    print("\nThis script will remove ALL apps NOT on the allowlist.")
    print("Only essential system apps and specified apps will remain.")
    
    # Check if device is connected
    success, stdout, stderr = run_command("adb devices")
    if not success or "device" not in stdout:
        print("\n❌ No device connected. Please connect a device first.")
        sys.exit(1)
    
    print("\n✅ Device connected. Analyzing installed packages...")
    
    # Get all installed packages
    installed_packages = get_device_packages()
    if not installed_packages:
        print("❌ Could not get installed packages")
        sys.exit(1)
    
    print(f"📦 Found {len(installed_packages)} total installed packages")
    
    # Get allowlist
    include_optional = input("\nInclude optional apps (Gmail, Maps, etc.)? (yes/no): ").strip().lower() in ['yes', 'y']
    allowlist = get_full_allowlist(include_optional=include_optional, include_phone_farm=True)
    
    # Categorize packages
    to_keep, to_remove = categorize_packages(installed_packages, allowlist)
    
    print(f"\n📊 Package Analysis:")
    print(f"  • Packages to KEEP: {len(to_keep)}")
    print(f"  • Packages to REMOVE: {len(to_remove)}")
    
    # Show what will be removed (categorized)
    if to_remove:
        print("\n" + "=" * 70)
        print("PACKAGES TO BE REMOVED:")
        print("=" * 70)
        
        # Categorize for better visibility
        games = []
        social = []
        samsung_bloat = []
        google_bloat = []
        carrier = []
        other = []
        
        for pkg in to_remove:
            pkg_lower = pkg.lower()
            if any(g in pkg_lower for g in ["game", "solitaire", "puzzle", "candy", "monopoly"]):
                games.append(pkg)
            elif any(s in pkg_lower for s in ["facebook", "instagram", "twitter", "tiktok", "whatsapp"]):
                social.append(pkg)
            elif "samsung" in pkg_lower and not any(e in pkg_lower for e in ["provider", "core", "system"]):
                samsung_bloat.append(pkg)
            elif "google" in pkg_lower and pkg not in allowlist:
                google_bloat.append(pkg)
            elif any(c in pkg_lower for c in ["att", "verizon", "tmobile", "sprint"]):
                carrier.append(pkg)
            else:
                other.append(pkg)
        
        if games:
            print(f"\n🎮 Games ({len(games)}):")
            for pkg in sorted(games):
                print(f"  • {pkg}")
        
        if social:
            print(f"\n💬 Social Media ({len(social)}):")
            for pkg in sorted(social):
                print(f"  • {pkg}")
        
        if samsung_bloat:
            print(f"\n📱 Samsung Bloatware ({len(samsung_bloat)}):")
            for pkg in sorted(samsung_bloat)[:10]:  # Show first 10
                print(f"  • {pkg}")
            if len(samsung_bloat) > 10:
                print(f"  ... and {len(samsung_bloat) - 10} more")
        
        if google_bloat:
            print(f"\n🔍 Google Apps ({len(google_bloat)}):")
            for pkg in sorted(google_bloat)[:10]:  # Show first 10
                print(f"  • {pkg}")
            if len(google_bloat) > 10:
                print(f"  ... and {len(google_bloat) - 10} more")
        
        if carrier:
            print(f"\n📡 Carrier Apps ({len(carrier)}):")
            for pkg in sorted(carrier):
                print(f"  • {pkg}")
        
        if other:
            print(f"\n📦 Other Apps ({len(other)}):")
            for pkg in sorted(other)[:10]:  # Show first 10
                print(f"  • {pkg}")
            if len(other) > 10:
                print(f"  ... and {len(other) - 10} more")
    
    # Safety check
    print("\n" + "=" * 70)
    print("⚠️  WARNING: This will remove ALL apps not on the allowlist!")
    print("⚠️  This action cannot be easily undone!")
    print("=" * 70)
    
    response = input("\nProceed with removal? Type 'YES' to confirm: ").strip()
    if response != 'YES':
        print("❌ Aborted. No changes made.")
        return
    
    # Remove packages
    print("\n" + "=" * 70)
    print("REMOVING PACKAGES...")
    print("=" * 70)
    
    success_count = 0
    failed_count = 0
    failed_packages = []
    
    total = len(to_remove)
    for i, package in enumerate(to_remove, 1):
        print(f"\n[{i}/{total}] Processing: {package}")
        success, status = uninstall_package(package)
        if success:
            print(f"  ✅ {status}: {package}")
            success_count += 1
        else:
            print(f"  ❌ Failed: {package}")
            failed_count += 1
            failed_packages.append((package, status))
        
        # Progress indicator
        if i % 10 == 0:
            print(f"\n  Progress: {i}/{total} ({i*100//total}%)")
        
        time.sleep(0.1)  # Small delay to prevent overwhelming the system
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✅ Successfully removed: {success_count} packages")
    print(f"❌ Failed to remove: {failed_count} packages")
    
    if failed_packages:
        print("\n❌ Failed packages (may be system-protected):")
        for pkg, error in failed_packages[:20]:  # Show first 20
            print(f"  • {pkg}")
        if len(failed_packages) > 20:
            print(f"  ... and {len(failed_packages) - 20} more")
    
    # Final verification
    print("\n" + "=" * 70)
    print("FINAL VERIFICATION")
    print("=" * 70)
    print("Checking remaining packages...")
    
    remaining = get_device_packages()
    print(f"\n📦 Total packages remaining: {len(remaining)}")
    
    # Check for any games/bloatware that might still be there
    remaining_unwanted = []
    unwanted_keywords = ["game", "solitaire", "candy", "facebook", "instagram", "tiktok"]
    for pkg in remaining:
        if any(keyword in pkg.lower() for keyword in unwanted_keywords):
            if pkg not in allowlist:
                remaining_unwanted.append(pkg)
    
    if remaining_unwanted:
        print(f"\n⚠️  Found {len(remaining_unwanted)} potential unwanted apps still installed:")
        for pkg in remaining_unwanted:
            print(f"  • {pkg}")
    else:
        print("\n✅ Device cleaned successfully! Only allowlisted apps remain.")
    
    print("\n" + "=" * 70)
    print("✅ Cleanup complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()