#!/bin/bash
# Render every stage (resumable: frames already on disk are skipped).
cd "$(dirname "$0")/.."
RES=${1:-540x960}; SPP=${2:-8}
for ST in palace london pond sewer market graveyard plague; do
  python3 render.py $ST frames/$ST --res $RES --samples $SPP 2>&1 | grep -E "built|Error|Traceback|rror:" 
  echo "DONE $ST $(ls frames/$ST 2>/dev/null | wc -l) frames"
done
