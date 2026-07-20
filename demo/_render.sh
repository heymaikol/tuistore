#!/usr/bin/env bash
# renders one demo gif for a given stage label + output path
set -euo pipefail
STAGE="$1"; OUT="$2"
cat > /tmp/demo.tape <<TAPE
Output "${OUT}"
Set Shell bash
Set FontSize 20
Set Width 1320
Set Height 860
Set Padding 26
Set Theme "Catppuccin Mocha"
Set TypingSpeed 12ms
Sleep 400ms
Type "PYTHONPATH=. python3 demo/scrape_demo.py '${STAGE}'"
Enter
Sleep 4500ms
TAPE
vhs /tmp/demo.tape
