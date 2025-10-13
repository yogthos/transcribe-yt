#!/bin/bash

# Example usage script for YouTube Transcription Tool
# This shows how to use the tool with different options

echo "🎬 YouTube Transcription Tool - Usage Examples"
echo "============================================"
echo ""

# Make sure virtual environment is activated
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

source venv/bin/activate

echo "📋 Available commands:"
echo ""
echo "1. Show help:"
echo "   python3 transcribe_yt.py --help"
echo ""

echo "2. Basic usage with DeepSeek (requires DEEPSEEK_API_KEY):"
echo "   python3 transcribe_yt.py 'https://www.youtube.com/watch?v=VIDEO_ID'"
echo ""

echo "3. Using local Ollama model:"
echo "   python3 transcribe_yt.py --model ollama 'https://www.youtube.com/watch?v=VIDEO_ID'"
echo ""

echo "4. Custom output directory:"
echo "   python3 transcribe_yt.py --output-dir ./transcriptions 'https://www.youtube.com/watch?v=VIDEO_ID'"
echo ""

echo "5. Specific Ollama model:"
echo "   python3 transcribe_yt.py --model ollama --ollama-model 'llama3.1:8b' 'https://www.youtube.com/watch?v=VIDEO_ID'"
echo ""

echo "🔧 Testing:"
echo "   python3 test_basic.py"
echo ""

echo "💡 Replace VIDEO_ID with an actual YouTube video ID"
echo ""

# Show current setup status
echo "🔍 Current setup status:"
if command -v yt-dlp &> /dev/null; then
    echo "   ✅ yt-dlp: installed"
else
    echo "   ❌ yt-dlp: not found"
fi

if command -v uvx &> /dev/null; then
    echo "   ✅ uvx: installed"
else
    echo "   ❌ uvx: not found"
fi

if [ -n "$DEEPSEEK_API_KEY" ]; then
    echo "   ✅ DEEPSEEK_API_KEY: set"
else
    echo "   ❌ DEEPSEEK_API_KEY: not set"
fi

# Check if Ollama is running
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "   ✅ Ollama: running"
else
    echo "   ❌ Ollama: not running or not installed"
fi

echo ""
echo "🚀 Ready to transcribe!"
echo "   python3 transcribe_yt.py 'YOUR_YOUTUBE_URL_HERE'"
echo ""