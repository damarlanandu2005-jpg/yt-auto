#!/usr/bin/env bash
# Download the Kokoro voice model (Apache-2.0) if it is not already present.
set -euo pipefail
dir="${1:-models}"
mkdir -p "$dir"
base="https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
for f in kokoro-v1.0.int8.onnx voices-v1.0.bin; do
  if [ ! -s "$dir/$f" ]; then
    echo "Downloading $f"
    curl -fsSL -o "$dir/$f" "$base/$f"
  fi
done
ls -la "$dir"
