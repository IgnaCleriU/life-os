#!/usr/bin/env bash
# Instala el cliente de escritorio de Life OS para el usuario actual
# (ADR 0009, spec 0002). No usa sudo ni toca la base de datos.
#
#   desktop/install.sh              instala/actualiza y arranca el daemon
#   desktop/install.sh --no-start   instala sin habilitar ni arrancar la unidad
#   desktop/install.sh --uninstall  quita la unidad y el plugin
#
# Qué hace:
#   1. Instala ~/.config/systemd/user/lifeos-daemon.service apuntando al
#      `lifeos-daemon` del venv de este checkout (backend/.venv).
#   2. Enlaza desktop/omarchy-plugin como el plugin `lifeos.board` del shell
#      de Omarchy (~/.config/omarchy/plugins/lifeos.board) y, si el shell
#      está corriendo, lo re-escanea y pide habilitarlo (Omarchy confirma en
#      la terminal: es código de terceros).
#   3. `systemctl --user enable --now lifeos-daemon`.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DAEMON="$REPO/backend/.venv/bin/lifeos-daemon"
CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
UNIT_DIR="$CONFIG_HOME/systemd/user"
UNIT="$UNIT_DIR/lifeos-daemon.service"
PLUGIN_ID="lifeos.board"
PLUGIN_SOURCE="$REPO/desktop/omarchy-plugin"
PLUGIN_LINK="$CONFIG_HOME/omarchy/plugins/$PLUGIN_ID"

have_systemctl() { command -v systemctl >/dev/null 2>&1; }

uninstall() {
  if have_systemctl; then
    systemctl --user disable --now lifeos-daemon.service 2>/dev/null || true
  fi
  rm -f "$UNIT"
  if command -v omarchy >/dev/null 2>&1; then
    omarchy plugin disable "$PLUGIN_ID" 2>/dev/null || true
  fi
  if [ -L "$PLUGIN_LINK" ]; then
    rm "$PLUGIN_LINK"
  fi
  if have_systemctl; then
    systemctl --user daemon-reload 2>/dev/null || true
  fi
  echo "Removed the lifeos-daemon unit and the $PLUGIN_ID plugin link."
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

link_plugin() {
  mkdir -p "$(dirname "$PLUGIN_LINK")"
  if [ -L "$PLUGIN_LINK" ]; then
    ln -sfn "$PLUGIN_SOURCE" "$PLUGIN_LINK"
  elif [ -e "$PLUGIN_LINK" ]; then
    echo "error: $PLUGIN_LINK exists and is not a link; move it away first." >&2
    exit 1
  else
    ln -s "$PLUGIN_SOURCE" "$PLUGIN_LINK"
  fi
  echo "Linked $PLUGIN_LINK -> $PLUGIN_SOURCE"
}

enable_plugin() {
  if ! command -v omarchy-shell >/dev/null 2>&1 || ! command -v omarchy >/dev/null 2>&1; then
    echo "Omarchy shell not found: enable the plugin later with 'omarchy plugin enable $PLUGIN_ID'."
    return
  fi
  omarchy-shell -q shell rescanPlugins || true
  omarchy plugin enable "$PLUGIN_ID" || echo "Enable it later with 'omarchy plugin enable $PLUGIN_ID'."
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
    link_plugin
    if [ "${1:-}" != "--no-start" ]; then
      start_unit
      enable_plugin
    fi
    echo
    echo "Next: bind a key to 'omarchy-shell shell toggle $PLUGIN_ID' (see docs/desktop.md)."
    ;;
  *)
    echo "usage: $0 [--no-start | --uninstall]" >&2
    exit 2
    ;;
esac
