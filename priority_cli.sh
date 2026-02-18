#!/usr/bin/env bash
# Priority override CLI — check, status, clear, restore
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

case "${1:-help}" in
  check)
    shift
    python3 "$SCRIPT_DIR/priority_override.py" check "$@" --dir "$SCRIPT_DIR"
    ;;
  status)
    python3 "$SCRIPT_DIR/priority_override.py" status --dir "$SCRIPT_DIR"
    ;;
  clear)
    python3 "$SCRIPT_DIR/priority_override.py" clear --reason "${2:-manual}" --dir "$SCRIPT_DIR"
    ;;
  restore)
    python3 "$SCRIPT_DIR/priority_override.py" restore --dir "$SCRIPT_DIR"
    ;;
  *)
    echo "Usage: $0 {check <text>|status|clear [reason]|restore}"
    echo ""
    echo "  check <text>   - Check text for priority triggers, activate if found"
    echo "  status         - Show active override"
    echo "  clear [reason] - Clear active override"
    echo "  restore        - Clear override and restore previous mood"
    ;;
esac
