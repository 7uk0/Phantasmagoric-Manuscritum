#!/bin/bash
# Phantasmagoric Manuscriptum - Dependency Installation Script (Linux)
# This script installs all required Python dependencies for the application

set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  PHANTASMAGORIC MANUSCRIPTUM - Dependency Installer       ║"
echo "║  Linux/macOS Version                                      ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "[!] Error: Python 3 is not installed."
    echo "    Please install Python 3.7 or higher from https://www.python.org/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "[✓] Python $PYTHON_VERSION detected"
echo ""

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "[!] Error: pip3 is not installed."
    echo "    Please install pip by running: sudo apt-get install python3-pip"
    exit 1
fi

PIP_VERSION=$(pip3 --version | cut -d' ' -f2)
echo "[✓] pip $PIP_VERSION detected"
echo ""

echo "Installing dependencies..."
echo ""

# Install required packages
DEPENDENCIES=(
    "pyfiglet"
    "tqdm"
    "rich"
)

for package in "${DEPENDENCIES[@]}"; do
    echo "[→] Installing $package..."
    pip3 install "$package" --break-system-packages || {
        echo "[!] Failed to install $package"
        exit 1
    }
done

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Installation Complete!                                   ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "You can now run the application:"
echo "  python3 Phantasmagoric-Manuscriptum.py "
echo ""
