import QtQuick

// Avisos efímeros dentro del tablero: confirmación de escrituras (con
// "undo"), errores y cambios que llegaron de afuera (el agente vía MCP).
// Con el tablero oculto, esos últimos van como notificación del escritorio
// (ver Board.qml).
Column {
  id: toasts

  property var board
  readonly property var theme: board.theme
  spacing: theme.gap
  width: theme.fontSize * 30

  function show(text, kind, withUndo) {
    entries.append({ text: text, kind: kind || "info", withUndo: withUndo === true, born: Date.now() })
    while (entries.count > 3) entries.remove(0)
  }

  ListModel { id: entries }

  Timer {
    interval: 400
    repeat: true
    running: entries.count > 0
    onTriggered: {
      var now = Date.now()
      for (var i = entries.count - 1; i >= 0; i--) {
        var item = entries.get(i)
        var ttl = item.kind === "agent" ? 6000 : item.kind === "error" ? 5000 : 3200
        if (now - item.born > ttl) entries.remove(i)
      }
    }
  }

  Repeater {
    model: entries
    delegate: Rectangle {
      id: toast
      required property string text
      required property string kind
      required property bool withUndo
      required property int index
      readonly property color tone: kind === "agent" ? toasts.theme.magenta : kind === "error" ? toasts.theme.red : toasts.theme.accent

      width: toasts.width
      height: Math.max(toasts.theme.fontSize * 2.6, body.implicitHeight + toasts.theme.gap * 2)
      radius: toasts.theme.radius
      color: toasts.theme.surface
      border.width: 1
      border.color: tone

      Text {
        id: icon
        anchors { left: parent.left; leftMargin: toasts.theme.gap * 1.5; verticalCenter: parent.verticalCenter }
        text: toast.kind === "agent" ? "✦" : toast.kind === "error" ? "✗" : "◐"
        color: toast.tone
        font { family: toasts.theme.fontFamily; pixelSize: toasts.theme.fontSize }
      }
      Text {
        id: body
        anchors { left: icon.right; leftMargin: toasts.theme.gap; right: undo.left; rightMargin: toasts.theme.gap; verticalCenter: parent.verticalCenter }
        text: toast.text
        wrapMode: Text.WordWrap
        color: toasts.theme.foreground
        font { family: toasts.theme.fontFamily; pixelSize: toasts.theme.fontSmall }
      }
      Rectangle {
        id: undo
        visible: toast.withUndo
        anchors { right: parent.right; rightMargin: toasts.theme.gap; verticalCenter: parent.verticalCenter }
        width: visible ? undoText.implicitWidth + toasts.theme.gap * 2 : 0
        height: toasts.theme.fontSize * 1.7
        radius: toasts.theme.radius
        color: "transparent"
        border.width: 1
        border.color: undoArea.containsMouse ? toasts.theme.accent : toasts.theme.tint(toasts.theme.foreground, 0.3)
        Text {
          id: undoText
          anchors.centerIn: parent
          text: "undo u"
          color: toasts.theme.foreground
          font { family: toasts.theme.fontFamily; pixelSize: toasts.theme.fontCaption }
        }
        MouseArea {
          id: undoArea
          anchors.fill: parent
          hoverEnabled: true
          cursorShape: Qt.PointingHandCursor
          onClicked: { entries.remove(toast.index); toasts.board.undo() }
        }
      }
    }
  }
}
