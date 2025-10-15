# YouTube Video Transcription and Summarization Tool

This Python script downloads YouTube videos as MP3, transcribes them using NVIDIA Parakeet (or downloads subtitles directly when available), and generates summaries using either DeepSeek API or local Ollama models.

## Quick Start

```bash
# Clone or download this project
cd transcribe-yt

# Install dependencies
./setup.sh

# activate environment
source venv/bin/activate

# Run with a YouTube URL
python3 transcribe_yt.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

## GUI Usage

For a user-friendly graphical interface, use the GTK GUI:

```bash
# Run the GUI
python3 run_gui.py
```

## macOS App Bundle

Create a distributable .app bundle for macOS:

### Quick Start
```bash
# Make the script executable and run it
chmod +x create_app.sh
./create_app.sh
```

### Manual Packaging

#### Option 1: Simple .app Bundle (Development)
```bash
# Create a simple .app bundle with virtual environment
python3 package_app.py
```

#### Option 2: PyInstaller Bundle (Distribution)
```bash
# Create a standalone .app bundle using PyInstaller
python3 build_app.py
```

### App Bundle Features
- **Standalone Application**: No need to install Python or dependencies
- **macOS Integration**: Proper .app bundle with Info.plist
- **Document Support**: Can handle YouTube URLs from Finder
- **High Resolution**: Supports Retina displays
- **Distribution Ready**: Can be zipped and shared

### Distribution
```bash
# Create a distributable zip file
zip -r TranscribeYouTube.zip TranscribeYouTube.app
```

The GUI provides:
- Easy URL input with validation
- Real-time progress tracking
- Configuration management for API keys
- Markdown summary display
- Model selection (DeepSeek API or Ollama)
- Output directory customization

### GUI Features

1. **Input Section**: Enter YouTube URLs and configure output settings
2. **Progress Tracking**: Real-time progress bar and status updates
3. **Summary Display**: View generated summaries in a scrollable text area
4. **Configuration**: Set up API keys and model preferences
5. **Error Handling**: User-friendly error messages and dialogs

## Features

- **Command Line Interface**: Full-featured CLI for automated processing
- **Graphical User Interface**: Easy-to-use GTK GUI for interactive transcription
- Download YouTube videos as MP3 audio
- Download subtitles directly when available (faster than audio transcription)
- Transcribe audio to text using NVIDIA Parakeet (with punctuation and capitalization)
- Generate summaries using DeepSeek API or local Ollama models
- Automatic file naming with timestamps
- Support for custom output directories
- Error handling and progress reporting
- Configuration management for API keys and settings

## Prerequisites

### Required Tools
- `yt-dlp` - for downloading YouTube videos
- `ffmpeg` - for audio format conversion
- Python 3.7+ with `requests` and `nemo_toolkit[asr]` libraries

### Optional Dependencies
- DeepSeek API key (for DeepSeek summaries)
- Ollama (for local model summaries)

## Installation

### Method 1: Automated Setup (Recommended)

1. Run the setup script:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

### Method 2: Manual Setup

1. Install the required system tools:

   **On macOS (using Homebrew):**
   ```bash
   # Install yt-dlp and ffmpeg
   brew install yt-dlp ffmpeg
   ```

   **On Linux/Ubuntu:**
   ```bash
   # Install yt-dlp
   pipx install yt-dlp

   # Install ffmpeg
   sudo apt update && sudo apt install ffmpeg
   ```

   **On Windows (using WSL or PowerShell):**
   ```powershell
   # Install yt-dlp
   pip install yt-dlp

   # Install ffmpeg - download from https://ffmpeg.org/download.html
   # or use chocolatey: choco install ffmpeg
   ```

2. Set up Python dependencies:
   ```bash
   # Create and activate virtual environment
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install Python dependencies
   pip install -r requirements.txt
   ```

3. (Optional) Set up API keys:
   ```bash
   # For DeepSeek API - add to your shell profile (.bashrc, .zshrc, etc.)
   echo 'export DEEPSEEK_API_KEY="your-api-key-here"' >> ~/.zshrc
   source ~/.zshrc
   ```

### Setting Up Ollama (for Local Model Summaries)

If you want to use local models instead of the DeepSeek API:

1. **Install Ollama:**
   ```bash
   # macOS/Linux
   curl -fsSL https://ollama.ai/install.sh | sh

   # Windows
   # Download from https://ollama.ai/download
   ```

2. **Pull a model:**
   ```bash
   # Pull a model (this may take a while depending on model size)
   ollama pull qwen3:32b

   # Or try a smaller model for faster results
   ollama pull qwen3:1.7b
   ```

3. **Start Ollama service:**
   ```bash
   # The service should start automatically after installation
   # If not, run:
   ollama serve
   ```

## Usage

### Basic Usage

Make sure to activate the virtual environment first:
```bash
source venv/bin/activate
```

Then run the tool:
```bash
# Using DeepSeek API (requires DEEPSEEK_API_KEY environment variable)
python3 transcribe_yt.py "https://www.youtube.com/watch?v=VIDEO_ID"

