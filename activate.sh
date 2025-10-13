#!/bin/zsh

# Simple activation script for zsh
# This script activates the Python virtual environment

if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
    echo "Virtual environment activated!"
    echo "Python path: $(which python)"
else
    echo "Error: Virtual environment 'venv' not found."
    echo "Please run './setup.sh' first to create the virtual environment."
    exit 1
fi