#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "SCRIPT_DIR=$SCRIPT_DIR"
export PYTHONPATH="$SCRIPT_DIR"

cd "$SCRIPT_DIR" || exit 1

VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"

if [[ ! -x "$VENV_PYTHON" ]]; then
    echo "Error: Python not found at $VENV_PYTHON" >&2
    exit 1
fi

"$VENV_PYTHON" src/main.py