# Whisper STT Local

> Local speech-to-text using [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2). No cloud, no API keys, no PyTorch.

**Version 1.1.0** | [Changelog](CHANGELOG.md) | Part of [VoxBox](https://github.com/mishandledservitor/voxbox)

---

## Table of Contents

- [Quick Start](#quick-start)
- [Setup](#setup)
- [Usage](#usage)
  - [Command Line](#command-line)
  - [Interactive Mode](#interactive-mode)
  - [Inbox Workflow (Batch Transcription)](#inbox-workflow-batch-transcription)
  - [Microphone Recording](#microphone-recording)
- [Models](#models)
  - [Model Catalog](#model-catalog)
  - [Choosing a Model](#choosing-a-model)
- [Output Formats](#output-formats)
- [Supported Audio Formats](#supported-audio-formats)
- [CLI Reference](#cli-reference)
- [How It Works](#how-it-works)
- [Platform Notes](#platform-notes)
- [Troubleshooting](#troubleshooting)
- [Uninstall](#uninstall)
- [File Manifest](#file-manifest)

---

## Quick Start

```bash
chmod +x setup_whisper.sh
./setup_whisper.sh
./whisper recording.mp3
```

---

## Setup

### Prerequisites

- macOS (Intel or Apple Silicon)
- Python 3.10+
- ~460 MB disk space for the default model (`small`)
- Internet for initial setup only

### Installation

```bash
chmod +x setup_whisper.sh
./setup_whisper.sh
```

The setup script runs four steps:

1. **Homebrew** — checks for Homebrew, installs if missing
2. **Python** — verifies Python 3.10+, installs via Homebrew if needed
3. **Python environment** — creates a venv, installs `faster-whisper`, `sounddevice`, `soundfile`, `numpy`
4. **Model download** — pre-downloads the default `small` model (~460 MB)

Everything is installed in the same directory. Models are cached in `~/.cache/huggingface/hub/` and shared across projects.

### Verifying Installation

```bash
./whisper --list-models
```

If this prints the model catalog, you're good to go.

---

## Usage

### Command Line

```bash
# Transcribe and print to terminal
./whisper recording.mp3

# Choose a model
./whisper -m medium interview.wav
./whisper -m tiny quick-note.m4a
./whisper -m large-v3 important-meeting.wav

# Force language (skip auto-detection)
./whisper -l en podcast.mp3
./whisper -l ja japanese-audio.wav
./whisper -l es spanish-interview.m4a

# Save as SRT subtitles
./whisper -o subtitles.srt podcast.mp3

# Save as WebVTT
./whisper -o captions.vtt -l en talk.m4a

# Save as JSON (includes timestamps and metadata)
./whisper -o transcript.json interview.wav

# Save as plain text
./whisper -o transcript.txt meeting.mp3

# Transcribe without printing (just save)
./whisper --no-print -o output.txt recording.mp3

# Batch transcribe inbox
./whisper --inbox
```

### Interactive Mode

Launch with no arguments:

```bash
./whisper
```

Interactive commands:

```
/inbox             — transcribe all files in inbox/
/model medium      — switch model
/lang en           — set language (or 'auto' for auto-detect)
/format srt        — set output format: text, srt, vtt, json
/record 15         — record from microphone (seconds)
/models            — list all models
/quit              — exit
```

Drop a file path at the prompt to transcribe it:

```
  ▶ /path/to/recording.mp3
  🎤 File: recording.mp3 (12.4 MB)
  🌐 Language: auto-detect
     Detected: en (98% confidence)
     ┃██████████████████████████████┃ 100%  23s  done!
  ✅ Transcribed 3m 42s of audio in 23s
     Real-time factor: 0.10x (1.0 = real-time)
     Segments: 47
```

If files are waiting in the inbox, you'll see a notification on launch:

```
  📬 3 file(s) waiting in inbox — type /inbox to process
```

### Inbox Workflow (Batch Transcription)

For hands-off transcription without typing file paths:

```
whisper-stt/
├── inbox/       ← Drop audio files here
├── output/      ← Transcripts appear here
└── processed/   ← Originals move here after transcription
```

**Steps:**

1. Drop one or more audio files into `inbox/`
2. Run `./whisper --inbox` (or launch interactive mode and type `/inbox`)
3. Each file is transcribed, the transcript is saved to `output/`, and the original is moved to `processed/`

**Example output:**

```
  📬 3 file(s) in inbox:

     • interview.mp3  (24.7 MB)
     • meeting.m4a  (8.2 MB)
     • voice-note.wav  (1.1 MB)

  ══════════════════════════════════════════════════
    [1/3]  interview.mp3
  ══════════════════════════════════════════════════
  ...
  💾 Saved: output/interview.txt
  📦 Moved: processed/interview.mp3

  ══════════════════════════════════════════════════
  ✅ Done!  3 transcribed
  📂 Transcripts in: .../whisper-stt/output/
  ══════════════════════════════════════════════════
```

The output format follows your current format setting. To get SRT subtitles instead of plain text:

```bash
./whisper --inbox -f srt
```

Or in interactive mode: `/format srt` then `/inbox`.

Duplicate filenames in `processed/` are handled automatically (appends `_1`, `_2`, etc.).

### Microphone Recording

```bash
# Record 10 seconds (default) and transcribe
./whisper --record

# Record 30 seconds
./whisper --record 30
```

In interactive mode: `/record` or `/record 30`.

Press Ctrl+C to stop recording early. The recording is transcribed immediately.

Requires microphone access — allow Terminal in **System Preferences > Privacy & Security > Microphone**.

---

## Models

### Model Catalog

| Model | Parameters | Download Size | Quality | Speed |
|-------|-----------|---------------|---------|-------|
| `tiny` | 39M | ~75 MB | Low | Fastest |
| `tiny.en` | 39M | ~75 MB | Low (English-only) | Fastest |
| `base` | 74M | ~140 MB | Moderate | Fast |
| `base.en` | 74M | ~140 MB | Moderate (English-only) | Fast |
| **`small`** | 244M | ~460 MB | **Good (default)** | **Balanced** |
| `small.en` | 244M | ~460 MB | Good (English-only) | Balanced |
| `medium` | 769M | ~1.5 GB | High | Slower |
| `medium.en` | 769M | ~1.5 GB | High (English-only) | Slower |
| `large-v3` | 1.55B | ~2.9 GB | Best | Slowest |
| `turbo` | 809M | ~1.6 GB | Near-best | Fast for its quality |

### Choosing a Model

- **Quick notes, voice memos:** `tiny` or `base` — fast, good enough for clear speech
- **Podcasts, meetings, general use:** `small` (default) — best balance of speed and accuracy
- **Interviews, transcription work:** `medium` — high accuracy, worth the wait
- **Critical accuracy, multilingual:** `large-v3` — best quality, slowest
- **Best bang for buck:** `turbo` — near large-v3 quality at much faster speed

**`.en` models** are English-only but slightly more accurate for English content. Use them if you know the audio is English.

Models are downloaded on first use and cached in `~/.cache/huggingface/hub/`. They're shared across projects using Faster-Whisper.

---

## Output Formats

| Format | Extension | Use Case | Example |
|--------|-----------|----------|---------|
| `text` | `.txt` | Plain transcript, reading, editing | `Hello, welcome to the podcast.` |
| `srt` | `.srt` | SubRip subtitles — video players, YouTube upload | `1\n00:00:01,200 --> 00:00:04,800\nHello, welcome to the podcast.` |
| `vtt` | `.vtt` | WebVTT — web/HTML5 video, browser playback | `WEBVTT\n\n00:00:01.200 --> 00:00:04.800\nHello, welcome to the podcast.` |
| `json` | `.json` | Programmatic use — includes timestamps, language, confidence | `{"language": "en", "segments": [...]}` |

Format is auto-detected from the output file extension (`-o transcript.srt` uses SRT), or set explicitly with `-f srt`.

### JSON Output Structure

```json
{
  "language": "en",
  "language_probability": 0.987,
  "duration": 222.45,
  "segments": [
    {
      "start": 1.2,
      "end": 4.8,
      "text": "Hello, welcome to the podcast."
    },
    ...
  ]
}
```

---

## Supported Audio Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| MP3 | `.mp3` | Most common |
| MP4 | `.mp4` | Video files (audio track extracted) |
| WAV | `.wav` | Uncompressed |
| M4A | `.m4a` | Apple audio (Voice Memos, etc.) |
| OGG | `.ogg` | Open format |
| FLAC | `.flac` | Lossless compressed |
| AAC | `.aac` | Advanced Audio Coding |
| WebM | `.webm` | Web video |
| MKV | `.mkv` | Matroska video |
| MOV | `.mov` | QuickTime |
| AVI | `.avi` | Windows video |
| Opus | `.opus` | Voice-optimized codec |

Audio decoding is handled by PyAV (bundled FFmpeg) — no system ffmpeg needed for transcription.

---

## CLI Reference

```
usage: whisper_stt_local.py [-h] [-m MODEL] [-l LANGUAGE] [-o OUTPUT]
                            [-f {text,srt,vtt,json}] [--list-models]
                            [--record [SECONDS]] [--inbox] [--no-print]
                            [audio]

positional arguments:
  audio                 Audio file to transcribe

optional arguments:
  -h, --help            show this help message and exit
  -m, --model MODEL     Model size (default: small)
  -l, --language LANG   Language code — e.g. en, ja, es (auto-detect if omitted)
  -o, --output PATH     Output file path (.txt, .srt, .vtt, or .json)
  -f, --format FORMAT   Output format: text, srt, vtt, json (default: text)
  --list-models         List all available models
  --record [SECONDS]    Record from microphone (default: 10 seconds)
  --inbox               Transcribe all files in inbox/, save to output/
  --no-print            Don't print transcript to terminal
```

### Examples

```bash
# Quick transcribe
./whisper recording.mp3

# Medium model, force English, save as SRT
./whisper -m medium -l en -o subtitles.srt podcast.mp3

# Batch transcribe inbox, output as JSON
./whisper --inbox -f json

# Record 30 seconds, save transcript
./whisper --record 30 -o note.txt

# Transcribe without terminal output
./whisper --no-print -o transcript.txt meeting.wav

# Interactive mode
./whisper
```

---

## How It Works

1. **Model loading** — Loads a Whisper model via CTranslate2 (quantized for CPU inference)
2. **Audio decoding** — Input file is decoded via PyAV (bundled FFmpeg)
3. **VAD filtering** — Voice Activity Detection removes silence (500ms threshold)
4. **Transcription** — Audio is processed through the Whisper encoder-decoder on CPU
5. **Language detection** — First 30 seconds are used to auto-detect language (unless forced with `-l`)
6. **Output formatting** — Segments are assembled into the chosen format (text, SRT, VTT, JSON)

Progress is shown in real-time with a progress bar, elapsed time, and ETA:

```
   ┃██████████████░░░░░░░░░░░░░░░░┃ 72%  45s  ~17s left
```

After transcription, a summary shows the real-time factor (RTF):

```
✅ Transcribed 3m 42s of audio in 23s
   Real-time factor: 0.10x (1.0 = real-time)
   Segments: 47
```

An RTF of 0.10x means 10x faster than real-time — 1 hour of audio takes ~6 minutes.

---

## Platform Notes

### Intel Mac
- Uses **CTranslate2** — not PyTorch. No version ceiling issues.
- Runs on **CPU** with `float32` compute — compatible with all Intel CPUs.
- `small` model: expect ~0.1–0.2x RTF (5–10x faster than real-time).
- ~460 MB model download on first setup. Fully **offline** after that.

### Apple Silicon
- Same CTranslate2 path. CPU only (no Metal/GPU), but Apple Silicon is fast enough.
- `small` model: expect ~0.05–0.1x RTF (10–20x faster than real-time).

### Model Caching
Models are cached in `~/.cache/huggingface/hub/` and shared across any project using Faster-Whisper or HuggingFace. Switching models downloads them on first use.

---

## Troubleshooting

**"No module named faster_whisper"**
Activate the venv: `source venv/bin/activate`. Or use the `./whisper` launcher which does this automatically.

**Slow transcription**
Try a smaller model: `./whisper -m tiny recording.mp3`. See [Choosing a Model](#choosing-a-model) for guidance.

**Microphone not working**
Allow Terminal microphone access in **System Preferences > Privacy & Security > Microphone**.

**Model download fails**
Check your internet connection. Models download from HuggingFace Hub on first use. If behind a proxy, set `HTTPS_PROXY`.

**"Unsupported format"**
Check the file extension. Supported formats: mp3, mp4, wav, m4a, ogg, flac, aac, webm, mkv, mov, avi, opus.

**Inbox is empty**
Make sure files are in `whisper-stt/inbox/` (not a subdirectory). Only files with supported audio extensions are detected.

---

## Uninstall

```bash
chmod +x uninstall_whisper.sh
./uninstall_whisper.sh
```

Prompts before deleting each component:

1. Virtual environment (`venv/`)
2. Cached Whisper models (`~/.cache/huggingface/hub/`)
3. Launcher script (`whisper`)
4. Output files (`whisper_output*`)
5. All scripts (full removal)

All prompts default to no.

---

## File Manifest

| File / Directory | Purpose | Size |
|-----------------|---------|------|
| `whisper_stt_local.py` | STT engine | ~614 lines |
| `setup_whisper.sh` | Installer | ~127 lines |
| `uninstall_whisper.sh` | Uninstaller | ~75 lines |
| `whisper` | Generated bash launcher | 4 lines |
| `inbox/` | Drop audio files here for batch processing | — |
| `output/` | Transcripts saved here | — |
| `processed/` | Originals moved here after transcription | — |
| `venv/` | Python virtual environment | ~300 MB |
| `.gitignore` | Git ignore rules | — |
| `README.md` | This documentation | — |
| `CHANGELOG.md` | Version history | — |
| `VERSION` | Current version number | — |
