#!/bin/bash

# Simple script to run VPN setup with hardcoded Google Sheets URL

echo "Starting VPN Setup..."
echo "Using Google Sheets: https://docs.google.com/spreadsheets/d/1Z_1XJC2R0g2_XZeAJk29M-Xt-Ynz_k-T-4jv-8xbFYE/edit"
echo ""

python3 vpn_setup.py "$@"