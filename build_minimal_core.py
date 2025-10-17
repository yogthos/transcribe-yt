#!/usr/bin/env python3
"""
Minimal core build script for creating a macOS .app bundle
Focuses only on essential functionality without complex dependencies
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

def create_minimal_gui():
    """Create a minimal GUI version without complex dependencies"""
    minimal_gui_content = '''#!/usr/bin/env python3
"""
Minimal GUI version of Transcribe YouTube
Only includes basic functionality without complex ML dependencies
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango
import subprocess
import os
import sys
from pathlib import Path

class TranscribeYouTubeGUI:
    def __init__(self):
        self.window = Gtk.Window(title="Transcribe YouTube - Minimal")
        self.window.set_default_size(800, 600)
        self.window.connect("destroy", Gtk.main_quit)

        # Create main container
        main_box = Gtk.VBox(spacing=10)
        main_box.set_margin_left(20)
        main_box.set_margin_right(20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        self.window.add(main_box)

        # Title
        title_label = Gtk.Label()
        title_label.set_markup("<span size='large' weight='bold'>Transcribe YouTube - Minimal Version</span>")
        main_box.pack_start(title_label, False, False, 0)

        # URL input
        url_frame = Gtk.Frame(label="YouTube URL")
        url_box = Gtk.VBox(spacing=5)
        url_frame.add(url_box)

        self.url_entry = Gtk.Entry()
        self.url_entry.set_placeholder_text("Enter YouTube URL here...")
        url_box.pack_start(self.url_entry, False, False, 0)

        # Buttons
        button_box = Gtk.HBox(spacing=10)

        self.download_button = Gtk.Button(label="Download Audio")
        self.download_button.connect("clicked", self.on_download_clicked)
        button_box.pack_start(self.download_button, False, False, 0)

        self.transcribe_button = Gtk.Button(label="Transcribe")
        self.transcribe_button.connect("clicked", self.on_transcribe_clicked)
        self.transcribe_button.set_sensitive(False)
        button_box.pack_start(self.transcribe_button, False, False, 0)

        url_box.pack_start(button_box, False, False, 0)
        main_box.pack_start(url_frame, False, False, 0)

        # Status
        self.status_label = Gtk.Label("Ready")
        main_box.pack_start(self.status_label, False, False, 0)

        # Output text
        output_frame = Gtk.Frame(label="Output")
        self.output_textview = Gtk.TextView()
        self.output_textview.set_editable(False)
        self.output_textview.set_wrap_mode(Gtk.WrapMode.WORD)

        # Set up font
        font_desc = Pango.FontDescription("monospace 10")
        self.output_textview.modify_font(font_desc)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.add(self.output_textview)
        output_frame.add(scrolled_window)

        main_box.pack_start(output_frame, True, True, 0)

        # Store paths
        self.audio_path = None
        self.transcript_path = None

    def update_status(self, message):
        """Update status label"""
        self.status_label.set_text(message)
        while Gtk.events_pending():
            Gtk.main_iteration()

    def append_output(self, text):
        """Append text to output"""
        buffer = self.output_textview.get_buffer()
        buffer.insert(buffer.get_end_iter(), text + "\\n")
        # Scroll to bottom
        self.output_textview.scroll_to_mark(buffer.get_insert(), 0.0, False, 0.0, 1.0)
        while Gtk.events_pending():
            Gtk.main_iteration()

    def on_download_clicked(self, widget):
        """Handle download button click"""
        url = self.url_entry.get_text().strip()
        if not url:
            self.update_status("Please enter a YouTube URL")
            return

        self.update_status("Downloading audio...")
        self.append_output(f"Downloading audio from: {url}")

        # Create output directory
        output_dir = Path.home() / ".transcribe-yt" / "downloads"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Download audio using yt-dlp
        try:
            cmd = [
                "yt-dlp",
                "-x",  # Extract audio
                "--audio-format", "wav",
                "--output", str(output_dir / "%(title)s.%(ext)s"),
                url
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                # Find the downloaded file
                audio_files = list(output_dir.glob("*.wav"))
                if audio_files:
                    self.audio_path = audio_files[0]
                    self.update_status("Audio downloaded successfully")
                    self.append_output(f"Audio saved to: {self.audio_path}")
                    self.transcribe_button.set_sensitive(True)
                else:
                    self.update_status("Download completed but no audio file found")
            else:
                self.update_status("Download failed")
                self.append_output(f"Error: {result.stderr}")

        except subprocess.TimeoutExpired:
            self.update_status("Download timed out")
            self.append_output("Download timed out after 5 minutes")
        except Exception as e:
            self.update_status(f"Download error: {e}")
            self.append_output(f"Error: {e}")

    def on_transcribe_clicked(self, widget):
        """Handle transcribe button click"""
        if not self.audio_path or not self.audio_path.exists():
            self.update_status("No audio file available")
            return

        self.update_status("Transcribing audio...")
        self.append_output(f"Transcribing: {self.audio_path}")

        # For this minimal version, we'll just create a placeholder transcript
        # In a real implementation, you would use a speech recognition service
        transcript_text = f"""
TRANSCRIPT PLACEHOLDER

This is a minimal version of Transcribe YouTube.
The audio file has been downloaded to: {self.audio_path}

To add full transcription functionality, you would need to:
1. Install a speech recognition library (e.g., whisper, speech_recognition)
2. Add the transcription logic here
3. Implement the full transcribe_yt.py functionality

For now, this demonstrates the basic GUI structure and file handling.
"""

        # Save transcript
        self.transcript_path = self.audio_path.with_suffix('.txt')
        with open(self.transcript_path, 'w', encoding='utf-8') as f:
            f.write(transcript_text)

        self.update_status("Transcription completed (placeholder)")
        self.append_output(f"Transcript saved to: {self.transcript_path}")
        self.append_output("\\n" + transcript_text)

    def run(self):
        """Run the GUI"""
        self.window.show_all()
        Gtk.main()

if __name__ == "__main__":
    app = TranscribeYouTubeGUI()
    app.run()
'''

    with open("transcribe_yt_minimal_gui.py", "w") as f:
        f.write(minimal_gui_content)

    print("✅ Created minimal GUI version")

def build_minimal_core_app():
    """Build the minimal core app"""
    print("Building minimal core app...")

    try:
        # Create a very simple spec file
        spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['transcribe_yt_minimal_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'gi',
        'gi.repository.Gtk',
        'gi.repository.Gdk',
        'gi.repository.GLib',
        'gi.repository.Pango',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'setuptools',
        'distutils',
        'pip',
        'wheel',
        'pkg_resources',
        'packaging',
        'importlib_metadata',
        'importlib_resources',
        'zipp',
        'more_itertools',
    ],
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
    codesign_identity='-',
    entitlements_file=None,
)

app = BUNDLE(
    exe,
    name='TranscribeYouTube.app',
    icon=None,
    bundle_identifier='com.transcribeyt.app',
    info_plist={
        'CFBundleName': 'Transcribe YouTube',
        'CFBundleDisplayName': 'Transcribe YouTube',
        'CFBundleVersion': '1.0',
        'CFBundleShortVersionString': '1.0',
        'CFBundleIdentifier': 'com.transcribeyt.app',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.15',
    },
)
'''

        # Write the spec file
        spec_path = "TranscribeYouTube_minimal_core.spec"
        with open(spec_path, "w") as f:
            f.write(spec_content)

        # Run PyInstaller
        cmd = [sys.executable, "-m", "PyInstaller", "--clean", spec_path]
        subprocess.run(cmd, check=True)

        # Check if the app was created
        app_path = "dist/TranscribeYouTube.app"
        if os.path.exists(app_path):
            print(f"✅ Minimal core app created: {app_path}")
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

    # Copy yt-dlp
    ytdlp_path = shutil.which("yt-dlp")
    if ytdlp_path:
        ytdlp_dest = os.path.join(bin_path, "yt-dlp")
        shutil.copy2(ytdlp_path, ytdlp_dest)
        os.chmod(ytdlp_dest, 0o755)
        print(f"✅ Copied yt-dlp to {ytdlp_dest}")
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
        print("Signing app bundle...")
        cmd = ["codesign", "--force", "--sign", "-", app_path]
        subprocess.run(cmd, check=True)
        print("✅ App bundle signed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Code signing failed: {e}")
        return False

def cleanup():
    """Clean up build artifacts"""
    cleanup_dirs = ['build', '__pycache__']
    cleanup_files = ['TranscribeYouTube_minimal_core.spec', 'transcribe_yt_minimal_gui.py']

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
    print("Transcribe YouTube - Minimal Core Build")
    print("=" * 50)

    # Check if we're on macOS
    if sys.platform != "darwin":
        print("❌ This script is designed for macOS only.")
        sys.exit(1)

    # Install PyInstaller
    if not install_pyinstaller():
        sys.exit(1)

    # Create minimal GUI
    print("\\nCreating minimal GUI version...")
    create_minimal_gui()

    # Build the minimal core app
    if not build_minimal_core_app():
        print("\\n❌ Minimal core app build failed!")
        sys.exit(1)

    # Copy external binaries
    print("\\nCopying external binaries...")
    copy_external_binaries()

    # Sign the app bundle
    print("\\nSigning app bundle...")
    if not sign_app_bundle():
        print("⚠️ Code signing failed, but app should still work")

    print("\\n🎉 Minimal core app built successfully!")
    print("Location: dist/TranscribeYouTube.app")
    print("\\nTo run the app:")
    print("  open dist/TranscribeYouTube.app")
    print("\\nNote: This is a minimal version with basic functionality.")
    print("For full features, use the original transcribe_yt_gui.py")

    # Ask if user wants to clean up
    response = input("\\nClean up build artifacts? (y/N): ").strip().lower()
    if response in ['y', 'yes']:
        cleanup()
        print("✅ Build artifacts cleaned up")

if __name__ == "__main__":
    main()
