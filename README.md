# YouTube Video Transcription and Summarization Tool

This Python script downloads YouTube videos as MP3, transcribes them using WhisperX, and generates summaries using either DeepSeek API or local Ollama models.

## Quick Start

```bash
# Clone or download this project
cd transcribe-yt

# Install dependencies
./setup.sh

# Run with a YouTube URL
python3 transcribe_yt.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

## Features

- Download YouTube videos as MP3 audio
- Transcribe audio to text using WhisperX
- Generate summaries using DeepSeek API or local Ollama models
- Automatic file naming with timestamps
- Support for custom output directories
- Error handling and progress reporting

## Prerequisites

### Required Tools
- `yt-dlp` - for downloading YouTube videos
- `uvx` - for running WhisperX
- Python 3.7+ with `requests` library

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
   # Install yt-dlp
   brew install yt-dlp

   # Install uv (for uvx)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   **On Linux/Ubuntu:**
   ```bash
   # Install yt-dlp
   pipx install yt-dlp

   # Install uv
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   **On Windows (using WSL or PowerShell):**
   ```powershell
   # Install yt-dlp
   pip install yt-dlp

   # Install uv
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
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

## Workflow

The tool follows this 4-step process:

1. **Download**: Downloads YouTube video as MP3 using `yt-dlp`
2. **Transcribe**: Converts audio to text using `whisperx`
3. **Summarize**: Generates a summary using either DeepSeek API or local Ollama model

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

2. **uvx not found**:
   - Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Make sure `~/.cargo/bin` is in your PATH

3. **DEEPSEEK_API_KEY not set**:
   ```bash
   export DEEPSEEK_API_KEY="your-api-key-here"
   # Add to your shell profile for persistence
   echo 'export DEEPSEEK_API_KEY="your-api-key-here"' >> ~/.zshrc
   ```

4. **Ollama connection refused**:
   - Make sure Ollama is installed and running: `ollama serve`
   - Check if service is running: `curl http://localhost:11434/api/tags`

5. **Python dependencies missing**:
   ```bash
   # Activate virtual environment and install
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Error Messages

- **"Failed to download audio"**: Check YouTube URL, internet connection, and yt-dlp installation
- **"Failed to transcribe audio"**: Verify WhisperX installation and audio file integrity
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