# Using local Ollama model
python3 transcribe_yt.py --model ollama "https://www.youtube.com/watch?v=VIDEO_ID"

# Specify custom output directory
python3 transcribe_yt.py --output-dir ./transcriptions "https://www.youtube.com/watch?v=VIDEO_ID"

# Use different Ollama model
python3 transcribe_yt.py --model ollama --ollama-model "qwen3:1.7b" "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Command Line Options

- `url`: YouTube video URL (required)
- `--output-dir, -o`: Output directory (default: `transcripts/`)
- `--model`: Summary model to use: `deepseek` or `ollama` (default: `deepseek`)
- `--ollama-model`: Ollama model name (default: `qwen3:32b`)
- `--force-transcribe`: Force audio transcription even if subtitles are available

## Workflow

The tool follows this smart 4-step process:

1. **Check Subtitles**: Attempts to download English subtitles directly using `yt-dlp` (faster and more accurate)
2. **Fallback to Audio**: If no subtitles available, downloads YouTube video as MP3 using `yt-dlp`
3. **Transcribe**: Converts audio to text using NVIDIA Parakeet (only if no subtitles available)
4. **Summarize**: Generates a summary using either DeepSeek API or local Ollama model

## Output Files

The script generates a summary markdown file for each video:

1. `[video_title]_[timestamp].md` - Generated summary (only file kept)

### Example Output Structure

```
transcripts/
└── Introduction_to_AI_20241013_143022.md
```

All files are automatically organized under the `transcripts/` folder by default.

## Examples

### Example 1: Quick Transcription with DeepSeek
```bash
# Make sure DEEPSEEK_API_KEY is set
export DEEPSEEK_API_KEY="your-api-key-here"

# Transcribe and summarize
python3 transcribe_yt.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### Example 2: Using Local Ollama Model
```bash
# Use local Ollama with default model
python3 transcribe_yt.py --model ollama "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Use specific Ollama model
python3 transcribe_yt.py --model ollama --ollama-model "qwen3:1.7b" "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### Example 3: Organized Output
```bash
# Save all files to a dedicated directory
python3 transcribe_yt.py --output-dir ~/transcriptions "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### Example 4: Force Audio Transcription
```bash
# Force audio transcription even if subtitles are available
python3 transcribe_yt.py --force-transcribe "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

## Testing

Run the basic test to verify everything is working:

```bash
python3 test_basic.py
```

## Troubleshooting

### Common Issues

1. **yt-dlp not found**:
   - Install using: `brew install yt-dlp` (macOS) or `pipx install yt-dlp` (Linux)
   - Or run the setup script: `./setup.sh`

2. **ffmpeg not found**:
   - Install using: `brew install ffmpeg` (macOS) or `sudo apt install ffmpeg` (Linux)
   - On Windows, download from https://ffmpeg.org/download.html

3. **nemo_toolkit not installed**:
   ```bash
   # Activate virtual environment and install
   source venv/bin/activate
   pip install -U nemo_toolkit["asr"]
   ```

4. **DEEPSEEK_API_KEY not set**:
   ```bash
   export DEEPSEEK_API_KEY="your-api-key-here"
   # Add to your shell profile for persistence
   echo 'export DEEPSEEK_API_KEY="your-api-key-here"' >> ~/.zshrc
   ```

5. **Ollama connection refused**:
   - Make sure Ollama is installed and running: `ollama serve`
   - Check if service is running: `curl http://localhost:11434/api/tags`

6. **Python dependencies missing**:
   ```bash
   # Activate virtual environment and install
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Error Messages

- **"Failed to download audio"**: Check YouTube URL, internet connection, and yt-dlp installation
- **"Failed to convert audio to WAV"**: Verify ffmpeg installation and audio file integrity
- **"Failed to transcribe audio"**: Verify NVIDIA Parakeet installation and audio file integrity
- **"Failed to generate summary"**: Check API key validity or Ollama service status
- **"ModuleNotFoundError: No module named 'requests'"**: Activate virtual environment and install dependencies

### Performance Tips

- **For faster results**: Use smaller Ollama models like `qwen3:1.7b`
- **For better quality**: Use larger models like `qwen3:32b` or DeepSeek API
- **Long videos**: Consider splitting long videos into segments for better transcription accuracy

## License

This project is open source and available under the MIT License.

## Contributing

Feel free to submit issues and pull requests to improve this tool!