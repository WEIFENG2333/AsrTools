# CLAUDE.md - AI Assistant Guide for AsrTools

## Project Overview

AsrTools is a Chinese audio/video speech recognition (ASR) tool that provides both a GUI application and programmatic API for converting audio/video files to subtitles. It leverages free online ASR services from Chinese platforms (Bilibili, JianYing/CapCut, KuaiShou) without requiring local GPU resources.

**Key Features:**
- No GPU required - uses cloud-based ASR services
- PyQt5-based GUI with qfluentwidgets for modern UI
- Multi-threaded batch processing (default 3 concurrent threads)
- Multiple output formats: SRT, TXT, ASS
- Video file support with automatic audio extraction via ffmpeg
- Built-in result caching to avoid redundant API calls

**License:** GPL-3.0

## Codebase Structure

```
AsrTools/
├── asr_gui.py              # Main GUI application entry point
├── example.py              # Simple API usage example
├── requirements.txt        # Python dependencies
├── bk_asr/                 # Core ASR library package
│   ├── __init__.py         # Package exports and transcribe() helper
│   ├── ASRData.py          # Data structures for ASR results & subtitle formats
│   ├── BaseASR.py          # Abstract base class for all ASR engines
│   ├── BcutASR.py          # Bilibili Bcut ASR implementation
│   ├── JianYingASR.py      # JianYing/CapCut ASR implementation
│   ├── KuaiShouASR.py      # KuaiShou ASR implementation
│   └── WhisperASR.py       # OpenAI Whisper API implementation (incomplete)
├── resources/              # Test files and assets
│   ├── test.mp3            # Test audio file
│   ├── test.srt            # Sample SRT output
│   └── main_window-*.png   # GUI screenshots
└── .github/
    └── ISSUE_TEMPLATE/     # GitHub issue templates
```

## Architecture

### Core Components

#### 1. BaseASR (`bk_asr/BaseASR.py`)
Abstract base class providing:
- Audio file loading (supports: flac, m4a, mp3, wav)
- CRC32-based cache key generation
- Thread-safe JSON cache (stored in temp directory)
- Template method pattern: `run()` calls `_run()` then `_make_segments()`

Subclasses must implement:
- `_run() -> dict`: Execute ASR API calls, return raw response
- `_make_segments(resp_data) -> list[ASRDataSeg]`: Parse response to segments

#### 2. ASRData (`bk_asr/ASRData.py`)
Data container for ASR results with conversion methods:
- `ASRDataSeg`: Single segment with text, start_time, end_time (milliseconds)
- `ASRData`: Collection of segments with export methods:
  - `to_srt()`, `to_txt()`, `to_ass()`, `to_lrc()`, `to_json()`
  - `save(path)`: Auto-detect format from file extension

Also provides parsers for importing existing subtitles:
- `from_srt()`, `from_ass()`, `from_vtt()`, `from_youtube_vtt()`, `from_json()`

#### 3. ASR Engine Implementations

| Engine | Class | API Provider | Notes |
|--------|-------|--------------|-------|
| B Interface | `BcutASR` | Bilibili (bcut) | Chunked upload, polling for results |
| J Interface | `JianYingASR` | ByteDance/JianYing | AWS-style auth, external sign service |
| K Interface | `KuaiShouASR` | KuaiShou | Simple single-request API |
| Whisper | `WhisperASR` | OpenAI-compatible | Requires OPENAI_BASE_URL, OPENAI_API_KEY env vars |

#### 4. GUI Application (`asr_gui.py`)
- `MainWindow`: FluentWindow with navigation to ASR and About pages
- `ASRWidget`: Main processing interface with file table, engine selection
- `ASRWorker`: QRunnable for background processing
- `video2audio()`: FFmpeg wrapper for video-to-audio conversion

### Data Flow

```
Audio/Video File → [FFmpeg conversion if needed] → ASR Engine
     ↓
Raw API Response → _make_segments() → ASRData
     ↓
ASRData → to_srt()/to_txt()/to_ass() → Subtitle File
```

## Development Workflows

### Running the Application

