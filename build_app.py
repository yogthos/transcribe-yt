#!/usr/bin/env python3
"""
Build script for creating a macOS .app bundle using PyInstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_pyinstaller():
    """Install PyInstaller if not already installed"""
    try:
        import PyInstaller
        print("✅ PyInstaller is already installed")
        return True
    except ImportError:
        print("Installing PyInstaller...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
            print("✅ PyInstaller installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install PyInstaller")
            return False

def create_spec_file():
    """Create a PyInstaller spec file for the app"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['transcribe_yt_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('transcribe_yt.py', '.'),
        ('requirements.txt', '.'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        'gi',
        'gi.repository.Gtk',
        'gi.repository.Gdk',
        'gi.repository.GLib',
        'gi.repository.Pango',
        'markdown',
        'beautifulsoup4',
        'requests',
        'nemo.collections.asr',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TranscribeYouTube',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.icns' if os.path.exists('app_icon.icns') else None,
)

app = BUNDLE(
    exe,
    name='TranscribeYouTube.app',
    icon='app_icon.icns' if os.path.exists('app_icon.icns') else None,
    bundle_identifier='com.transcribeyt.app',
    info_plist={
        'CFBundleName': 'Transcribe YouTube',
        'CFBundleDisplayName': 'Transcribe YouTube',
        'CFBundleVersion': '1.0',
        'CFBundleShortVersionString': '1.0',
        'CFBundleIdentifier': 'com.transcribeyt.app',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.15',
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'YouTube URL',
                'CFBundleTypeRole': 'Viewer',
                'LSItemContentTypes': ['public.url'],
            }
        ],
    },
)
'''

    with open('TranscribeYouTube.spec', 'w') as f:
        f.write(spec_content)

    print("✅ PyInstaller spec file created")

def build_app():
    """Build the .app bundle using PyInstaller"""
    print("Building .app bundle with PyInstaller...")

    try:
        # Run PyInstaller
        cmd = [sys.executable, "-m", "PyInstaller", "--clean", "TranscribeYouTube.spec"]
        subprocess.run(cmd, check=True)

        # Check if the app was created
        app_path = "dist/TranscribeYouTube.app"
        if os.path.exists(app_path):
            print(f"✅ App bundle created successfully: {app_path}")
            return True
        else:
            print("❌ App bundle not found after build")
            return False

    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller build failed: {e}")
        return False

def create_simple_icon():
    """Create a simple icon file (placeholder)"""
    # This is a placeholder - in a real app, you'd want a proper .icns file
    icon_content = """# Transcribe YouTube App Icon
# This is a placeholder
# For production, replace with a proper .icns file
"""

    with open('app_icon.txt', 'w') as f:
        f.write(icon_content)

    print("✅ Placeholder icon created (replace with .icns for production)")

def cleanup():
    """Clean up build artifacts"""
    cleanup_dirs = ['build', '__pycache__']
    cleanup_files = ['TranscribeYouTube.spec', 'app_icon.txt']

    for dir_name in cleanup_dirs:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"Cleaned up {dir_name}")

    for file_name in cleanup_files:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"Cleaned up {file_name}")

def main():
    """Main build function"""
    print("Transcribe YouTube - macOS App Builder")
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

    # Install PyInstaller
    if not install_pyinstaller():
        sys.exit(1)

    # Create icon placeholder
    create_simple_icon()

    # Create spec file
    create_spec_file()

    # Build the app
    if build_app():
        print("\n🎉 App bundle built successfully!")
        print("Location: dist/TranscribeYouTube.app")
        print("\nTo run the app:")
        print("  open dist/TranscribeYouTube.app")
        print("\nTo distribute the app:")
        print("  zip -r TranscribeYouTube.zip dist/TranscribeYouTube.app")

        # Ask if user wants to clean up
        response = input("\nClean up build artifacts? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            cleanup()
            print("✅ Build artifacts cleaned up")
    else:
        print("\n❌ App build failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
