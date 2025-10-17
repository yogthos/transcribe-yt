#!/usr/bin/env python3
"""
Build script for creating a macOS .app bundle without PyInstaller issues
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def copy_gtk_dependencies(resources_path):
    """Copy GTK libraries and typelib files to the app bundle"""
    homebrew_prefix = "/opt/homebrew"

    # Create directories for GTK files
    lib_path = os.path.join(resources_path, "lib")
    share_path = os.path.join(resources_path, "share")
    gir_path = os.path.join(share_path, "gir-1.0")
    typelib_path = os.path.join(lib_path, "girepository-1.0")

    os.makedirs(lib_path, exist_ok=True)
    os.makedirs(share_path, exist_ok=True)
    os.makedirs(gir_path, exist_ok=True)
    os.makedirs(typelib_path, exist_ok=True)

    try:
        # GTK libraries to copy
        gtk_libs = [
            "libgtk-3.0.dylib",
            "libgdk-3.0.dylib",
            "libgobject-2.0.0.dylib",
            "libglib-2.0.0.dylib",
            "libgio-2.0.0.dylib",
            "libgmodule-2.0.0.dylib",
            "libgthread-2.0.0.dylib",
            "libcairo.2.dylib",
            "libpango-1.0.0.dylib",
            "libpangocairo-1.0.0.dylib",
            "libpangoft2-1.0.0.dylib",
            "libgdk_pixbuf-2.0.0.dylib",
            "libepoxy.0.dylib",
            "libharfbuzz.0.dylib",
            "libfreetype.6.dylib",
            "libfontconfig.1.dylib",
            "libintl.8.dylib",
            "libatk-1.0.0.dylib"
        ]

        # Copy libraries
        for lib in gtk_libs:
            src = os.path.join(homebrew_prefix, "lib", lib)
            if os.path.exists(src):
                dst = os.path.join(lib_path, lib)
                if not os.path.exists(dst):
                    shutil.copy2(src, dst)
                    print(f"Copied {lib}")
                else:
                    print(f"Skipped {lib} (already exists)")
            else:
                print(f"Warning: {lib} not found")

        # Copy typelib files for GTK
        typelib_files = [
            "Gtk-3.0.typelib",
            "Gdk-3.0.typelib",
            "Gio-2.0.typelib",
            "GLib-2.0.typelib",
            "GObject-2.0.typelib",
            "cairo-1.0.typelib",
            "Pango-1.0.typelib",
            "GdkPixbuf-2.0.typelib",
            "GModule-2.0.typelib",
            "Atk-1.0.typelib",
            "GdkPixbuf-2.0.typelib",
            "Gio-2.0.typelib",
            "GLib-2.0.typelib",
            "GObject-2.0.typelib"
        ]

        for typelib in typelib_files:
            src = os.path.join(homebrew_prefix, "lib", "girepository-1.0", typelib)
            if os.path.exists(src):
                dst = os.path.join(typelib_path, typelib)
                if not os.path.exists(dst):
                    shutil.copy2(src, dst)
                    print(f"Copied {typelib}")
                else:
                    print(f"Skipped {typelib} (already exists)")
            else:
                print(f"Warning: {typelib} not found")

        # Copy GIR files
        gir_files = [
            "Gtk-3.0.gir",
            "Gdk-3.0.gir",
            "Gio-2.0.gir",
            "GLib-2.0.gir",
            "GObject-2.0.gir",
            "cairo-1.0.gir",
            "Pango-1.0.gir",
            "GdkPixbuf-2.0.gir",
            "Atk-1.0.gir"
        ]

        for gir_file in gir_files:
            src = os.path.join(homebrew_prefix, "share", "gir-1.0", gir_file)
            if os.path.exists(src):
                dst = os.path.join(gir_path, gir_file)
                if not os.path.exists(dst):
                    shutil.copy2(src, dst)
                    print(f"Copied {gir_file}")
                else:
                    print(f"Skipped {gir_file} (already exists)")
            else:
                print(f"Warning: {gir_file} not found")

        # Copy GTK schemas
        schemas_path = os.path.join(share_path, "glib-2.0", "schemas")
        os.makedirs(schemas_path, exist_ok=True)

        schemas_src = os.path.join(homebrew_prefix, "share", "glib-2.0", "schemas")
        if os.path.exists(schemas_src):
            for schema_file in os.listdir(schemas_src):
                if schema_file.endswith(".gschema.xml"):
                    src = os.path.join(schemas_src, schema_file)
                    dst = os.path.join(schemas_path, schema_file)
                    if not os.path.exists(dst):
                        shutil.copy2(src, dst)
                        print(f"Copied schema {schema_file}")
                    else:
                        print(f"Skipped schema {schema_file} (already exists)")

        # Compile schemas
        if os.path.exists(schemas_path):
            try:
                subprocess.run([
                    os.path.join(homebrew_prefix, "bin", "glib-compile-schemas"),
                    schemas_path
                ], check=True)
                print("Compiled GTK schemas")
            except subprocess.CalledProcessError:
                print("Warning: Failed to compile GTK schemas")

        print("GTK dependencies copied successfully")
        return True

    except Exception as e:
        print(f"Error copying GTK dependencies: {e}")
        return False

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

# Set up GTK environment variables
export PKG_CONFIG_PATH="$RESOURCES_PATH/lib/pkgconfig:$RESOURCES_PATH/share/pkgconfig:$PKG_CONFIG_PATH"
export DYLD_LIBRARY_PATH="$RESOURCES_PATH/lib:$DYLD_LIBRARY_PATH"
export GI_TYPELIB_PATH="$RESOURCES_PATH/share/gir-1.0:$GI_TYPELIB_PATH"
export XDG_DATA_DIRS="$RESOURCES_PATH/share:$XDG_DATA_DIRS"

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
        "config.py",
        "download.py",
        "transcription.py",
        "summarization.py",
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
    venv_path = os.path.join(resources_path, "venv")

    try:
        subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
        print("Virtual environment created successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e}")
        return False

    # Install dependencies in the virtual environment
    print("Installing dependencies...")
    pip_path = os.path.join(venv_path, "bin", "pip")
    requirements_path = os.path.join(resources_path, "requirements.txt")

    # Set environment for pip to find GTK-related packages
    env = os.environ.copy()
    env['PKG_CONFIG_PATH'] = f"{resources_path}/lib/pkgconfig:{resources_path}/share/pkgconfig:/opt/homebrew/lib/pkgconfig:/opt/homebrew/share/pkgconfig:{env.get('PKG_CONFIG_PATH', '')}"
    env['DYLD_LIBRARY_PATH'] = f"{resources_path}/lib:/opt/homebrew/lib:{env.get('DYLD_LIBRARY_PATH', '')}"
    env['GI_TYPELIB_PATH'] = f"{resources_path}/share/gir-1.0:/opt/homebrew/share/gir-1.0:{env.get('GI_TYPELIB_PATH', '')}"

    try:
        subprocess.run([pip_path, "install", "-r", requirements_path], check=True, env=env)
        print("Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False

    # Copy GTK libraries and typelib files
    print("Copying GTK libraries and typelib files...")
    if not copy_gtk_dependencies(resources_path):
        print("Failed to copy GTK dependencies")
        return False

    # Skip spaCy model download during build due to PyTorch circular import issues
    print("Skipping spaCy English model download during build...")
    print("The model will be downloaded automatically on first use of extractive summarization.")

    # Skip Hugging Face model download during build due to potential torch import issues
    print("Skipping Hugging Face model download during build...")
    print("The model will be downloaded automatically on first use of the application.")

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
    required_files = [
        "transcribe_yt_gui.py",
        "transcribe_yt.py",
        "config.py",
        "download.py",
        "transcription.py",
        "summarization.py"
    ]
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
