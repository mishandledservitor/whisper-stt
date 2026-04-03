#!/bin/bash
# ══════════════════════════════════════════════════════════════════════════════
# Whisper STT Local — Uninstall Script
# ══════════════════════════════════════════════════════════════════════════════

INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║       🗑  WHISPER STT LOCAL — UNINSTALL                  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "   Directory: $INSTALL_DIR"
echo ""

# ── 1. Virtual environment ───────────────────────────────────────────────────
if [ -d "$INSTALL_DIR/venv" ]; then
    SIZE=$(du -sh "$INSTALL_DIR/venv" 2>/dev/null | awk '{print $1}')
    echo "🐍 Virtual environment ($SIZE)"
    read -p "   Delete? [y/N] " c; [[ "$c" =~ ^[Yy]$ ]] && rm -rf "$INSTALL_DIR/venv" && echo "   ✅ Removed" || echo "   ⏭  Skipped"
fi

# ── 2. Cached models ────────────────────────────────────────────────────────
echo ""
CACHE_DIR="$HOME/.cache/huggingface/hub"
WHISPER_MODELS=$(find "$CACHE_DIR" -maxdepth 1 -name "models--Systran--faster-whisper-*" -type d 2>/dev/null)
if [ -n "$WHISPER_MODELS" ]; then
    SIZE=$(du -sh $WHISPER_MODELS 2>/dev/null | awk '{total += $1} END {print total}')
    TOTAL_SIZE=$(du -shc $WHISPER_MODELS 2>/dev/null | tail -1 | awk '{print $1}')
    echo "📦 Cached Whisper models ($TOTAL_SIZE total)"
    echo "$WHISPER_MODELS" | while read d; do
        S=$(du -sh "$d" 2>/dev/null | awk '{print $1}')
        echo "      $(basename $d) ($S)"
    done
    read -p "   Delete all cached models? [y/N] " c
    if [[ "$c" =~ ^[Yy]$ ]]; then
        echo "$WHISPER_MODELS" | xargs rm -rf
        echo "   ✅ Removed"
    else
        echo "   ⏭  Skipped"
    fi
else
    echo "📦 No cached Whisper models found"
fi

# ── 3. Launcher ─────────────────────────────────────────────────────────────
echo ""
if [ -f "$INSTALL_DIR/whisper" ]; then
    echo "🚀 Launcher script"
    read -p "   Delete? [y/N] " c; [[ "$c" =~ ^[Yy]$ ]] && rm -f "$INSTALL_DIR/whisper" && echo "   ✅ Removed" || echo "   ⏭  Skipped"
fi

# ── 4. Output files ─────────────────────────────────────────────────────────
echo ""
OUTPUTS=$(find "$INSTALL_DIR" -maxdepth 1 -name "whisper_output*" 2>/dev/null)
if [ -n "$OUTPUTS" ]; then
    echo "🔊 Output files:"
    echo "$OUTPUTS" | while read f; do echo "      $(basename $f)"; done
    read -p "   Delete all? [y/N] " c; [[ "$c" =~ ^[Yy]$ ]] && echo "$OUTPUTS" | xargs rm -f && echo "   ✅ Removed" || echo "   ⏭  Skipped"
fi

# ── 5. Scripts themselves ────────────────────────────────────────────────────
echo ""
echo "📄 Scripts: whisper_stt_local.py, setup_whisper.sh, uninstall_whisper.sh, README.md"
read -p "   Delete all scripts? (full removal) [y/N] " c
if [[ "$c" =~ ^[Yy]$ ]]; then
    rm -f "$INSTALL_DIR/whisper_stt_local.py" "$INSTALL_DIR/setup_whisper.sh" "$INSTALL_DIR/uninstall_whisper.sh" "$INSTALL_DIR/README.md"
    echo "   ✅ Removed"
    rmdir "$INSTALL_DIR" 2>/dev/null && echo "   ✅ Removed empty directory"
fi

echo ""
echo "✅ Uninstall complete."
echo ""