**GUI Mode:**
```bash
pip install -r requirements.txt
python asr_gui.py
```

**Programmatic API:**
```python
from bk_asr import BcutASR, JianYingASR, KuaiShouASR

asr = JianYingASR("audio.mp3")
result = asr.run()
print(result.to_srt())
result.save("output.srt")
```

**Quick transcribe helper:**
```python
from bk_asr import transcribe
result = transcribe("audio.mp3", "JianYingASR")
```

### Dependencies

Core (required):
- `requests` - HTTP client for API calls

GUI (optional):
- `PyQt5` - Qt bindings for Python
- `PyQt-Fluent-Widgets` - Modern fluent design widgets

External tools:
- `ffmpeg` - Required for video file processing (must be in PATH)

### Adding a New ASR Engine

1. Create `bk_asr/NewEngineASR.py`
2. Inherit from `BaseASR`
3. Implement:
   ```python
   class NewEngineASR(BaseASR):
       def _run(self) -> dict:
           # Call external API, return raw response
           pass

       def _make_segments(self, resp_data: dict) -> list[ASRDataSeg]:
           # Parse response into ASRDataSeg list
           return [ASRDataSeg(text, start_ms, end_ms) for ...]
   ```
4. Export in `bk_asr/__init__.py`
5. Add to GUI engine dropdown in `asr_gui.py`

## Key Conventions

### Code Style
- Language: Python 3.8+
- Comments/docstrings: Chinese (project is Chinese-focused)
- Type hints: Used sparingly (Union types for path parameters)
- Logging: Use `logging` module, configured in entry points

### Time Units
- All timestamps are in **milliseconds** (int)
- Conversion helpers in `ASRDataSeg`:
  - `_ms_to_srt_time()`: HH:MM:SS,mmm
  - `_ms_to_ass_ts()`: H:MM:SS.cc (centiseconds)
  - `_ms_to_lrc_time()`: MM:SS.ss

### Caching
- Cache file: `{tempdir}/bk_asr/asr_cache.json`
- Cache key format: `{ClassName}-{crc32_hex}[-{extra_params}]`
- Auto-cleanup when cache exceeds 10MB
- Thread-safe with `threading.Lock`

### Error Handling
- ASR failures emit `errno` signal in GUI (file_path, error_message)
- BaseASR uses assertions for file validation
- Network errors typically raise exceptions (not silently caught)

### GUI Patterns
- Qt signals for cross-thread communication (`WorkerSignals`)
- `QThreadPool` with configurable max threads (default: 3)
- Status colors: gray (pending), orange (processing), green (done), red (error)
- File paths stored in `Qt.UserRole` data of table items

## Common Tasks

### Testing ASR Engines
```python
# Quick test
from bk_asr import JianYingASR
asr = JianYingASR("resources/test.mp3")
result = asr.run()
print(result.to_srt())
```

### Converting Subtitle Formats
```python
from bk_asr.ASRData import from_srt, ASRData

# Load existing SRT
asr_data = from_srt(open("input.srt").read())

# Convert to other formats
asr_data.save("output.ass")
asr_data.save("output.txt")
```

### Debugging API Issues
- Enable logging: `logging.basicConfig(level=logging.INFO)`
- Check cache: `{tempdir}/bk_asr/asr_cache.json`
- BcutASR logs upload progress with partition details
- JianYingASR uses external sign service at `asrtools-update.bkfeng.top/sign`

## External Services

The project relies on these external APIs (subject to change):

| Service | Base URL | Authentication |
|---------|----------|----------------|
| Bilibili Bcut | `member.bilibili.com/x/bcut/rubick-interface` | None (anonymous) |
| JianYing | `lv-pc-api-sinfonlinec.ulikecam.com` | Device ID + signature |
| KuaiShou | `ai.kuaishou.com/api/effects/subtitle_generate` | None (anonymous) |
| JianYing Sign Service | `asrtools-update.bkfeng.top/sign` | Project-specific |

## Related Projects

- [VideoCaptioner](https://github.com/WEIFENG2333/VideoCaptioner) - Advanced version with LLM-powered subtitle optimization, translation, and video embedding
