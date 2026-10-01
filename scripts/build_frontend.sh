#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
rm -rf "$ROOT/frontend/dist"
mkdir -p "$ROOT/frontend/dist"
cp "$ROOT/frontend/index.html" "$ROOT/frontend/app.js" "$ROOT/frontend/styles.css" "$ROOT/frontend/favicon.svg" "$ROOT/frontend/dist/"
