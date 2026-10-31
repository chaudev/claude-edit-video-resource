#!/bin/bash
# One-time setup per fresh container. Run from repo root: bash setup.sh
set -e
cd "$(dirname "$0")"
pip install -q sherpa-onnx numpy pillow --break-system-packages 2>/dev/null || pip install -q sherpa-onnx numpy pillow
mkdir -p fonts models
G=https://raw.githubusercontent.com/google/fonts/main/ofl
for s in Medium SemiBold Bold ExtraBold; do [ -f fonts/BeVietnamPro-$s.ttf ] || curl -sL -o fonts/BeVietnamPro-$s.ttf $G/bevietnampro/BeVietnamPro-$s.ttf; done
[ -f fonts/Anton.ttf ] || curl -sL -o fonts/Anton.ttf $G/anton/Anton-Regular.ttf
[ -f fonts/JBMono.ttf ] || curl -sL -o fonts/JBMono.ttf "$G/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf"
[ -f fonts/PatrickHand.ttf ] || curl -sL -o fonts/PatrickHand.ttf $G/patrickhand/PatrickHand-Regular.ttf
[ -f fonts/VT323.ttf ] || curl -sL -o fonts/VT323.ttf $G/vt323/VT323-Regular.ttf
[ -f fonts/Bungee.ttf ] || curl -sL -o fonts/Bungee.ttf $G/bungee/Bungee-Regular.ttf
[ -f fonts/Lora.ttf ] || curl -sL -o fonts/Lora.ttf "$G/lora/Lora%5Bwght%5D.ttf"
[ -f fonts/LoraItalic.ttf ] || curl -sL -o fonts/LoraItalic.ttf "$G/lora/Lora-Italic%5Bwght%5D.ttf"
R=https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models
if [ ! -d models/vi ]; then curl -sL -o /tmp/vi.tar.bz2 $R/sherpa-onnx-zipformer-vi-int8-2025-04-20.tar.bz2 && tar xjf /tmp/vi.tar.bz2 -C models && mv models/sherpa-onnx-zipformer-vi-int8-2025-04-20 models/vi; fi
[ -f models/silero_vad.onnx ] || curl -sL -o models/silero_vad.onnx $R/silero_vad.onnx
echo SETUP_OK
