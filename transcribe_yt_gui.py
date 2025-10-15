#!/usr/bin/env python3
"""
GTK GUI for YouTube Video Transcription and Summarization Tool
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango
import threading
import os
import sys
import markdown
from pathlib import Path

# Import the transcription logic from the main module
from transcribe_yt import (
    download_subtitles, download_audio, convert_srt_to_text,
    transcribe_audio, generate_summary_deepseek, generate_summary_ollama,
    load_config, save_config, check_dependencies
)


class TranscribeYTGUI:
    def __init__(self):
        self.window = Gtk.Window(title="Transcribe YouTube")
        self.window.set_default_size(900, 700)
        self.window.set_resizable(True)
        self.window.connect("destroy", self.on_window_destroy)

        # Create main container
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.main_box.set_margin_left(10)
        self.main_box.set_margin_right(10)
        self.main_box.set_margin_top(10)
        self.main_box.set_margin_bottom(10)
        self.window.add(self.main_box)

        # Create input section
        self.create_input_section()

        # Create progress section
        self.create_progress_section()

        # Create summary section
        self.create_summary_section()

        # Load configuration
        self.config = load_config()
        self.update_config_ui()

    def create_input_section(self):
        """Create the input section with URL field and controls"""
        # Input frame
        input_frame = Gtk.Frame(label="Input")
        input_frame.set_margin_bottom(10)
        self.main_box.pack_start(input_frame, False, False, 0)

        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        input_box.set_margin_left(10)
        input_box.set_margin_right(10)
        input_box.set_margin_top(10)
        input_box.set_margin_bottom(10)
        input_frame.add(input_box)

        # URL input
        url_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        url_label = Gtk.Label("YouTube URL:")
        url_label.set_size_request(120, -1)
        url_label.set_halign(Gtk.Align.START)

        self.url_entry = Gtk.Entry()
        self.url_entry.set_placeholder_text("https://youtube.com/watch?v=...")
        self.url_entry.connect("activate", self.on_transcribe_clicked)

        url_box.pack_start(url_label, False, False, 0)
        url_box.pack_start(self.url_entry, True, True, 0)
        input_box.pack_start(url_box, False, False, 0)

        # Options box
        options_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)

        # Model selection
        model_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        model_label = Gtk.Label("Model:")
        model_label.set_size_request(60, -1)
        model_label.set_halign(Gtk.Align.START)

        self.model_combo = Gtk.ComboBoxText()
        self.model_combo.append_text("DeepSeek API")
        self.model_combo.append_text("Ollama (Local)")
        self.model_combo.set_active(0)

        model_box.pack_start(model_label, False, False, 0)
        model_box.pack_start(self.model_combo, False, False, 0)
        options_box.pack_start(model_box, False, False, 0)

        # Force transcribe checkbox
        self.force_transcribe_check = Gtk.CheckButton(label="Force audio transcription")
        options_box.pack_start(self.force_transcribe_check, False, False, 0)

        input_box.pack_start(options_box, False, False, 0)

        # Button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.transcribe_button = Gtk.Button(label="Start Transcription")
        self.transcribe_button.set_size_request(150, -1)
        self.transcribe_button.connect("clicked", self.on_transcribe_clicked)
        self.transcribe_button.get_style_context().add_class("suggested-action")

        self.configure_button = Gtk.Button(label="Configure")
        self.configure_button.connect("clicked", self.on_configure_clicked)

        self.clear_button = Gtk.Button(label="Clear")
        self.clear_button.connect("clicked", self.on_clear_clicked)

        button_box.pack_start(self.transcribe_button, False, False, 0)
        button_box.pack_start(self.configure_button, False, False, 0)
        button_box.pack_start(self.clear_button, False, False, 0)

        input_box.pack_start(button_box, False, False, 0)

    def create_progress_section(self):
        """Create the progress section"""
        # Progress frame
        progress_frame = Gtk.Frame(label="Progress")
        progress_frame.set_margin_bottom(10)
        self.main_box.pack_start(progress_frame, False, False, 0)

        progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        progress_box.set_margin_left(10)
        progress_box.set_margin_right(10)
        progress_box.set_margin_top(10)
        progress_box.set_margin_bottom(10)
        progress_frame.add(progress_box)

        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_text("Ready")
        progress_box.pack_start(self.progress_bar, False, False, 0)

        # Status label
        self.status_label = Gtk.Label("Ready")
        self.status_label.set_halign(Gtk.Align.START)
        progress_box.pack_start(self.status_label, False, False, 0)

    def create_summary_section(self):
        """Create the summary section with TextView for text rendering"""
        # Summary frame
        summary_frame = Gtk.Frame(label="Summary")
        self.main_box.pack_start(summary_frame, True, True, 0)

        # Create TextView for summary display
        self.summary_textview = Gtk.TextView()
        self.summary_textview.set_editable(False)
        self.summary_textview.set_wrap_mode(Gtk.WrapMode.WORD)
        self.summary_textview.set_margin_left(10)
        self.summary_textview.set_margin_right(10)
        self.summary_textview.set_margin_top(10)
        self.summary_textview.set_margin_bottom(10)

        # Set up font
        font_desc = Pango.FontDescription("monospace 12")
        self.summary_textview.modify_font(font_desc)

        # Create scrolled window for the textview
        self.summary_scrolled = Gtk.ScrolledWindow()
        self.summary_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.summary_scrolled.add(self.summary_textview)

        summary_frame.add(self.summary_scrolled)

        # Set initial content
        self.set_initial_content()

    def set_initial_content(self):
        """Set initial content for the summary view"""
        initial_text = """Transcribe YouTube
