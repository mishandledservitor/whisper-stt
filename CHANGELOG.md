# Changelog

All notable changes to Whisper STT Local are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/). Versions follow [Semantic Versioning](https://semver.org/).

---

## [1.1.0] — 2026-04-03

### Added
- Inbox workflow for batch transcription — drop files in `inbox/`, transcribe all at once
- `inbox/`, `output/`, `processed/` directories
- `--inbox` CLI flag to process all files in inbox
- `/inbox` interactive command
- Inbox file count notification on interactive mode launch
- Comprehensive project documentation (README, CHANGELOG, VERSION)

## [1.0.1] — 2026-04-03

### Fixed
- Setup script now finds Homebrew on both Intel (`/usr/local/bin`) and Apple Silicon (`/opt/homebrew/bin`) when invoked from a parent script
- Made `setup_whisper.sh` executable

## [1.0.0] — 2026-04-03

### Added
- `whisper_stt_local.py` — full STT engine using Faster-Whisper (CTranslate2)
- 10 model sizes from tiny (75 MB) to large-v3 (2.9 GB)
- Auto language detection (99+ languages)
- Output as plain text, SRT subtitles, VTT captions, or JSON
- Interactive mode with `/model`, `/lang`, `/format`, `/record`, `/models` commands
- Microphone recording with sounddevice
- Progress bar with ETA and real-time factor
- VAD filtering for cleaner transcription
- `setup_whisper.sh` — automated installer (venv, dependencies, model download)
- `uninstall_whisper.sh` — interactive cleanup with confirmation prompts
