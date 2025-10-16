# YouTube Video Transcription and Summarization Tool

A Python tool that downloads YouTube videos, transcribes them using NVIDIA Parakeet (or subtitles when available), and generates summaries using DeepSeek API or local Ollama models.

## Quick Start

```bash
# 1. Setup (one-time)
./setup.sh
source venv/bin/activate

# 2. Run with YouTube URL
python3 transcribe_yt.py "https://www.youtube.com/watch?v=VIDEO_ID"

# 3. Or use the GUI
python3 run_gui.py
```

## Features

- **Smart Processing**: Downloads subtitles when available, falls back to audio transcription
- **Memory Optimized**: Handles large files with automatic chunking
- **Multiple Models**: DeepSeek API or local Ollama models
- **GUI Interface**: Easy-to-use graphical interface

## Installation

### Automated Setup (Recommended)
```bash
chmod +x setup.sh
./setup.sh
```

### Manual Setup
1. **Install system dependencies:**
   ```bash
   # macOS
   brew install yt-dlp ffmpeg

   # Linux
   pipx install yt-dlp
   sudo apt install ffmpeg
   ```

2. **Install Python dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure API keys (optional):**
   ```bash
   # For DeepSeek API
   export DEEPSEEK_API_KEY="your-api-key-here"

   # For Ollama (local models)
   curl -fsSL https://ollama.ai/install.sh | sh
   ollama pull vicuna:7b
   ```

## Usage

### Command Line
```bash
# Basic usage
python3 transcribe_yt.py "https://www.youtube.com/watch?v=VIDEO_ID"

# With local Ollama model
python3 transcribe_yt.py --model ollama "https://www.youtube.com/watch?v=VIDEO_ID"

# Custom output directory
python3 transcribe_yt.py --output-dir ./transcriptions "https://www.youtube.com/watch?v=VIDEO_ID"

# Memory optimization for large files
python3 transcribe_yt.py --chunk-duration 600 --overlap-duration 60 "https://www.youtube.com/watch?v=VIDEO_ID"
```

### GUI Interface
```bash
python3 run_gui.py
```

### macOS App Bundle
```bash
# Create distributable .app bundle
./create_app.sh

# Or manual packaging
python3 build_app.py
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `url` | YouTube video URL (required) | - |
| `--output-dir, -o` | Output directory | `~/.transcribe-yt/transcripts` |
| `--model` | Summary model: `deepseek` or `ollama` | `deepseek` |
| `--ollama-model` | Ollama model name | `vicuna:7b` |
| `--force-transcribe` | Force audio transcription | `false` |
| `--chunk-duration` | Audio chunk size (seconds) | `300` |
| `--overlap-duration` | Chunk overlap (seconds) | `30` |

## Configuration

Set default settings:
```bash
# Set API key
python3 transcribe_yt.py --set-api-key "your-api-key"

# Set chunk duration
python3 transcribe_yt.py --set-chunk-duration 600

# View current settings
python3 transcribe_yt.py --show-config
```

## Output

Creates a single markdown file per video:
```
transcripts/
└── Video_Title_20241013_143022.md
```

## Examples

### DeepSeek API
```bash
export DEEPSEEK_API_KEY="your-key"
python3 transcribe_yt.py "https://www.youtube.com/watch?v=example"
```

### Local Ollama
```bash
python3 transcribe_yt.py --model ollama "https://www.youtube.com/watch?v=example"
```

### Large Files
```bash
python3 transcribe_yt.py --chunk-duration 600 "https://www.youtube.com/watch?v=long-video"
```

## Troubleshooting

### Common Issues
- **yt-dlp not found**: Run `./setup.sh` or install manually
- **ffmpeg not found**: Install via package manager
- **nemo_toolkit not installed**: `pip install -U nemo_toolkit["asr"]`
- **API key issues**: Set `DEEPSEEK_API_KEY` environment variable
- **Ollama connection**: Run `ollama serve`

### Performance Tips
- Use smaller models (`vicuna:7b`) for faster results
- Use larger models (`qwen3:32b`) for better quality
- Adjust chunk size for your system's memory

## Testing

```bash
python3 test_basic.py
```

## License

MIT License - feel free to contribute!