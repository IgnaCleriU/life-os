#!/usr/bin/env bash
# Instala el cliente de escritorio de Life OS para el usuario actual
# (ADR 0009, spec 0002). No usa sudo ni toca la base de datos.
#
#   desktop/install.sh              instala/actualiza y arranca el daemon
#   desktop/install.sh --no-start   instala sin habilitar ni arrancar la unidad
#   desktop/install.sh --uninstall  quita la unidad y el enlace de Quickshell
#
# Qué hace:
#   1. Instala ~/.config/systemd/user/lifeos-daemon.service apuntando al
#      `lifeos-daemon` del venv de este checkout (backend/.venv).
#   2. Enlaza desktop/quickshell/lifeos en ~/.config/quickshell/lifeos.
#   3. `systemctl --user enable --now lifeos-daemon`.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DAEMON="$REPO/backend/.venv/bin/lifeos-daemon"
CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
UNIT_DIR="$CONFIG_HOME/systemd/user"
UNIT="$UNIT_DIR/lifeos-daemon.service"
QS_SOURCE="$REPO/desktop/quickshell/lifeos"
QS_LINK="$CONFIG_HOME/quickshell/lifeos"

have_systemctl() { command -v systemctl >/dev/null 2>&1; }

uninstall() {
  if have_systemctl; then
    systemctl --user disable --now lifeos-daemon.service 2>/dev/null || true
  fi
  rm -f "$UNIT"
  if [ -L "$QS_LINK" ]; then
    rm "$QS_LINK"
  fi
  if have_systemctl; then
    systemctl --user daemon-reload 2>/dev/null || true
  fi
  echo "Removed the lifeos-daemon unit and the Quickshell link."
  echo "Your data in \${XDG_DATA_HOME:-~/.local/share}/life-os/ was not touched."
}

install_unit() {
  if [ ! -x "$DAEMON" ]; then
    echo "error: $DAEMON not found." >&2
    echo "Run 'uv sync --all-extras' in $REPO/backend first." >&2
    exit 1
  fi
  mkdir -p "$UNIT_DIR"
  sed -e "s|@LIFEOS_DAEMON@|$DAEMON|g" -e "s|@REPO@|$REPO|g" \
    "$REPO/desktop/systemd/lifeos-daemon.service" >"$UNIT"
  echo "Installed $UNIT"
}

link_quickshell() {
  if [ ! -d "$QS_SOURCE" ]; then
    echo "Skipping Quickshell: $QS_SOURCE does not exist in this checkout."
    return
  fi
  mkdir -p "$(dirname "$QS_LINK")"
  if [ -L "$QS_LINK" ]; then
    ln -sfn "$QS_SOURCE" "$QS_LINK"
  elif [ -e "$QS_LINK" ]; then
    echo "error: $QS_LINK exists and is not a link; move it away first." >&2
    exit 1
  else
    ln -s "$QS_SOURCE" "$QS_LINK"
  fi
  echo "Linked $QS_LINK -> $QS_SOURCE"
}

start_unit() {
  if ! have_systemctl; then
    echo "systemctl not found: start the daemon with '$DAEMON' instead."
    return
  fi
  systemctl --user daemon-reload
  systemctl --user enable --now lifeos-daemon.service
  # `restart` recoge un venv o una unidad actualizados en una reinstalación.
  systemctl --user restart lifeos-daemon.service
  echo "lifeos-daemon is running: systemctl --user status lifeos-daemon"
}

case "${1:-}" in
  --uninstall)
    uninstall
    ;;
  --no-start | "")
    install_unit
    link_quickshell
    if [ "${1:-}" != "--no-start" ]; then
      start_unit
    fi
    echo
    echo "Next: add the Hyprland binds from docs/desktop.md."
    ;;
  *)
    echo "usage: $0 [--no-start | --uninstall]" >&2
    exit 2
    ;;
esac
