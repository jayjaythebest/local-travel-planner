#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${1:-$ROOT_DIR/dist}"
ZIP_NAME="${2:-local-travel-planner-export.zip}"

mkdir -p "$OUT_DIR"
OUT_PATH="$OUT_DIR/$ZIP_NAME"

cd "$ROOT_DIR"

zip -r "$OUT_PATH" . \
  -x "*.git*" \
  -x "frontend/node_modules/*" \
  -x "__pycache__/*" \
  -x "*.pyc" \
  -x "dist/*"

echo "Created export: $OUT_PATH"
