#!/bin/bash
# ══════════════════════════════════════════════════════════════════════════════
# Whisper STT Local — Setup Script for macOS
# Uses Faster-Whisper (CTranslate2) — no PyTorch required!
# ══════════════════════════════════════════════════════════════════════════════

set -e

INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$INSTALL_DIR"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     🎤  WHISPER STT LOCAL — macOS Setup  🎤               ║"
echo "║     Powered by CTranslate2 (no PyTorch needed)           ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "   Install directory: $INSTALL_DIR"
echo ""

# ── 1. Check for Homebrew ────────────────────────────────────────────────────
echo "🔍 Step 1/4: Checking for Homebrew..."
if ! command -v brew &> /dev/null; then
    echo "   ⚠  Homebrew not found. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "   ✅ Homebrew found"
fi

# ── 2. Check Python ─────────────────────────────────────────────────────────
echo ""
echo "🔍 Step 2/4: Checking Python..."
PYTHON_CMD=""

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 10 ]; then
        PYTHON_CMD="python3"
        echo "   ✅ Python $PYTHON_VERSION found"
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "   ⚠  Python 3.10+ required. Installing via Homebrew..."
    brew install python@3.12
    PYTHON_CMD="python3"
fi

# ── 3. Create venv & install packages ───────────────────────────────────────
echo ""
echo "📦 Step 3/4: Setting up Python environment..."

if [ ! -d "$INSTALL_DIR/venv" ]; then
    echo "   🐍 Creating virtual environment..."
    $PYTHON_CMD -m venv "$INSTALL_DIR/venv"
else
    echo "   ✅ Virtual environment exists"
fi

source "$INSTALL_DIR/venv/bin/activate"

echo "   📦 Upgrading pip..."
pip install --upgrade pip setuptools wheel -q

echo "   📦 Installing faster-whisper..."
pip install -U faster-whisper -q

echo "   📦 Installing sounddevice (microphone support)..."
pip install -U sounddevice soundfile numpy -q

# ── 4. Pre-download default model ──────────────────────────────────────────
echo ""
echo "📥 Step 4/4: Pre-downloading default model (small, ~460 MB)..."
echo "   This may take a few minutes on first install."
echo ""

python -c "
from faster_whisper import WhisperModel
print('   ⏳ Downloading model...')
WhisperModel('small', device='cpu', compute_type='float32')
print('   ✅ Model downloaded and ready')
"

# ── Create launcher ─────────────────────────────────────────────────────────
cat > "$INSTALL_DIR/whisper" << LAUNCHER
#!/bin/bash
SCRIPT_DIR="$INSTALL_DIR"
source "\$SCRIPT_DIR/venv/bin/activate"
exec python "\$SCRIPT_DIR/whisper_stt_local.py" "\$@"
LAUNCHER

chmod +x "$INSTALL_DIR/whisper"

# ── Done! ────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                 ✅  SETUP COMPLETE!                      ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║                                                          ║"
echo "║  Quick start:                                            ║"
echo "║    cd $INSTALL_DIR"
echo "║    ./whisper recording.mp3                               ║"
echo "║                                                          ║"
echo "║  Interactive mode:                                       ║"
echo "║    ./whisper                                             ║"
echo "║                                                          ║"
echo "║  Record from mic:                                        ║"
echo "║    ./whisper --record                                    ║"
echo "║                                                          ║"
echo "║  Save as subtitles:                                      ║"
echo "║    ./whisper -o subtitles.srt podcast.mp3                ║"
echo "║                                                          ║"
echo "║  List models:                                            ║"
echo "║    ./whisper --list-models                               ║"
echo "║                                                          ║"
echo "║  Everything runs offline after setup.                    ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
