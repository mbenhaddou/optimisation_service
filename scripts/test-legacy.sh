#!/usr/bin/env bash
set -euo pipefail

if [ ! -f "../.venv/bin/python" ]; then
  echo "Missing .venv. Run: python -m venv .venv && ./.venv/bin/pip install -r requirements.txt"
  exit 1
fi

PYTHONPATH="$PWD:$PWD/archive" ../.venv/bin/python -m pytest ../archive/tests "$@"