================

Enter a YouTube URL above and click "Start Transcription" to begin.

The summary will appear here once the transcription is complete.

Features:
• Automatic subtitle detection and download
• Audio transcription using NVIDIA Parakeet
• AI-powered summarization with DeepSeek or Ollama
• Rich markdown formatting support
"""
        buffer = self.summary_textview.get_buffer()
        buffer.set_text(initial_text)


    def update_config_ui(self):
        """Update UI elements based on loaded configuration"""
        # Update model selection if configured
        if "ollama_model" in self.config:
            # For now, keep default selection (DeepSeek)
            pass

    def on_transcribe_clicked(self, widget):
        """Handle transcribe button click"""
        url = self.url_entry.get_text().strip()
        if not url:
            self.show_error("Please enter a YouTube URL")
            return

        # Validate URL (basic check)
        if "youtube.com" not in url and "youtu.be" not in url:
            self.show_error("Please enter a valid YouTube URL")
            return

        # Start transcription in a separate thread
        self.transcribe_button.set_sensitive(False)
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_text("Starting...")
        self.status_label.set_text("Preparing transcription...")

        thread = threading.Thread(target=self.transcribe_video, args=(url,))
        thread.daemon = True
        thread.start()

    def transcribe_video(self, url):
        """Transcribe video in background thread"""
        try:
            # Update progress
            GLib.idle_add(self.update_progress, 0.1, "Checking dependencies...")

            # Check dependencies
            check_dependencies()

            GLib.idle_add(self.update_progress, 0.2, "Downloading content...")

            # Get settings from UI
            output_dir = os.path.expanduser("~/.transcribe-yt/transcripts")

            # Ensure output directory exists
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            txt_path = None
            mp3_path = None
            srt_path = None

            # Step 1: Try to download subtitles first (unless forced to transcribe)
            force_transcribe = self.force_transcribe_check.get_active()
            if not force_transcribe:
                GLib.idle_add(self.update_progress, 0.3, "Downloading subtitles...")
                srt_path = download_subtitles(url, output_dir)
                if srt_path:
                    GLib.idle_add(self.update_progress, 0.4, "Converting subtitles...")
                    txt_path = convert_srt_to_text(srt_path)
                    GLib.idle_add(self.update_status, "✓ Using subtitles instead of audio transcription")

            # Step 2: If no subtitles available or forced transcription, download and transcribe audio
            if txt_path is None:
                GLib.idle_add(self.update_progress, 0.4, "Downloading audio...")
                mp3_path = download_audio(url, output_dir)
                GLib.idle_add(self.update_progress, 0.6, "Transcribing audio...")
                txt_path = transcribe_audio(mp3_path)

            # Step 3: Generate summary
            GLib.idle_add(self.update_progress, 0.7, "Generating summary...")

            model_index = self.model_combo.get_active()
            if model_index == 0:  # DeepSeek
                api_key = self.config.get("deepseek_api_key")
                if not api_key:
                    GLib.idle_add(self.show_error, "DeepSeek API key not set. Please configure it first.")
                    return
                md_path = generate_summary_deepseek(txt_path, api_key)
            else:  # Ollama
                ollama_model = self.config.get("ollama_model", "qwen3:32b")
                md_path = generate_summary_ollama(txt_path, ollama_model)

            # Step 4: Load and display summary
            GLib.idle_add(self.update_progress, 0.9, "Loading summary...")

            with open(md_path, 'r', encoding='utf-8') as f:
                summary_content = f.read()

            # Convert markdown to HTML for display
            html_content = markdown.markdown(summary_content, extensions=['codehilite', 'fenced_code'])

            GLib.idle_add(self.display_summary, html_content, md_path)

            # Step 5: Clean up intermediate files
            GLib.idle_add(self.update_progress, 1.0, "Cleaning up...")
            if mp3_path and os.path.exists(mp3_path):
                os.remove(mp3_path)
            if srt_path and os.path.exists(srt_path):
                os.remove(srt_path)
            if txt_path and os.path.exists(txt_path):
                os.remove(txt_path)

            GLib.idle_add(self.update_progress, 1.0, "Complete!")
            GLib.idle_add(self.update_status, "Transcription completed successfully!")

        except Exception as e:
            GLib.idle_add(self.show_error, f"Error: {str(e)}")
        finally:
            GLib.idle_add(self.transcribe_button.set_sensitive, True)

    def update_progress(self, fraction, text):
        """Update progress bar (called from main thread)"""
        self.progress_bar.set_fraction(fraction)
        self.progress_bar.set_text(text)
        return False

    def update_status(self, text):
        """Update status label (called from main thread)"""
        self.status_label.set_text(text)
        return False

    def display_summary(self, html_content, file_path):
        """Display the summary in the TextView"""
        # Convert HTML back to markdown for display in TextView
        # For now, just display the HTML content as plain text
        buffer = self.summary_textview.get_buffer()
        buffer.set_text(html_content)
        self.status_label.set_text(f"Summary loaded from: {file_path}")
        return False

    def show_error(self, message):
        """Show error dialog"""
        dialog = Gtk.MessageDialog(
            parent=self.window,
            flags=Gtk.DialogFlags.MODAL,
            type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            message_format=message
        )
        dialog.run()
        dialog.destroy()
        return False

    def on_configure_clicked(self, widget):
        """Handle configure button click"""
        dialog = Gtk.Dialog("Configuration", self.window, 0,
                           (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                            Gtk.STOCK_OK, Gtk.ResponseType.OK))

        dialog.set_default_size(400, 200)

        # Create content area
        content_area = dialog.get_content_area()
        content_area.set_spacing(10)

        # API Key entry
        api_key_label = Gtk.Label("DeepSeek API Key:")
        api_key_label.set_halign(Gtk.Align.START)
        content_area.pack_start(api_key_label, False, False, 0)

        api_key_entry = Gtk.Entry()
        api_key_entry.set_placeholder_text("Enter your DeepSeek API key")
        api_key_entry.set_visibility(False)  # Password field
        if self.config.get("deepseek_api_key"):
            api_key_entry.set_text(self.config["deepseek_api_key"])
        content_area.pack_start(api_key_entry, True, True, 0)

        # Ollama model entry
        ollama_label = Gtk.Label("Ollama Model:")
        ollama_label.set_halign(Gtk.Align.START)
        content_area.pack_start(ollama_label, False, False, 0)

        ollama_entry = Gtk.Entry()
        ollama_entry.set_placeholder_text("e.g., qwen3:32b")
        ollama_entry.set_text(self.config.get("ollama_model", "qwen3:32b"))
        content_area.pack_start(ollama_entry, True, True, 0)

        dialog.show_all()

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            # Save configuration
            self.config["deepseek_api_key"] = api_key_entry.get_text()
            self.config["ollama_model"] = ollama_entry.get_text()
            save_config(self.config)
            self.update_config_ui()

        dialog.destroy()

    def on_clear_clicked(self, widget):
        """Handle clear button click"""
        self.set_initial_content()
        self.status_label.set_text("Ready")
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_text("Ready")
        self.url_entry.set_text("")

    def on_window_destroy(self, widget):
        """Handle window close"""
        Gtk.main_quit()

    def run(self):
        """Run the GUI application"""
        self.window.show_all()
        Gtk.main()


def main():
    """Main entry point for GUI application"""
    app = TranscribeYTGUI()
    app.run()


if __name__ == "__main__":
    main()
