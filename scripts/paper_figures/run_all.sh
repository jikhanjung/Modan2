#!/usr/bin/env bash
# Take the Modan2 paper's screenshots (Figures 2-6) from a Modan2 checkout.
#
#   scripts/paper_figures/run_all.sh <checkout> <tardigrades.zip> <out dir>
#
# <checkout>        the Modan2 version the figures show, e.g. a worktree at a tag
# <tardigrades.zip> the tardigrade dataset as a JSON+ZIP package (see README.md)
# <out dir>         where the PNGs go
#
# The library is built in a temporary HOME, so neither the user's library nor
# their preferences are touched; the screen is a private Xvfb display. Run
# scripts/rovinsky2021_data.py first: the cranial data come from its output.
# PYTHON may name the interpreter (default: python3).
set -euo pipefail

if [ $# -ne 3 ]; then
    sed -n '2,13p' "$0"
    exit 2
fi
CHECKOUT=$(realpath "$1")
ZIP=$(realpath "$2")
OUT=$(realpath -m "$3")
HERE=$(cd "$(dirname "$0")" && pwd)
NEURO="$HERE/../../benchmarks/data/rovinsky2021/neurocranium_222.txt"
PYTHON=${PYTHON:-python3}

[ -f "$NEURO" ] || { echo "missing $NEURO -- run scripts/rovinsky2021_data.py first" >&2; exit 1; }
command -v Xvfb >/dev/null || { echo "Xvfb is required" >&2; exit 1; }

WORK=$(mktemp -d)
mkdir -p "$OUT"
DISPLAY_NUM=99
while [ -e "/tmp/.X${DISPLAY_NUM}-lock" ]; do DISPLAY_NUM=$((DISPLAY_NUM + 1)); done
Xvfb ":$DISPLAY_NUM" -screen 0 1920x1080x24 >/dev/null 2>&1 &
XVFB_PID=$!
trap 'kill $XVFB_PID 2>/dev/null; rm -rf "$WORK"' EXIT
sleep 2

export HOME="$WORK" XDG_CONFIG_HOME="$WORK/.config" XDG_DATA_HOME="$WORK/.local/share"
export DISPLAY=":$DISPLAY_NUM"

cd "$CHECKOUT"  # Modan2 resolves its resources (migrations, icons) against the cwd
run() {  # run one step, show its summary lines, stop on failure with its log
    local name=$1
    shift
    echo "== $name"
    if ! "$PYTHON" -I "$@" >"$WORK/$name.log" 2>&1; then
        tail -n 30 "$WORK/$name.log"
        echo "$name failed" >&2
        exit 1
    fi
    grep -E '^(saved|library|curve scheme)' "$WORK/$name.log" || true
}

run build_library "$HERE/build_library.py" "$CHECKOUT" "$WORK" "$ZIP" "Milnesium grandicupula" "$NEURO"
for script in fig2_3 fig4_5 fig6cd fig6ab; do  # fig6ab saves a curve, so it runs last
    run "$script" "$HERE/$script.py" "$CHECKOUT" "$OUT"
done
