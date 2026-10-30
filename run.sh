#!/bin/sh
# Usage: ./run.sh --source <name> <folder>
cd "$(dirname "$0")" || exit 1
PYTHONPATH=../mvw-core exec python3 -m mvw_importer_local "$@"
