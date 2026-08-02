#!/usr/bin/env sh
set -eu
COMMAND="${1:-ready}"
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
PYTHON="$ROOT/.venv/bin/python"
if [ ! -x "$PYTHON" ]; then python3 -m venv .venv; fi
case "$COMMAND" in
  bootstrap) shift; exec "$PYTHON" scripts/bootstrap.py "$@" ;;
  doctor) exec "$PYTHON" -m aegis_os doctor ;;
  ready) exec "$PYTHON" -m aegis_os ready ;;
  serve) exec "$PYTHON" -m aegis_os serve ;;
  acceptance) exec "$PYTHON" scripts/release_acceptance.py ;;
  validate) exec "$PYTHON" scripts/validate.py ;;
  *) echo "Unknown command: $COMMAND" >&2; exit 2 ;;
esac
