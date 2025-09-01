"""Configuration settings for large phone farms"""

# Performance settings
PERFORMANCE = {
    # Maximum concurrent connections during startup
    'max_concurrent_connections': 50,
    
    # Always use fast mode (skip UIAutomator2) for initial connection
    'fast_mode_threshold': 0,  # 0 means always use fast mode
    
    # Batch size for different farm sizes
    'batch_sizes': {
        'small': 10,    # <= 10 devices
        'medium': 25,   # 11-50 devices  
        'large': 50,    # 51-100 devices
        'xlarge': 75    # > 100 devices
    },
    
    # Connection timeout in seconds
    'connection_timeout': 5,
    
    # Skip press any key prompts for large farms
    'auto_continue_threshold': 20,
    
    # Cache device connections between sessions
    'cache_connections': True,
    
    # Parallel operation limits
    'max_parallel_operations': {
        'install': 30,
        'configure': 25,
        'bloatware_removal': 20
    }
}

# Display settings  
DISPLAY = {
    # Use compact display for large device counts
    'compact_mode_threshold': 30,
    
    # Show progress bars
    'show_progress': True,
    
    # Update frequency for progress bars (per second)
    'progress_refresh_rate': 10,
    
    # Show device connection speed metrics
    'show_metrics': True
}

# Optimization flags
OPTIMIZATIONS = {
    # Skip device info queries during initial connection
    'skip_device_info': True,
    
    # Use connection pooling
    'use_connection_pool': True,
    
    # Preload common operations
    'preload_operations': False,
    
    # Enable device grouping for batch operations
    'enable_device_groups': True,
    
    # Number of devices per group
    'devices_per_group': 25
}