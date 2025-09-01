# Performance Optimizations for 100+ Device Farms

## Overview
This document describes the performance optimizations implemented to handle large phone farms with 100+ devices efficiently.

## Key Optimizations

### 1. Fast Mode Connection (20+ devices)
- **What it does**: Skips UIAutomator2 initialization during startup
- **Impact**: Reduces connection time from ~0.5s to ~0.1s per device
- **When activated**: Automatically when device count > 20
- **Trade-off**: UIAutomator2 is initialized on-demand when needed for operations

### 2. Parallel Batch Processing
The system automatically adjusts batch sizes based on device count:
- **1-10 devices**: All at once
- **11-50 devices**: Batches of 25
- **51-100 devices**: Batches of 50  
- **100+ devices**: Batches of 75

### 3. Connection Caching
- Device information is cached between sessions
- Reduces time for device property queries
- Cache stored in `data/device_cache.json`

### 4. ADB Server Pre-warming
- ADB server is pre-warmed before device scanning
- Parallel device scanning for faster detection
- Reduces initial scan time by 30-50%

### 5. Auto-Continue for Large Farms
- Skips "Press any key" prompts when > 20 devices
- Automatic menu progression
- Saves 2-3 seconds per interaction

### 6. Batch ADB Commands
- Execute same command on multiple devices in parallel
- Thread pool executor with configurable workers
- Supports batch installs, launches, and property queries

## Performance Metrics

### Expected Connection Times

| Devices | Normal Mode | Fast Mode | Improvement |
|---------|------------|-----------|-------------|
| 10      | ~5s        | N/A       | -           |
| 30      | ~15s       | ~5s       | 67% faster  |
| 50      | ~25s       | ~8s       | 68% faster  |
| 100     | ~50s       | ~15s      | 70% faster  |

### Throughput
- **Fast Mode**: 5-10 devices/second
- **Normal Mode**: 1-2 devices/second
- **Batch Operations**: Up to 50 devices in parallel

## Configuration

Edit `config/farm_settings.py` to customize:

```python
PERFORMANCE = {
    'max_concurrent_connections': 50,  # Max parallel connections
    'fast_mode_threshold': 20,         # When to use fast mode
    'batch_sizes': {
        'small': 10,
        'medium': 25,  
        'large': 50,
        'xlarge': 75
    }
}
```

## Usage Tips

### For 100 Device Farms

1. **Initial Setup**
   ```bash
   python main.py run
   ```
   - The system will automatically detect 100 devices
   - Fast mode will be activated
   - Connection will complete in ~15-20 seconds

2. **Batch Operations**
   - When installing apps, select all devices
   - The system will process in optimized batches
   - Progress bars show real-time status

3. **Network Operations**
   - Proxy configuration is batched
   - Network status checks run in parallel
   - Expected time: <30s for 100 devices

### Monitoring Performance

The system displays performance metrics:
- Connection rate (devices/sec)
- Average time per device
- Batch processing speed

### Troubleshooting

If connections are slow:
1. Check USB hub power (100 devices need powered hubs)
2. Ensure ADB server isn't overloaded: `adb kill-server && adb start-server`
3. Check system resources (CPU, RAM)
4. Consider increasing batch sizes in config

## Hardware Recommendations

For 100+ device farms:
- **CPU**: 8+ cores recommended
- **RAM**: 16GB minimum, 32GB recommended
- **USB**: Powered USB 3.0 hubs (10A+ per 10 devices)
- **Network**: Gigabit ethernet for device network operations

## Advanced Features

### Custom Batch Sizes
Override automatic batch sizing:
```python
await device_manager.connect_all_devices(batch_size=100)
```

### Selective Fast Mode
Force fast mode even for small device counts:
```python
await device_manager.connect_all_devices(fast_mode=True)
```

### Parallel Command Execution
Use BatchADB for custom commands:
```python
batch_adb = BatchADB(max_workers=50)
results = await batch_adb.run_command_batch(
    devices=['device1', 'device2', ...],
    command=['shell', 'getprop', 'ro.build.version.release']
)