#!/usr/bin/env python3
"""
Whisper STT Local — Speech-to-Text using Faster-Whisper (CTranslate2)
For macOS (Intel / Apple Silicon) — no PyTorch required!

Usage:
    python whisper_stt_local.py                             # Interactive mode
    python whisper_stt_local.py recording.mp3               # Quick transcribe
    python whisper_stt_local.py -m small recording.mp3      # Specify model
    python whisper_stt_local.py -o out.srt recording.mp3    # Output as SRT
    python whisper_stt_local.py --list-models               # List models
    python whisper_stt_local.py -l ja recording.mp3         # Force language
    python whisper_stt_local.py --record                    # Record from mic
"""

import argparse
import os
import shutil
import sys
import tempfile
import time
import warnings

warnings.filterwarnings("ignore")

# ── Model catalog ───────────────────────────────────────────────────────────

MODELS = {
    "tiny":     {"params": "39M",   "size": "~75 MB",   "note": "fastest, least accurate"},
    "tiny.en":  {"params": "39M",   "size": "~75 MB",   "note": "English-only tiny"},
    "base":     {"params": "74M",   "size": "~140 MB",  "note": "fast, reasonable accuracy"},
    "base.en":  {"params": "74M",   "size": "~140 MB",  "note": "English-only base"},
    "small":    {"params": "244M",  "size": "~460 MB",  "note": "good balance (recommended)"},
    "small.en": {"params": "244M",  "size": "~460 MB",  "note": "English-only small"},
    "medium":   {"params": "769M",  "size": "~1.5 GB",  "note": "high accuracy, slower"},
    "medium.en":{"params": "769M",  "size": "~1.5 GB",  "note": "English-only medium"},
    "large-v3": {"params": "1.55B", "size": "~2.9 GB",  "note": "best accuracy, slowest"},
    "turbo":    {"params": "809M",  "size": "~1.6 GB",  "note": "near large-v3 quality, much faster"},
}

ALL_MODELS = list(MODELS.keys())
DEFAULT_MODEL = "small"

SUPPORTED_FORMATS = [
    "mp3", "mp4", "wav", "m4a", "ogg", "flac",
    "aac", "webm", "mkv", "mov", "avi", "opus",
]

WHISPER_DIR = os.path.dirname(os.path.abspath(__file__))
INBOX_DIR = os.path.join(WHISPER_DIR, "inbox")
OUTPUT_DIR = os.path.join(WHISPER_DIR, "output")
PROCESSED_DIR = os.path.join(WHISPER_DIR, "processed")

# ── Utilities ───────────────────────────────────────────────────────────────

def resolve_path(path):
    return os.path.abspath(os.path.expanduser(path))


def format_time(seconds):
    if seconds < 60:
        return f"{seconds:.0f}s"
    m, s = divmod(int(seconds), 60)
    if m < 60:
        return f"{m}m {s:02d}s"
    h, m = divmod(m, 60)
    return f"{h}h {m:02d}m"


