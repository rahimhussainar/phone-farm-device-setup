#!/usr/bin/env python3
"""Test script to verify parallel device connection performance"""

import asyncio
import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.device_manager import DeviceManager
from loguru import logger

async def test_parallel_connections():
    """Test parallel connection to multiple devices"""
    print("\n" + "="*60)
    print("PARALLEL DEVICE CONNECTION TEST")
    print("="*60 + "\n")
    
    device_manager = DeviceManager()
    
    # Scan for devices
    print("Scanning for devices...")
    devices = await device_manager.scan_devices()
    
    if not devices:
        print("❌ No devices found. Please connect devices via USB.")
        return
    
    # Show device summary
    total = len(devices)
    authorized = len([d for d in devices if d.status == "device"])
    unauthorized = len([d for d in devices if d.status == "unauthorized"])
    connected = len([d for d in devices if d.status == "connected"])
    
    print(f"\n📱 Found {total} device(s):")
    print(f"  • Authorized (ready to connect): {authorized}")
    print(f"  • Unauthorized (need approval): {unauthorized}")
    print(f"  • Already connected: {connected}")
    
    if authorized == 0:
        print("\n⚠️  No authorized devices to connect.")
        print("Please authorize USB debugging on your device(s).")
        return
    
    # Connect to all authorized devices
    print(f"\n🚀 Connecting to {authorized} device(s) in parallel...")
    print("   (All connections will happen simultaneously)\n")
    
    start_time = time.time()
    
    # Progress callback to show live updates
    async def progress_callback(connected_count, total_count):
        print(f"   Progress: {connected_count}/{total_count} devices connected")
    
    # Connect with progress updates
    connected_count = await device_manager.connect_all_devices(progress_callback)
    
    elapsed_time = time.time() - start_time
    
    # Show results
    print(f"\n✅ Connection complete!")
    print(f"   • Connected: {connected_count}/{authorized} devices")
    print(f"   • Total time: {elapsed_time:.1f} seconds")
    
    if authorized > 1:
        avg_time = elapsed_time / authorized
        print(f"   • Average per device: {avg_time:.2f} seconds")
        
        # Compare to sequential time estimate
        sequential_estimate = avg_time * authorized
        time_saved = sequential_estimate - elapsed_time
        speedup = sequential_estimate / elapsed_time if elapsed_time > 0 else 1
        
        print(f"\n📊 Performance Analysis:")
        print(f"   • Sequential estimate: {sequential_estimate:.1f} seconds")
        print(f"   • Time saved: {time_saved:.1f} seconds")
        print(f"   • Speedup: {speedup:.1f}x faster")
    
    # List connected devices
    connected_devices = device_manager.get_connected_devices()
    if connected_devices:
        print(f"\n📋 Connected Devices:")
        for device in connected_devices:
            print(f"   • {device.serial} ({device.model}) - Android {device.android_version}")

if __name__ == "__main__":
    # Configure minimal logging
    logger.remove()
    logger.add(sys.stderr, level="ERROR")
    
    try:
        asyncio.run(test_parallel_connections())
    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
    
    print("\n" + "="*60 + "\n")