#!/bin/bash
# Simple script to create a macOS .app bundle for Transcribe YouTube

set -e

echo "Transcribe YouTube - macOS App Creator"
echo "======================================"

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is designed for macOS only."
    exit 1
fi

# Check if required files exist
required_files=("transcribe_yt_gui.py" "transcribe_yt.py")
for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "❌ Missing required file: $file"
        exit 1
    fi
done

echo "✅ Required files found"

# Choose packaging method
echo ""
echo "Choose packaging method:"
echo "1) Simple .app bundle (recommended for development)"
echo "2) PyInstaller bundle (recommended for distribution)"
echo ""
read -p "Enter choice (1 or 2): " choice

case $choice in
    1)
        echo "Creating simple .app bundle..."
        python3 package_app.py
        ;;
    2)
        echo "Creating PyInstaller bundle..."
        python3 build_app.py
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "🎉 App creation completed!"
echo ""
echo "To run the app:"
if [[ $choice == 1 ]]; then
    echo "  open TranscribeYouTube.app"
else
    echo "  open dist/TranscribeYouTube.app"
fi
echo ""
echo "To distribute the app:"
if [[ $choice == 1 ]]; then
    echo "  zip -r TranscribeYouTube.zip TranscribeYouTube.app"
else
    echo "  zip -r TranscribeYouTube.zip dist/TranscribeYouTube.app"
fi
