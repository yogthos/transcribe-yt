#!/usr/bin/env python3
"""
Minimal build script for creating a macOS .app bundle with PyInstaller
Excludes unnecessary libraries and enables code signing
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

def build_minimal_app():
    """Build the .app bundle using minimal PyInstaller spec"""
    print("Building minimal .app bundle with PyInstaller...")

    try:
        # Run PyInstaller with minimal spec
        cmd = [sys.executable, "-m", "PyInstaller", "--clean", "TranscribeYouTube_minimal.spec"]
        subprocess.run(cmd, check=True)

        # Check if the app was created
        app_path = "dist/TranscribeYouTube.app"
        if os.path.exists(app_path):
            print(f"✅ Minimal app bundle created successfully: {app_path}")
            return True
        else:
            print("❌ App bundle not found after build")
            return False

    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller build failed: {e}")
        return False

def copy_external_binaries():
    """Copy external binaries to the app bundle"""
    app_path = "dist/TranscribeYouTube.app"
    if not os.path.exists(app_path):
        print("❌ App bundle not found")
        return False

    # Create bin directory in app bundle
    bin_path = os.path.join(app_path, "Contents", "Resources", "bin")
    os.makedirs(bin_path, exist_ok=True)

    # Copy ffmpeg
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        ffmpeg_dest = os.path.join(bin_path, "ffmpeg")
        shutil.copy2(ffmpeg_path, ffmpeg_dest)
        os.chmod(ffmpeg_dest, 0o755)
        print(f"Copied ffmpeg to {ffmpeg_dest}")
    else:
        print("⚠️ ffmpeg not found in system PATH")

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
        os.chmod(ytdlp_dest, 0o755)
        print(f"Copied yt-dlp to {ytdlp_dest}")
    else:
        print("⚠️ yt-dlp not found in system PATH")

    return True

def sign_app_bundle():
    """Sign the app bundle with ad-hoc signing"""
    app_path = "dist/TranscribeYouTube.app"
    if not os.path.exists(app_path):
        print("❌ App bundle not found for signing")
        return False

    try:
        print("Signing app bundle with ad-hoc signature...")
        cmd = ["codesign", "--force", "--sign", "-", app_path]
        subprocess.run(cmd, check=True)
        print("✅ App bundle signed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Code signing failed: {e}")
        return False

def verify_app_bundle():
    """Verify the app bundle"""
    app_path = "dist/TranscribeYouTube.app"
    if not os.path.exists(app_path):
        print("❌ App bundle not found for verification")
        return False

    try:
        print("Verifying app bundle...")
        cmd = ["codesign", "--verify", "--verbose", app_path]
        subprocess.run(cmd, check=True)
        print("✅ App bundle verification successful")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ App bundle verification failed: {e}")
        return False

def cleanup():
    """Clean up build artifacts"""
    cleanup_dirs = ['build', '__pycache__']
    cleanup_files = ['TranscribeYouTube_minimal.spec']

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
    print("Transcribe YouTube - Minimal PyInstaller Build")
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

    # Build the minimal app
    if not build_minimal_app():
        print("\n❌ Minimal app build failed!")
        sys.exit(1)

    # Copy external binaries
    print("\nCopying external binaries...")
    copy_external_binaries()

    # Download Hugging Face model after build
    print("\nSkipping spaCy English model download during build...")
    print("The model will be downloaded automatically on first use of extractive summarization.")

    print("\nDownloading Hugging Face model...")
    try:
        # Run a Python script to download the model
        download_script = """
import sys
import os
sys.path.insert(0, '.')

# Set custom cache directory for models
cache_dir = os.path.expanduser("~/.transcribe-yt/models")
os.makedirs(cache_dir, exist_ok=True)

# Set environment variables for transformers cache
os.environ['TRANSFORMERS_CACHE'] = cache_dir
os.environ['HF_HOME'] = cache_dir

print(f"Using model cache directory: {{cache_dir}}")

try:
    from transformers import pipeline
    print("Downloading facebook/bart-large-cnn model...")
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn", cache_dir=cache_dir)
    print("Hugging Face model downloaded successfully")
except Exception as e:
    print(f"Warning: Failed to download Hugging Face model: {{e}}")
    print("The model will be downloaded on first use instead")
"""

        # Write the download script to a temporary file
        download_script_path = os.path.join(resources_path, "download_model.py")
        with open(download_script_path, "w") as f:
            f.write(download_script)

        # Run the download script
        python_cmd = [sys.executable, download_script_path]
        subprocess.run(python_cmd, check=True, cwd=resources_path)

        # Clean up the temporary script
        os.remove(download_script_path)

        print("Hugging Face model downloaded successfully")
    except Exception as e:
        print(f"Warning: Failed to download Hugging Face model: {e}")
        print("The model will be downloaded on first use instead")

    # Sign the app bundle
    print("\nSigning app bundle...")
    if not sign_app_bundle():
        print("⚠️ Code signing failed, but app should still work")

    # Verify the app bundle
    print("\nVerifying app bundle...")
    verify_app_bundle()

    print("\n🎉 Minimal app bundle built successfully!")
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

if __name__ == "__main__":
    main()
