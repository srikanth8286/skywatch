#!/bin/bash

# SkyWatch Installation Script

echo "🌤️  SkyWatch Installation"
echo "========================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Create storage directory
echo ""
echo "Creating storage directory..."
mkdir -p storage

# Copy config if needed
if [ ! -f config.local.yaml ]; then
    echo ""
    echo "Creating local configuration..."
    cp config.yaml config.local.yaml
    echo "⚠️  Please edit config.local.yaml with your camera settings"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "To start SkyWatch:"
echo "  1. Edit config.local.yaml with your camera RTSP URL"
echo "  2. Run: source venv/bin/activate"
echo "  3. Run: python main.py"
echo "  4. Open browser to: http://localhost:8080"
echo ""