def format_timestamp_srt(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def format_timestamp_vtt(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def draw_progress(current, total, elapsed, bar_width=30):
    term_width = shutil.get_terminal_size((80, 20)).columns
    bar_width = min(bar_width, term_width - 50)
    pct = current / total if total > 0 else 0
    filled = int(bar_width * pct)
    bar = '█' * filled + '░' * (bar_width - filled)
    if current > 0 and pct < 1.0:
        eta = (elapsed / current) * (total - current)
        eta_str = f"~{format_time(eta)} left"
    elif pct >= 1.0:
        eta_str = "done!"
    else:
        eta_str = "estimating..."
    line = f"\r   ┃{bar}┃ {pct*100:.0f}%  {format_time(elapsed)}  {eta_str}"
    sys.stdout.write(line.ljust(term_width - 1))
    sys.stdout.flush()

# ── Output formatters ───────────────────────────────────────────────────────

def format_text(segments):
    lines = []
    for seg in segments:
        lines.append(seg.text.strip())
    return "\n".join(lines)


def format_srt(segments):
    lines = []
    for i, seg in enumerate(segments, 1):
        start = format_timestamp_srt(seg.start)
        end = format_timestamp_srt(seg.end)
        lines.append(str(i))
        lines.append(f"{start} --> {end}")
        lines.append(seg.text.strip())
        lines.append("")
    return "\n".join(lines)


def format_vtt(segments):
    lines = ["WEBVTT", ""]
    for seg in segments:
        start = format_timestamp_vtt(seg.start)
        end = format_timestamp_vtt(seg.end)
        lines.append(f"{start} --> {end}")
        lines.append(seg.text.strip())
        lines.append("")
    return "\n".join(lines)


def format_json(segments, info):
    import json
    data = {
        "language": info.language,
        "language_probability": round(info.language_probability, 3),
        "duration": round(info.duration, 2),
        "segments": [],
    }
    for seg in segments:
        data["segments"].append({
            "start": round(seg.start, 3),
            "end": round(seg.end, 3),
            "text": seg.text.strip(),
        })
    return json.dumps(data, indent=2, ensure_ascii=False)


def detect_format_from_path(path):
    _, ext = os.path.splitext(path)
    ext = ext.lower().lstrip(".")
    return {"srt": "srt", "vtt": "vtt", "json": "json", "txt": "text"}.get(ext, "text")

# ── Core ────────────────────────────────────────────────────────────────────

def load_model(model_name):
    print(f"⏳ Loading Whisper model ({model_name})...")
    start = time.time()
    from faster_whisper import WhisperModel
    model = WhisperModel(model_name, device="cpu", compute_type="float32")
    elapsed = time.time() - start
    print(f"✅ Model loaded in {elapsed:.1f}s")
    return model


def transcribe_audio(model, audio_path, language=None):
    audio_path = resolve_path(audio_path)
    if not os.path.isfile(audio_path):
        print(f"⚠  File not found: {audio_path}")
        print(f"   (working dir: {os.getcwd()})")
        return None, None

    _, ext = os.path.splitext(audio_path)
    ext = ext.lower().lstrip(".")
    if ext not in SUPPORTED_FORMATS:
        print(f"⚠  Unsupported format: .{ext}")
        print(f"   Supported: {', '.join(SUPPORTED_FORMATS)}")
        return None, None

    file_size = os.path.getsize(audio_path)
    print(f"\n🎤 File: {os.path.basename(audio_path)} ({file_size / (1024*1024):.1f} MB)")
    if language:
        print(f"🌐 Language: {language}")
    else:
        print("🌐 Language: auto-detect")

    print()
    start = time.time()

    segments_gen, info = model.transcribe(
        audio_path,
        language=language,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )

    if not language:
        print(f"   Detected: {info.language} ({info.language_probability:.0%} confidence)")

    # Consume the generator to get all segments
    segments = []
    duration = info.duration
    for seg in segments_gen:
        segments.append(seg)
        if duration > 0:
            draw_progress(seg.end, duration, time.time() - start)

    elapsed = time.time() - start
    if duration > 0:
        draw_progress(duration, duration, elapsed)
    print()

    audio_duration = format_time(duration)
    print(f"\n✅ Transcribed {audio_duration} of audio in {format_time(elapsed)}")
    rtf = elapsed / duration if duration > 0 else 0
    print(f"   Real-time factor: {rtf:.2f}x (1.0 = real-time)")
    print(f"   Segments: {len(segments)}")

    return segments, info


def record_audio(duration=10, sample_rate=16000):
    try:
        import sounddevice as sd
    except ImportError:
        print("⚠  Microphone recording requires sounddevice.")
        print("   Install: pip install sounddevice")
        return None

    try:
        import numpy as np
        import soundfile as sf
    except ImportError:
        print("⚠  Recording requires numpy and soundfile.")
        return None

    print(f"🎙  Recording for {duration}s (Ctrl+C to stop early)...")
    print("   ⏺  Recording...", end="", flush=True)

    try:
        audio = sd.rec(int(duration * sample_rate),
                       samplerate=sample_rate, channels=1, dtype='float32')
        sd.wait()
        print(" done!")
    except KeyboardInterrupt:
        sd.stop()
        frames = sd.get_stream().read_available if hasattr(sd, 'get_stream') else 0
        print(" stopped early!")
        # Trim to actual recorded samples
        audio = audio[:max(1, int(sd.default.samplerate * 0.5))]
    except Exception as e:
        print(f"\n⚠  Recording failed: {e}")
        print("   On macOS, allow Terminal microphone access in System Preferences → Privacy.")
        return None

    # Write to temp file
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(tmp.name, audio, sample_rate)
    tmp.close()

    file_size = os.path.getsize(tmp.name)
    actual_duration = len(audio) / sample_rate
    print(f"   📁 {actual_duration:.1f}s recorded ({file_size / 1024:.0f} KB)")

    return tmp.name


def print_models():
    print("\n╔══════════════════════════════════════════════╗")
    print("║       🤖  WHISPER MODEL CATALOG  🤖          ║")
    print("╚══════════════════════════════════════════════╝\n")
    print(f"  ┌─ {'Model':<12} {'Params':<8} {'Size':<12} {'Notes'} ─┐")
    print(f"  │{'─' * 55}│")
    for name, info in MODELS.items():
        marker = " ★" if name == DEFAULT_MODEL else ""
        print(f"  │  {name:<12} {info['params']:<8} {info['size']:<12} {info['note']}{marker}")
    print(f"  └{'─' * 55}┘\n")
    print(f"  ★ = default model ({DEFAULT_MODEL})")
    print(f"  .en models are English-only (slightly better for English)\n")

# ── Inbox / batch processing ───────────────────────────────────────────────

def scan_inbox():
    """Return list of audio files in the inbox folder."""
    os.makedirs(INBOX_DIR, exist_ok=True)
    files = []
    for name in sorted(os.listdir(INBOX_DIR)):
        ext = os.path.splitext(name)[1].lower().lstrip(".")
        if ext in SUPPORTED_FORMATS:
            files.append(os.path.join(INBOX_DIR, name))
    return files


def process_inbox(model, language=None, out_format="text"):
    """Transcribe all files in inbox/, save to output/, move originals to processed/."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    files = scan_inbox()
    if not files:
        print("\n  📭 Inbox is empty — drop audio files into:")
        print(f"     {INBOX_DIR}/\n")
        return

    ext_map = {"text": ".txt", "srt": ".srt", "vtt": ".vtt", "json": ".json"}
    out_ext = ext_map.get(out_format, ".txt")

    print(f"\n  📬 {len(files)} file(s) in inbox:\n")
    for f in files:
        size = os.path.getsize(f) / (1024 * 1024)
        print(f"     • {os.path.basename(f)}  ({size:.1f} MB)")
    print()

    succeeded = 0
    failed = 0

    for i, audio_path in enumerate(files, 1):
        basename = os.path.basename(audio_path)
        name_no_ext = os.path.splitext(basename)[0]

        print(f"\n{'═' * 50}")
        print(f"  [{i}/{len(files)}]  {basename}")
        print(f"{'═' * 50}")

        segments, info = transcribe_audio(model, audio_path, language)
        if segments is None:
            print(f"  ⚠  Skipping {basename}")
            failed += 1
            continue

        # Format output
        if out_format == "json":
            result = format_json(segments, info)
        else:
            formatter = {"text": format_text, "srt": format_srt,
                         "vtt": format_vtt}.get(out_format, format_text)
            result = formatter(segments)

        # Save transcript
        out_path = os.path.join(OUTPUT_DIR, name_no_ext + out_ext)
        with open(out_path, "w") as f:
            f.write(result)
        print(f"  💾 Saved: output/{name_no_ext}{out_ext}")

        # Move original to processed
        dest = os.path.join(PROCESSED_DIR, basename)
        # Handle duplicate filenames
        if os.path.exists(dest):
            base, ext = os.path.splitext(basename)
            counter = 1
            while os.path.exists(dest):
                dest = os.path.join(PROCESSED_DIR, f"{base}_{counter}{ext}")
                counter += 1
        shutil.move(audio_path, dest)
        print(f"  📦 Moved:  processed/{os.path.basename(dest)}")
        succeeded += 1

    print(f"\n{'═' * 50}")
    print(f"  ✅ Done!  {succeeded} transcribed", end="")
    if failed:
        print(f", {failed} failed", end="")
    print(f"\n  📂 Transcripts in: {OUTPUT_DIR}/")
    print(f"{'═' * 50}\n")


# ── Interactive mode ────────────────────────────────────────────────────────

def interactive_mode(model, model_name):
    language = None
    output_format = "text"

    print("\n╔══════════════════════════════════════════════╗")
    print("║     🎧  WHISPER STT — INTERACTIVE MODE  🎧    ║")
    print("╚══════════════════════════════════════════════╝")
    print(f"\n  Model: {model_name}  |  Language: {'auto' if not language else language}  |  Format: {output_format}")
    # Show inbox count on launch
    inbox_files = scan_inbox()
    if inbox_files:
        print(f"\n  📬 {len(inbox_files)} file(s) waiting in inbox — type /inbox to process")

    print("\n  Drop a file path or use a command:")
    print("    /inbox             — transcribe all files in inbox/")
    print("    /model <name>      — change model (e.g. /model medium)")
    print("    /lang <code>       — set language (e.g. /lang ja), 'auto' to detect")
    print("    /format <fmt>      — set output: text, srt, vtt, json")
    print("    /record [seconds]  — record from microphone (default 10s)")
    print("    /models            — list all models")
    print("    /quit              — exit\n")

    while True:
        try:
            text = input("  ▶ ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  👋 Goodbye!\n")
            break

        if not text:
            continue

        if text.startswith("/"):
            parts = text.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1].strip() if len(parts) > 1 else ""

            if cmd in ("/quit", "/exit", "/q"):
                print("\n  👋 Goodbye!\n")
                break
            elif cmd == "/model":
                if arg in ALL_MODELS:
                    model_name = arg
                    print(f"  ⏳ Switching to {model_name}...")
                    model = load_model(model_name)
                elif arg:
                    print(f"  ⚠  Unknown model: {arg}. Use /models to see options.")
                else:
                    print(f"  ℹ  Current model: {model_name}")
            elif cmd == "/lang":
                if arg.lower() == "auto":
                    language = None
                    print("  ✅ Language: auto-detect")
                elif arg:
                    language = arg.lower()
                    print(f"  ✅ Language: {language}")
                else:
                    print(f"  ℹ  Language: {'auto' if not language else language}")
            elif cmd == "/format":
                if arg in ("text", "srt", "vtt", "json"):
                    output_format = arg
                    print(f"  ✅ Format: {output_format}")
                elif arg:
                    print(f"  ⚠  Unknown format. Use: text, srt, vtt, json")
                else:
                    print(f"  ℹ  Format: {output_format}")
            elif cmd == "/record":
                duration = 10
                if arg:
                    try:
                        duration = int(arg)
                    except ValueError:
                        print("  ⚠  Invalid duration. Use: /record 15")
                        continue
                tmp_path = record_audio(duration)
                if tmp_path:
                    segments, info = transcribe_audio(model, tmp_path, language)
                    if segments is not None:
                        formatter = {"text": format_text, "srt": format_srt,
                                     "vtt": format_vtt}.get(output_format, format_text)
                        if output_format == "json":
                            result = format_json(segments, info)
                        else:
                            result = formatter(segments)
                        print(f"\n{'─' * 50}")
                        print(result)
                        print(f"{'─' * 50}")
                    os.unlink(tmp_path)
            elif cmd == "/inbox":
                process_inbox(model, language, output_format)
            elif cmd == "/models":
                print_models()
            else:
                print(f"  ⚠  Unknown command: {cmd}")
            continue

        # Treat input as a file path
        audio_path = resolve_path(text)
        if not os.path.isfile(audio_path):
            print(f"  ⚠  File not found: {audio_path}")
            print(f"     Drop an audio file path or use /record")
            continue

        segments, info = transcribe_audio(model, audio_path, language)
        if segments is None:
            continue

        formatter = {"text": format_text, "srt": format_srt,
                     "vtt": format_vtt}.get(output_format, format_text)
        if output_format == "json":
            result = format_json(segments, info)
        else:
            result = formatter(segments)

        print(f"\n{'─' * 50}")
        print(result)
        print(f"{'─' * 50}")

        # Ask to save
        try:
            save = input("\n  💾 Save to file? (path or Enter to skip): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            continue
        if save:
            save_path = resolve_path(save)
            out_fmt = detect_format_from_path(save_path)
            if out_fmt == "json":
                out_text = format_json(segments, info)
            else:
                out_formatter = {"text": format_text, "srt": format_srt,
                                 "vtt": format_vtt}.get(out_fmt, format_text)
                out_text = out_formatter(segments)
            with open(save_path, "w") as f:
                f.write(out_text)
            print(f"  ✅ Saved to: {save_path}")

# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Whisper STT Local — Speech-to-text using Faster-Whisper (CTranslate2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                  Interactive mode
  %(prog)s recording.mp3                    Quick transcribe & print
  %(prog)s -m medium interview.wav          Use medium model
  %(prog)s -o subtitles.srt podcast.mp3     Save as SRT subtitles
  %(prog)s -o transcript.vtt -l en talk.m4a Save as VTT, force English
  %(prog)s --record                         Record from microphone
  %(prog)s --record 30                      Record 30 seconds from mic
  %(prog)s --list-models                    Show all models
        """
    )
    parser.add_argument("audio", nargs="?", help="Audio file to transcribe")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL,
                        help=f"Model size (default: {DEFAULT_MODEL})")
    parser.add_argument("-l", "--language", default=None,
                        help="Language code (auto-detect if omitted)")
    parser.add_argument("-o", "--output", default=None,
                        help="Output path — .txt, .srt, .vtt, or .json")
    parser.add_argument("-f", "--format", default=None,
                        choices=["text", "srt", "vtt", "json"],
                        help="Output format (default: text, or inferred from -o)")
    parser.add_argument("--list-models", action="store_true",
                        help="List all available models")
    parser.add_argument("--record", type=int, nargs="?", const=10, default=None,
                        help="Record from microphone (optional: seconds, default 10)")
    parser.add_argument("--inbox", action="store_true",
                        help="Transcribe all files in inbox/, save to output/")
    parser.add_argument("--no-print", action="store_true",
                        help="Don't print transcript to terminal")

    args = parser.parse_args()

    if args.list_models:
        print_models()
        sys.exit(0)

    if args.model not in ALL_MODELS:
        print(f"⚠  Unknown model: {args.model}")
        print_models()
        sys.exit(1)

    model = load_model(args.model)

    # Determine output format
    out_format = args.format
    if not out_format and args.output:
        out_format = detect_format_from_path(args.output)
    if not out_format:
        out_format = "text"

    # Process inbox
    if args.inbox:
        process_inbox(model, args.language, out_format)
        return

    # Record from mic
    if args.record is not None:
        tmp_path = record_audio(args.record)
        if not tmp_path:
            sys.exit(1)
        segments, info = transcribe_audio(model, tmp_path, args.language)
        os.unlink(tmp_path)
        if segments is None:
            sys.exit(1)
    elif args.audio:
        segments, info = transcribe_audio(model, args.audio, args.language)
        if segments is None:
            sys.exit(1)
    else:
        # No audio file and no --record: enter interactive mode
        interactive_mode(model, args.model)
        return

    # Format output
    if out_format == "json":
        result = format_json(segments, info)
    else:
        formatter = {"text": format_text, "srt": format_srt,
                     "vtt": format_vtt}.get(out_format, format_text)
        result = formatter(segments)

    # Print to terminal
    if not args.no_print:
        print(f"\n{'─' * 50}")
        print(result)
        print(f"{'─' * 50}")

    # Save to file
    if args.output:
        out_path = resolve_path(args.output)
        out_dir = os.path.dirname(out_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(out_path, "w") as f:
            f.write(result)
        print(f"\n💾 Saved to: {out_path}")


if __name__ == "__main__":
    main()
