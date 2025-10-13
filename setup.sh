#!/bin/bash

# YouTube Transcription Tool Setup Script
# This script installs all required dependencies

set -e  # Exit on any error

echo "🚀 Setting up YouTube Transcription Tool..."
echo "=========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7 or higher."
    exit 1
fi

echo "✅ Python 3 is installed"

# Check operating system
OS=$(uname -s)
case "$OS" in
    Darwin)
        echo "📱 Detected macOS"
        ;;
    Linux)
        echo "🐧 Detected Linux"
        ;;
    *)
        echo "⚠️  Unsupported operating system: $OS"
        echo "Please install dependencies manually."
        exit 1
        ;;
esac

# Install yt-dlp
if ! command -v yt-dlp &> /dev/null; then
    echo "📥 Installing yt-dlp..."
    if command -v brew &> /dev/null; then
        brew install yt-dlp
    elif command -v pipx &> /dev/null; then
        pipx install yt-dlp
    else
        pip3 install yt-dlp
    fi
    echo "✅ yt-dlp installed"
else
    echo "✅ yt-dlp is already installed"
fi

# Install uv (for uvx)
if ! command -v uvx &> /dev/null; then
    echo "📥 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "✅ uv installed"
    # Add uv to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
else
    echo "✅ uv is already installed"
fi

# Set up Python virtual environment
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo "📦 Installing Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. (Optional) Set DeepSeek API key:"
echo "   export DEEPSEEK_API_KEY='your-api-key-here'"
echo ""
echo "3. Run the tool:"
echo "   python3 transcribe_yt.py 'https://www.youtube.com/watch?v=VIDEO_ID'"
echo ""
echo "For more options, run:"
echo "   python3 transcribe_yt.py --help"