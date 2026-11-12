#!/usr/bin/env bash
# Launch the Salla market basket analysis application.
set -euo pipefail

cd "$(dirname "$0")"

if ! python3 -c "import PyQt6" 2>/dev/null; then
    echo "PyQt6 غير مثبّت. ثبّت المتطلبات أولًا:"
    echo "    pip install -r requirements.txt"
    exit 1
fi

exec python3 main.py "$@"
