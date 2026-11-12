#!/usr/bin/env bash
# One-time setup for the Augaster AI Digest reel renderer.
set -euo pipefail
cd "$(dirname "$0")"
pip install --break-system-packages -q -r requirements.txt 2>/dev/null || pip install -q -r requirements.txt
command -v ffmpeg >/dev/null || { echo "ffmpeg is required"; exit 1; }
mkdir -p voices
if [ ! -f voices/en-us-lessac-medium.onnx ]; then
  curl -sSL -o voices/voice.tar.gz https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-en-us-lessac-medium.tar.gz
  tar xzf voices/voice.tar.gz -C voices && rm voices/voice.tar.gz
fi
for f in kokoro-v1.0.onnx voices-v1.0.bin; do
  [ -f "voices/$f" ] || curl -sSL -o "voices/$f" "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/$f"
done
echo "Ready: python3 render_reel.py episodes/<date-slug>/script.json --voice kokoro:af_heart"
