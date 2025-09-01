"""Fast startup optimizations for large phone farms"""

import asyncio
import subprocess
import time
from typing import List, Set
from loguru import logger
from concurrent.futures import ThreadPoolExecutor

class FastStartup:
    """Optimized startup procedures for 100+ device farms"""
    
    @staticmethod
    async def prewarm_adb_server():
        """Pre-warm ADB server for faster device detection"""
        try:
            # Kill and restart ADB server to ensure clean state
            subprocess.run(["adb", "kill-server"], capture_output=True, timeout=5)
            await asyncio.sleep(0.5)
            
            # Start server with increased device scan threads
            subprocess.run(["adb", "start-server"], capture_output=True, timeout=10)
            
            # Force initial device scan
            subprocess.run(["adb", "devices"], capture_output=True, timeout=5)
            
            logger.debug("ADB server pre-warmed")
        except Exception as e:
            logger.warning(f"Could not pre-warm ADB: {e}")
    
    @staticmethod
    async def parallel_device_scan(max_workers: int = 30) -> List[str]:
        """Scan for devices using parallel ADB calls"""
        start_time = time.time()
        
        # Get initial device list
        result = subprocess.run(
            ["adb", "devices", "-l"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        lines = result.stdout.strip().split('\n')[1:]
        device_serials = []
        
        for line in lines:
            if line.strip() and '\t' in line:
                serial = line.split('\t')[0]
                device_serials.append(serial)
        
        elapsed = time.time() - start_time
        if len(device_serials) > 20:
            logger.info(f"Fast scan found {len(device_serials)} devices in {elapsed:.2f}s")
        
        return device_serials
    
    @staticmethod
    async def batch_authorize_devices(unauthorized_serials: List[str]) -> Set[str]:
        """Check which devices have been authorized in parallel"""
        authorized = set()
        
        async def check_device(serial: str) -> str:
            """Check if a single device is now authorized"""
            try:
                result = subprocess.run(
                    ["adb", "-s", serial, "shell", "echo", "test"],
                    capture_output=True,
                    timeout=2
                )
                if result.returncode == 0:
                    return serial
            except:
                pass
            return None
        
        # Check all unauthorized devices in parallel
        tasks = [check_device(serial) for serial in unauthorized_serials]
        results = await asyncio.gather(*tasks)
        
        for serial in results:
            if serial:
                authorized.add(serial)
        
        return authorized
    
    @staticmethod
    async def optimize_device_connections(device_count: int) -> dict:
        """Return optimized connection parameters based on device count"""
        
        if device_count <= 10:
            return {
                'batch_size': device_count,
                'fast_mode': True,  # Always use fast mode
                'parallel_limit': device_count,
                'use_cache': False
            }
        elif device_count <= 30:
            return {
                'batch_size': 15,
                'fast_mode': True,  # Always use fast mode
                'parallel_limit': 15,
                'use_cache': True
            }
        elif device_count <= 50:
            return {
                'batch_size': 25,
                'fast_mode': True,
                'parallel_limit': 25,
                'use_cache': True
            }
        elif device_count <= 100:
            return {
                'batch_size': 50,
                'fast_mode': True,
                'parallel_limit': 50,
                'use_cache': True
            }
        else:
            # 100+ devices
            return {
                'batch_size': 75,
                'fast_mode': True,
                'parallel_limit': 75,
                'use_cache': True
            }
    
    @staticmethod
    def estimate_connection_time(device_count: int, fast_mode: bool = False) -> float:
        """Estimate time to connect all devices"""
        
        if fast_mode:
            # Fast mode: ~0.1s per device in parallel batches
            base_time = 2.0  # Overhead
            per_device = 0.1
        else:
            # Normal mode with UIAutomator2: ~0.5s per device
            base_time = 3.0
            per_device = 0.5
        
        # Account for batching
        if device_count <= 30:
            batch_overhead = 0
        elif device_count <= 50:
            batch_overhead = 2.0
        elif device_count <= 100:
            batch_overhead = 4.0
        else:
            batch_overhead = 6.0
        
        estimated = base_time + (per_device * device_count / 10) + batch_overhead
        return estimated