#!/bin/bash
# Quick activation script
source venv/bin/activate
echo "✅ Virtual environment activated!"
echo "You can now run:"
echo "  python test_devices.py"
echo "  python batch_setup.py"
echo "  python main.py run"
exec $SHELL