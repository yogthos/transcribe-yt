#!/usr/bin/env python3
"""
Build script for creating a macOS .app bundle without PyInstaller issues
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def create_app_bundle():
    """Create the macOS .app bundle structure"""

    # App bundle name and paths
    app_name = "TranscribeYouTube"
    app_bundle_path = f"dist/{app_name}.app"
    contents_path = f"{app_bundle_path}/Contents"
    macos_path = f"{contents_path}/MacOS"
    resources_path = f"{contents_path}/Resources"

    print(f"Creating {app_name}.app bundle...")

    # Remove existing bundle if it exists
    if os.path.exists(app_bundle_path):
        print(f"Removing existing {app_bundle_path}...")
        shutil.rmtree(app_bundle_path)

    # Create directory structure
    os.makedirs(macos_path, exist_ok=True)
    os.makedirs(resources_path, exist_ok=True)

    # Create Info.plist
    info_plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>{app_name}</string>
    <key>CFBundleIdentifier</key>
    <string>com.transcribeyt.app</string>
    <key>CFBundleName</key>
    <string>{app_name}</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
    <key>NSAppleScriptEnabled</key>
    <false/>
    <key>CFBundleDocumentTypes</key>
    <array>
        <dict>
            <key>CFBundleTypeName</key>
            <string>YouTube URL</string>
            <key>CFBundleTypeRole</key>
            <string>Viewer</string>
            <key>LSItemContentTypes</key>
            <array>
                <string>public.url</string>
            </array>
        </dict>
    </array>
</dict>
</plist>"""

    with open(f"{contents_path}/Info.plist", "w") as f:
        f.write(info_plist_content)

    # Create the main executable script
    launcher_script = f"""#!/bin/bash
# Get the path to the app bundle
APP_BUNDLE_PATH="$(dirname "$(dirname "$(realpath "$0")")")"
RESOURCES_PATH="$APP_BUNDLE_PATH/Resources"
VENV_PATH="$RESOURCES_PATH/venv"
VENV_PYTHON="$VENV_PATH/bin/python"

# Change to the resources directory
cd "$RESOURCES_PATH"

# Add the app bundle's bin directory to PATH for ffmpeg and yt-dlp
export PATH="$RESOURCES_PATH/bin:$PATH"

# Check if virtual environment exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "Error: Virtual environment not found at $VENV_PATH"
    echo "Please run the packaging script again."
    exit 1
fi

# Run the GUI using the virtual environment Python
exec "$VENV_PYTHON" -c "
import sys
import os

# Add the resources path to Python path
sys.path.insert(0, '$RESOURCES_PATH')

try:
    from transcribe_yt_gui import main
    main()
except ImportError as e:
    print(f'Error importing GUI module: {{e}}')
    print('Make sure all dependencies are installed in the virtual environment.')
    print(f'Virtual environment path: $VENV_PATH')
    print(f'Python executable: $VENV_PYTHON')
    sys.exit(1)
except Exception as e:
    print(f'Error running GUI: {{e}}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"
"""

    launcher_path = f"{macos_path}/{app_name}"
    with open(launcher_path, "w") as f:
        f.write(launcher_script)

    # Make the launcher executable
    os.chmod(launcher_path, 0o755)

    # Copy application files to Resources
    print("Copying application files...")
    files_to_copy = [
        "transcribe_yt_gui.py",
        "transcribe_yt.py",
        "requirements.txt",
        "README.md"
    ]

    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy2(file, resources_path)
            print(f"Copied {file}")

    # Copy ffmpeg and yt-dlp binaries
    print("Copying external binaries...")
    bin_path = os.path.join(resources_path, "bin")
    os.makedirs(bin_path, exist_ok=True)

    # Copy ffmpeg
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        ffmpeg_dest = os.path.join(bin_path, "ffmpeg")
        shutil.copy2(ffmpeg_path, ffmpeg_dest)
        os.chmod(ffmpeg_dest, 0o755)  # Make it executable
        print(f"Copied ffmpeg to {ffmpeg_dest}")
    else:
        print("❌ ffmpeg not found in system PATH")
        print("Please install ffmpeg: brew install ffmpeg")
        return False

    # Copy ffprobe if available
    ffprobe_path = shutil.which("ffprobe")
    if ffprobe_path:
        ffprobe_dest = os.path.join(bin_path, "ffprobe")
        shutil.copy2(ffprobe_path, ffprobe_dest)
        os.chmod(ffprobe_dest, 0o755)
        print(f"Copied ffprobe to {ffprobe_dest}")

    # Copy yt-dlp
    ytdlp_path = shutil.which("yt-dlp")
    if ytdlp_path:
        ytdlp_dest = os.path.join(bin_path, "yt-dlp")
        shutil.copy2(ytdlp_path, ytdlp_dest)
        os.chmod(ytdlp_dest, 0o755)  # Make it executable
        print(f"Copied yt-dlp to {ytdlp_dest}")
    else:
        print("❌ yt-dlp not found in system PATH")
        print("Please install yt-dlp: pip install yt-dlp")
        return False

    # Create a virtual environment in the app bundle
    print("Creating virtual environment in app bundle...")
    venv_path = f"{resources_path}/venv"

    try:
        subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
        print("Virtual environment created successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e}")
        return False

    # Install dependencies in the virtual environment
    print("Installing dependencies...")
    pip_path = f"{venv_path}/bin/pip"
    requirements_path = f"{resources_path}/requirements.txt"

    try:
        subprocess.run([pip_path, "install", "-r", requirements_path], check=True)
        print("Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False

    print(f"\n✅ {app_name}.app bundle created successfully!")
    print(f"Location: {os.path.abspath(app_bundle_path)}")
    print("\nTo run the app:")
    print(f"  open {app_bundle_path}")
    print("\nTo distribute the app:")
    print(f"  zip -r {app_name}.zip {app_bundle_path}")

    return True

def main():
    """Main build function"""
    print("Transcribe YouTube - Simple macOS App Builder")
    print("=" * 50)

    # Check if we're on macOS
    if sys.platform != "darwin":
        print("❌ This script is designed for macOS only.")
        sys.exit(1)

    # Check if required files exist
    required_files = ["transcribe_yt_gui.py", "transcribe_yt.py"]
    missing_files = [f for f in required_files if not os.path.exists(f)]

    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        sys.exit(1)

    # Create the app bundle
    if create_app_bundle():
        print("\n🎉 App bundle built successfully!")
    else:
        print("\n❌ App bundle creation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
