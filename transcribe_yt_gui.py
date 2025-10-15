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
import signal
import markdown
import re
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

        # Create main content area with transcription list and summary
        self.create_content_area()

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

    def create_content_area(self):
        """Create the main content area with transcription list and summary"""
        # Create horizontal box for side-by-side layout
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        content_box.set_margin_bottom(10)
        self.main_box.pack_start(content_box, True, True, 0)

        # Create transcription list section
        self.create_transcription_list_section(content_box)

        # Create summary section
        self.create_summary_section(content_box)

    def create_transcription_list_section(self, parent_box):
        """Create the transcription list section"""
        # Transcription list frame
        list_frame = Gtk.Frame(label="Existing Transcriptions")
        list_frame.set_size_request(300, 400)
        parent_box.pack_start(list_frame, False, False, 0)

        # Create vertical box for list content
        list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        list_box.set_margin_left(10)
        list_box.set_margin_right(10)
        list_box.set_margin_top(10)
        list_box.set_margin_bottom(10)
        list_frame.add(list_box)

        # Refresh button
        refresh_button = Gtk.Button(label="Refresh List")
        refresh_button.connect("clicked", self.on_refresh_transcriptions)
        list_box.pack_start(refresh_button, False, False, 0)

        # Create scrolled window for the list
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        list_box.pack_start(scrolled_window, True, True, 0)

        # Create list store for transcriptions
        self.transcription_store = Gtk.ListStore(str, str, str)  # title, date, file_path

        # Create tree view
        self.transcription_tree = Gtk.TreeView(model=self.transcription_store)
        self.transcription_tree.set_headers_visible(True)
        self.transcription_tree.connect("row-activated", self.on_transcription_selected)

        # Create columns
        title_col = Gtk.TreeViewColumn("Title", Gtk.CellRendererText(), text=0)
        title_col.set_expand(True)
        self.transcription_tree.append_column(title_col)

        date_col = Gtk.TreeViewColumn("Date", Gtk.CellRendererText(), text=1)
        date_col.set_min_width(120)
        self.transcription_tree.append_column(date_col)

        scrolled_window.add(self.transcription_tree)

        # Load initial transcriptions
        self.load_transcriptions()

    def create_summary_section(self, parent_box):
        """Create the summary section with TextView for rich text rendering"""
        # Summary frame
        summary_frame = Gtk.Frame(label="Summary")
        parent_box.pack_start(summary_frame, True, True, 0)

        # Create TextView for summary display
        self.summary_textview = Gtk.TextView()
        self.summary_textview.set_editable(False)
        self.summary_textview.set_wrap_mode(Gtk.WrapMode.WORD)
        self.summary_textview.set_margin_left(10)
        self.summary_textview.set_margin_right(10)
        self.summary_textview.set_margin_top(10)
        self.summary_textview.set_margin_bottom(10)

        # Set up font
        font_desc = Pango.FontDescription("sans-serif 12")
        self.summary_textview.modify_font(font_desc)

        # Set up text tags for rich formatting
        self.setup_text_tags()

        # Create scrolled window for the textview
        self.summary_scrolled = Gtk.ScrolledWindow()
        self.summary_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.summary_scrolled.add(self.summary_textview)

        summary_frame.add(self.summary_scrolled)

        # Set initial content
        self.set_initial_content()

    def setup_text_tags(self):
        """Set up text tags for rich formatting"""
        buffer = self.summary_textview.get_buffer()

        # Bold tag
        buffer.create_tag("bold", weight=Pango.Weight.BOLD)

        # Italic tag
        buffer.create_tag("italic", style=Pango.Style.ITALIC)

        # Code tag
        buffer.create_tag("code",
                         family="monospace",
                         background="#f4f4f4",
                         foreground="#333333")

        # Large tag for H1
        buffer.create_tag("large",
                        weight=Pango.Weight.BOLD,
                        scale=1.3)

        # Medium tag for H2
        buffer.create_tag("medium",
                         weight=Pango.Weight.BOLD,
                         scale=1.1)

        # Header tag
        buffer.create_tag("header",
                         weight=Pango.Weight.BOLD,
                         scale=1.2,
                         foreground="#2c3e50")

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
• Rich text formatting support
"""
        buffer = self.summary_textview.get_buffer()
        buffer.set_text(initial_text)

        # Apply formatting to the initial content
        self.apply_initial_formatting()

    def apply_initial_formatting(self):
        """Apply formatting to the initial content"""
        buffer = self.summary_textview.get_buffer()
        start_iter = buffer.get_start_iter()
        end_iter = buffer.get_end_iter()

        # Format the title
        title_start = buffer.get_iter_at_offset(0)
        title_end = buffer.get_iter_at_offset(17)  # "Transcribe YouTube"
        buffer.apply_tag_by_name("large", title_start, title_end)

        # Format the "Features:" header
        features_start = buffer.get_iter_at_offset(buffer.get_text(start_iter, end_iter, False).find("Features:"))
        features_end = buffer.get_iter_at_offset(features_start.get_offset() + 9)
        buffer.apply_tag_by_name("header", features_start, features_end)

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
                # Use default chunking parameters for GUI (5min chunks, 30s overlap)
                txt_path = transcribe_audio(mp3_path, chunk_duration=300, overlap_duration=30)

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

            # Refresh the transcription list to show the new transcription
            GLib.idle_add(self.load_transcriptions)

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
        """Display the summary in the TextView with HTML rendering"""
        # Render HTML content directly with rich formatting
        self.render_html_content(html_content)

        self.status_label.set_text(f"Summary loaded from: {file_path}")
        return False

    def render_html_content(self, html_content):
        """Render HTML content directly in the TextView with proper formatting"""
        buffer = self.summary_textview.get_buffer()
        buffer.set_text("")  # Clear existing content

        # Use BeautifulSoup for proper HTML parsing
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            self.render_soup_element(buffer, soup)
        except ImportError:
            # Fallback to simple text extraction if BeautifulSoup is not available
            import re
            # Remove HTML tags and get plain text
            text = re.sub(r'<[^>]+>', '', html_content)
            buffer.set_text(text)

    def render_soup_element(self, buffer, element):
        """Recursively render BeautifulSoup elements with formatting"""
        if hasattr(element, 'name') and element.name is not None:
            # This is a tag
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                self.render_header(buffer, element)
            elif element.name in ['strong', 'b']:
                self.render_bold(buffer, element)
            elif element.name in ['em', 'i']:
                self.render_italic(buffer, element)
            elif element.name == 'code':
                self.render_code(buffer, element)
            elif element.name == 'p':
                self.render_paragraph(buffer, element)
            elif element.name in ['ul', 'ol']:
                self.render_list(buffer, element)
            elif element.name == 'li':
                self.render_list_item(buffer, element)
            elif element.name == 'br':
                buffer.insert(buffer.get_end_iter(), '\n')
            else:
                # For other tags, just render their content
                for child in element.children:
                    self.render_soup_element(buffer, child)
        else:
            # This is text content (NavigableString)
            text = str(element).strip()
            if text:
                buffer.insert(buffer.get_end_iter(), text)

    def render_header(self, buffer, element):
        """Render a header element with appropriate formatting"""
        text = element.get_text().strip()
        if text:
            start_iter = buffer.get_end_iter()
            buffer.insert(start_iter, text + '\n')

            # Apply formatting
            end_iter = buffer.get_end_iter()
            start_iter = end_iter.copy()
            start_iter.backward_chars(len(text) + 1)

            if element.name == 'h1':
                buffer.apply_tag_by_name("large", start_iter, end_iter)
            elif element.name == 'h2':
                buffer.apply_tag_by_name("medium", start_iter, end_iter)
            else:
                buffer.apply_tag_by_name("header", start_iter, end_iter)

    def render_bold(self, buffer, element):
        """Render bold text with formatting"""
        text = element.get_text().strip()
        if text:
            start_iter = buffer.get_end_iter()
            buffer.insert(start_iter, text)

            # Apply bold formatting
            end_iter = buffer.get_end_iter()
            start_iter = end_iter.copy()
            start_iter.backward_chars(len(text))
            buffer.apply_tag_by_name("bold", start_iter, end_iter)

    def render_italic(self, buffer, element):
        """Render italic text with formatting"""
        text = element.get_text().strip()
        if text:
            start_iter = buffer.get_end_iter()
            buffer.insert(start_iter, text)

            # Apply italic formatting
            end_iter = buffer.get_end_iter()
            start_iter = end_iter.copy()
            start_iter.backward_chars(len(text))
            buffer.apply_tag_by_name("italic", start_iter, end_iter)

    def render_code(self, buffer, element):
        """Render code with formatting"""
        text = element.get_text().strip()
        if text:
            start_iter = buffer.get_end_iter()
            buffer.insert(start_iter, text)

            # Apply code formatting
            end_iter = buffer.get_end_iter()
            start_iter = end_iter.copy()
            start_iter.backward_chars(len(text))
            buffer.apply_tag_by_name("code", start_iter, end_iter)

    def render_paragraph(self, buffer, element):
        """Render a paragraph"""
        text = element.get_text().strip()
        if text:
            buffer.insert(buffer.get_end_iter(), text + '\n\n')

    def render_list(self, buffer, element):
        """Render a list"""
        for child in element.children:
            if hasattr(child, 'name') and child.name == 'li':
                self.render_list_item(buffer, child)

    def render_list_item(self, buffer, element):
        """Render a list item"""
        text = element.get_text().strip()
        if text:
            buffer.insert(buffer.get_end_iter(), '• ' + text + '\n')

    def html_to_formatted_text(self, html_content):
        """Convert HTML to formatted text for display in TextView"""
        # Remove HTML tags and convert to formatted text
        text = html_content

        # Convert common HTML elements to text formatting
        text = re.sub(r'<h1[^>]*>(.*?)</h1>', r'\n# \1\n', text, flags=re.DOTALL)
        text = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n## \1\n', text, flags=re.DOTALL)
        text = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n### \1\n', text, flags=re.DOTALL)
        text = re.sub(r'<h4[^>]*>(.*?)</h4>', r'\n#### \1\n', text, flags=re.DOTALL)
        text = re.sub(r'<h5[^>]*>(.*?)</h5>', r'\n##### \1\n', text, flags=re.DOTALL)
        text = re.sub(r'<h6[^>]*>(.*?)</h6>', r'\n###### \1\n', text, flags=re.DOTALL)

        # Convert paragraphs
        text = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', text, flags=re.DOTALL)

        # Convert lists
        text = re.sub(r'<ul[^>]*>(.*?)</ul>', r'\1', text, flags=re.DOTALL)
        text = re.sub(r'<ol[^>]*>(.*?)</ol>', r'\1', text, flags=re.DOTALL)
        text = re.sub(r'<li[^>]*>(.*?)</li>', r'• \1\n', text, flags=re.DOTALL)

        # Convert emphasis
        text = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', text, flags=re.DOTALL)
        text = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', text, flags=re.DOTALL)
        text = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', text, flags=re.DOTALL)
        text = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', text, flags=re.DOTALL)

        # Convert code
        text = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', text, flags=re.DOTALL)
        text = re.sub(r'<pre[^>]*>(.*?)</pre>', r'\n```\n\1\n```\n', text, flags=re.DOTALL)

        # Convert blockquotes
        text = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', r'\n> \1\n', text, flags=re.DOTALL)

        # Convert links
        text = re.sub(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', r'[\2](\1)', text, flags=re.DOTALL)

        # Convert line breaks
        text = re.sub(r'<br[^>]*>', r'\n', text)

        # Remove remaining HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Clean up extra whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        text = text.strip()

        return text

    def apply_rich_formatting(self, buffer):
        """Apply rich formatting to the text buffer"""
        start_iter = buffer.get_start_iter()
        end_iter = buffer.get_end_iter()
        text = buffer.get_text(start_iter, end_iter, False)

        # Find and format headers
        for match in re.finditer(r'^(#{1,6})\s+(.+)$', text, re.MULTILINE):
            header_level = len(match.group(1))
            header_text = match.group(2)

            # Find the position of this header in the buffer
            header_start = buffer.get_iter_at_offset(match.start())
            header_end = buffer.get_iter_at_offset(match.end())

            # Apply formatting based on header level
            if header_level == 1:
                buffer.apply_tag_by_name("large", header_start, header_end)
            elif header_level == 2:
                buffer.apply_tag_by_name("medium", header_start, header_end)
            else:
                buffer.apply_tag_by_name("header", header_start, header_end)

        # Find and format bold text (**text**)
        for match in re.finditer(r'\*\*(.*?)\*\*', text):
            bold_start = buffer.get_iter_at_offset(match.start())
            bold_end = buffer.get_iter_at_offset(match.end())
            buffer.apply_tag_by_name("bold", bold_start, bold_end)

        # Find and format italic text (*text*)
        for match in re.finditer(r'\*(.*?)\*', text):
            italic_start = buffer.get_iter_at_offset(match.start())
            italic_end = buffer.get_iter_at_offset(match.end())
            buffer.apply_tag_by_name("italic", italic_start, italic_end)

        # Find and format code (`text`)
        for match in re.finditer(r'`([^`]+)`', text):
            code_start = buffer.get_iter_at_offset(match.start())
            code_end = buffer.get_iter_at_offset(match.end())
            buffer.apply_tag_by_name("code", code_start, code_end)


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
        return True

    def run(self):
        """Run the GUI application"""
        self.window.show_all()
        try:
            Gtk.main()
        except KeyboardInterrupt:
            Gtk.main_quit()
        finally:
            # Ensure the application exits cleanly
            import sys
            sys.exit(0)

    def load_transcriptions(self):
        """Load existing transcriptions from the transcripts directory"""
        transcripts_dir = Path.home() / ".transcribe-yt" / "transcripts"
        if not transcripts_dir.exists():
            return

        # Clear existing entries
        self.transcription_store.clear()

        # Find all markdown files
        md_files = list(transcripts_dir.glob("*.md"))
        md_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)  # Sort by modification time, newest first

        for md_file in md_files:
            try:
                # Extract title from filename (remove timestamp and .md extension)
                filename = md_file.stem
                # Remove timestamp pattern from end of filename
                title = re.sub(r'_\d{8}_\d{6}$', '', filename)

                # Get file modification time
                import datetime
                mtime = datetime.datetime.fromtimestamp(md_file.stat().st_mtime)
                date_str = mtime.strftime("%Y-%m-%d %H:%M")

                # Add to store
                self.transcription_store.append([title, date_str, str(md_file)])
            except Exception as e:
                print(f"Error loading transcription {md_file}: {e}")

    def on_refresh_transcriptions(self, button):
        """Refresh the transcription list"""
        self.load_transcriptions()

    def on_transcription_selected(self, tree_view, path, column):
        """Handle transcription selection"""
        print(f"Transcription selected: path={path}")
        model = tree_view.get_model()
        tree_iter = model.get_iter(path)
        if tree_iter:
            file_path = model.get_value(tree_iter, 2)
            print(f"Loading transcription: {file_path}")
            self.load_transcription_summary(file_path)

    def load_transcription_summary(self, file_path):
        """Load and display a transcription summary"""
        try:
            print(f"Loading file: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()

            print(f"File content length: {len(markdown_content)} characters")
            # Convert markdown to HTML
            html_content = markdown.markdown(markdown_content)
            print(f"HTML content length: {len(html_content)} characters")

            # Display in the summary viewer
            self.display_summary(html_content, file_path)
            print("Summary displayed successfully")

        except Exception as e:
            print(f"Error loading transcription {file_path}: {e}")
            self.status_label.set_text(f"Error loading transcription: {e}")


def main():
    """Main entry point for GUI application"""
    # Set up signal handlers for clean exit
    def signal_handler(signum, frame):
        print("\nReceived interrupt signal. Exiting...")
        Gtk.main_quit()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    app = TranscribeYTGUI()
    app.run()


if __name__ == "__main__":
    main()
