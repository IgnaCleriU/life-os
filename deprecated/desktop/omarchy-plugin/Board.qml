import Quickshell
import Quickshell.Wayland
import QtQuick

// Punto de entrada del plugin de Omarchy (`lifeos.board`, tipo overlay).
//
// El shell de Omarchy lo carga y lo invoca con
// `omarchy-shell shell toggle lifeos.board`. `keepLoaded` (manifest.json)
// mantiene la instancia entre invocaciones: la selección, los filtros y el
// historial de deshacer sobreviven a ocultar el tablero, y el sondeo de
// cambios sigue corriendo para avisar lo que agregue el agente.
//
// Todo lo visible vive en BoardView.qml; acá solo está la ventana
// layer-shell y la integración con el escritorio (notificaciones,
// portapapeles).
Item {
  id: root

  property string omarchyPath: Quickshell.env("OMARCHY_PATH")
  property var shell: null
  property var manifest: null

  property bool opened: false
  readonly property string pluginId: (manifest && manifest.id) || "lifeos.board"

  function open(payloadJson) {
    root.opened = true
    Qt.callLater(function() { view.restoreFocus() })
  }

  function close() {
    root.opened = false
  }

  function dismiss() {
    root.opened = false
    if (root.shell && typeof root.shell.hide === "function") root.shell.hide(root.pluginId)
  }

  function toggle() {
    if (root.opened) root.dismiss()
    else root.open("{}")
  }

  function notify(title, body) {
    // Clic en la notificación: abre el tablero.
    var reopen = ["--exec", "omarchy-shell", "shell", "summon", root.pluginId, "{}"]
    if (root.omarchyPath)
      Quickshell.execDetached([root.omarchyPath + "/bin/omarchy-notification-send", "--app-name", "Life OS", title, body].concat(reopen))
    else
      Quickshell.execDetached(["notify-send", "--app-name=Life OS", title, body])
  }

  Theme { id: theme }
  Api { id: api }

  PanelWindow {
    id: panel
    visible: root.opened
    anchors { top: true; bottom: true; left: true; right: true }
    color: "transparent"
    WlrLayershell.namespace: "lifeos-board"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: root.opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    exclusionMode: ExclusionMode.Ignore

    Rectangle {
      anchors.fill: parent
      color: theme.scrim
    }

    MouseArea {
      anchors.fill: parent
      onClicked: root.dismiss()
    }

    BoardView {
      id: view
      api: api
      theme: theme
      shown: root.opened
      anchors.centerIn: parent
      width: Math.min(theme.fontSize * 110, panel.width - theme.gapsOut * 2 - 48)
      height: Math.min(theme.fontSize * 64, panel.height - theme.gapsOut * 2 - 48)
      onDismissRequested: root.dismiss()
      onNotifyRequested: function(title, body) { root.notify(title, body) }
      onCopyRequested: function(text) { Quickshell.execDetached(["wl-copy", "--", text]) }
    }
  }
}
