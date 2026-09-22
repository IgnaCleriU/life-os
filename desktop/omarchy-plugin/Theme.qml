import QtQuick
import Quickshell.Io
import qs.Commons

// Colores y tipografía del tablero, tomados del tema activo de Omarchy.
//
// La base (fondo, texto, acento, urgente, superficies de menú) sale de los
// singletons de `qs.Commons`, así el tablero cambia junto con el resto del
// shell. Los colores semánticos que esos singletons no exponen (verde para
// "hecha", amarillo para "en curso", magenta para la selección) se leen del
// mismo `colors.toml` del tema, con los valores de Tokyo Night como respaldo.
QtObject {
  id: theme

  readonly property color background: Color.background
  readonly property color foreground: Color.foreground
  readonly property color accent: Color.accent
  readonly property color red: Color.urgent
  readonly property color muted: Color.muted
  readonly property color dim: Qt.rgba(foreground.r, foreground.g, foreground.b, 0.5)

  readonly property color surface: Color.menu.background
  readonly property color border: Color.menu.border
  readonly property color scrim: Color.menu.scrim
  readonly property color selectedBackground: Color.menu.selectedBackground
  readonly property color selectedText: Color.menu.selectedText

  property color green: "#9ece6a"
  property color yellow: "#e0af68"
  property color magenta: "#bb9af7"
  property color cyan: "#7dcfff"

  readonly property string fontFamily: Style.font.menuFamily
  readonly property int fontSize: Style.font.body
  readonly property int fontSmall: Style.font.bodySmall
  readonly property int fontCaption: Style.font.caption
  readonly property int fontTitle: Style.font.title
  readonly property int radius: Style.cornerRadius
  readonly property int gap: Style.spacing.lg
  readonly property int padding: Style.spacing.panelPadding
  readonly property int gapsOut: Style.gapsOut

  function tint(c, alpha) {
    return Qt.rgba(c.r, c.g, c.b, alpha)
  }

  function loadColors(raw) {
    var keys = { green: "green", yellow: "yellow", magenta: "bright_magenta", cyan: "bright_cyan" }
    var found = {}
    var lines = String(raw || "").split("\n")
    for (var i = 0; i < lines.length; i++) {
      var m = lines[i].match(/^\s*([A-Za-z0-9_-]+)\s*=\s*["']?(#[0-9A-Fa-f]{6})/)
      if (m) found[m[1]] = m[2]
    }
    if (found.green) theme.green = found.green
    if (found.yellow) theme.yellow = found.yellow
    theme.magenta = found.bright_magenta || found.magenta || theme.magenta
    theme.cyan = found.bright_cyan || found.cyan || theme.cyan
  }

  property FileView colorsFile: FileView {
    path: Color.currentThemePath + "/colors.toml"
    watchChanges: true
    printErrors: false
    onFileChanged: reload()
    onLoaded: theme.loadColors(text())
  }

  // Un cambio de tema llega al shell por IPC y actualiza `Color`; se relee
  // el archivo en ese momento en vez de depender solo del watcher.
  property Connections themeSwitch: Connections {
    target: Color
    function onAccentChanged() { theme.colorsFile.reload() }
    function onBackgroundChanged() { theme.colorsFile.reload() }
  }
}
