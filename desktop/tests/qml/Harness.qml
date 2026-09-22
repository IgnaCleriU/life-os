import QtQuick

// Anfitrión de prueba: monta BoardView (sin la ventana layer-shell de
// Board.qml) sobre un fondo, con el mismo Theme y Api que usa el plugin.
Rectangle {
  width: 1400
  height: 820
  color: "#0e0e14"

  Theme { id: theme }
  Api { id: api }

  BoardView {
    id: view
    objectName: "board"
    api: api
    theme: theme
    anchors.centerIn: parent
    width: Math.min(theme.fontSize * 110, parent.width - 40)
    height: Math.min(theme.fontSize * 64, parent.height - 40)
    onNotifyRequested: function(title, body) { console.log("NOTIFY", title, "|", body) }
    onCopyRequested: function(text) { console.log("COPY", text) }
    onDismissRequested: console.log("DISMISS")
  }
}
