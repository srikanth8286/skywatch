#!/bin/bash

# SkyWatch startup script

echo "🌤️  Starting SkyWatch..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if config.local.yaml exists
if [ ! -f config.local.yaml ] && [ ! -f config.yaml ]; then
    echo "❌ Configuration file not found!"
    echo "Please create config.yaml or config.local.yaml"
    exit 1
fi

# Start the application
python main.py
