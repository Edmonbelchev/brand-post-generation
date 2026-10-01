#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
rm -rf "$ROOT/frontend/dist" "$ROOT/public"
mkdir -p "$ROOT/frontend/dist" "$ROOT/public"
cp "$ROOT/frontend/index.html" "$ROOT/frontend/app.js" "$ROOT/frontend/styles.css" "$ROOT/frontend/favicon.svg" "$ROOT/frontend/dist/"
cp "$ROOT/frontend/dist/"* "$ROOT/public/"
