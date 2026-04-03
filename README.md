# Whisper STT Local — macOS

Local speech-to-text using [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2). No cloud, no API keys, no PyTorch.

> **Your system:** macOS (Intel / Apple Silicon) — this uses `faster-whisper` which runs on CTranslate2, sidestepping the PyTorch dependency entirely.

---

## Setup

Clone the repo, `cd` into it, and run:

```bash
chmod +x setup_whisper.sh
./setup_whisper.sh
```

This installs everything **in the same folder**: Python venv, `faster-whisper`, and downloads the default model (~460 MB). No surprises about where things go.

---

## Usage

```bash
# Quick transcribe & print
./whisper recording.mp3

# Choose a model
./whisper -m medium interview.wav
./whisper -m tiny quick-note.m4a

# Force language (skip auto-detection)
./whisper -l en podcast.mp3
./whisper -l ja japanese-audio.wav

# Save as SRT subtitles
./whisper -o subtitles.srt podcast.mp3

# Save as VTT
./whisper -o captions.vtt -l en talk.m4a

# Save as JSON (with timestamps + metadata)
./whisper -o transcript.json interview.wav

# Record from microphone
./whisper --record
./whisper --record 30     # record 30 seconds

# Interactive mode
./whisper

# List all models
./whisper --list-models
```

### Interactive Commands

```
/model medium     — switch model
/lang en          — set language (or 'auto')
/format srt       — set output: text, srt, vtt, json
/record 15        — record from mic (seconds)
/models           — list all models
/quit             — exit
```

Drop a file path at the prompt to transcribe it.

### Progress Bar

Transcription shows a live progress bar:

```
   ┃██████████████░░░░░░░░░░░░░░░░┃ 72%  45s  ~17s left
```

---

## Models

| Model | Params | Size | Notes |
|-------|--------|------|-------|
| tiny | 39M | ~75 MB | Fastest, least accurate |
| tiny.en | 39M | ~75 MB | English-only tiny |
| base | 74M | ~140 MB | Fast, reasonable accuracy |
| base.en | 74M | ~140 MB | English-only base |
| **small** | 244M | ~460 MB | **Good balance (default)** |
| small.en | 244M | ~460 MB | English-only small |
| medium | 769M | ~1.5 GB | High accuracy, slower |
| medium.en | 769M | ~1.5 GB | English-only medium |
| large-v3 | 1.55B | ~2.9 GB | Best accuracy, slowest |
| turbo | 809M | ~1.6 GB | Near large-v3 quality, much faster |

`.en` models are English-only but slightly better for English content.

---

## Supported Audio Formats

mp3, mp4, wav, m4a, ogg, flac, aac, webm, mkv, mov, avi, opus

Powered by PyAV (bundled FFmpeg) — no system ffmpeg needed for transcription.

---

## Output Formats

| Format | Extension | Use case |
|--------|-----------|----------|
| text | .txt | Plain transcript |
| srt | .srt | SubRip subtitles (video players, YouTube) |
| vtt | .vtt | WebVTT subtitles (web, HTML5 video) |
| json | .json | Programmatic use (includes timestamps + metadata) |

Format is auto-detected from the output file extension, or set with `-f`.

---

## Intel Mac Notes

- Uses **CTranslate2** — not PyTorch. No version ceiling issues on Intel Mac.
- Runs on **CPU** with `float32` compute — compatible with all Intel CPUs.
- ~460 MB model download on first setup (for `small`). Fully **offline** after that.
- Models cached in `~/.cache/huggingface/hub/` and shared across projects.

---

## Troubleshooting

**"No module named faster_whisper"** — Activate the venv: `source venv/bin/activate`

**Slow transcription** — Try a smaller model: `./whisper -m tiny recording.mp3`

**Microphone not working** — Allow Terminal microphone access in System Preferences → Privacy & Security → Microphone.

**Model download fails** — Check internet connection. Models download from HuggingFace Hub on first use.

---

## Uninstall

```bash
chmod +x uninstall_whisper.sh
./uninstall_whisper.sh
```

Asks before deleting each component. Defaults to no.

---

## What's Here

| File | Purpose |
|------|---------|
| `setup_whisper.sh` | Installer — run this first |
| `whisper_stt_local.py` | The STT script |
| `uninstall_whisper.sh` | Clean removal |
| `README.md` | This guide |
