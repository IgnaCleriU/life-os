import QtQuick

// Base de los modales del tablero: velo sobre el tablero, caja arriba al
// centro y cierre con clic afuera. Solo uno a la vez (`board.activeModal`).
FocusScope {
  id: modal

  property var board
  property string name: ""
  property string heading: ""
  property color accentColor: board.theme.accent
  property real boxWidth: Math.min(board.theme.fontSize * 50, width * 0.9)
  default property alias content: inner.data
  readonly property bool active: board.activeModal === name
  readonly property var theme: board.theme

  signal dismissed()

  visible: active
  z: 50

  function show() {
    board.activeModal = name
    forceActiveFocus()
  }

  function hide() {
    if (board.activeModal === name) board.activeModal = ""
    board.restoreFocus()
  }

  Rectangle {
    anchors.fill: parent
    color: modal.theme.tint(modal.theme.background, 0.45)
    radius: modal.theme.radius
    MouseArea {
      anchors.fill: parent
      onClicked: { modal.hide(); modal.dismissed() }
    }
  }

  Rectangle {
    id: box
    anchors { horizontalCenter: parent.horizontalCenter; top: parent.top; topMargin: parent.height * 0.12 }
    width: modal.boxWidth
    height: title.height + inner.childrenRect.height + modal.theme.gap * 3
    color: modal.theme.surface
    radius: modal.theme.radius
    border.width: 1
    border.color: modal.accentColor

    MouseArea { anchors.fill: parent }

    Text {
      id: title
      anchors { left: parent.left; right: parent.right; top: parent.top; margins: modal.theme.gap * 1.5 }
      text: modal.heading.toUpperCase()
      elide: Text.ElideRight
      color: modal.theme.dim
      font { family: modal.theme.fontFamily; pixelSize: modal.theme.fontCaption; letterSpacing: 1.5 }
    }

    Item {
      id: inner
      anchors { left: parent.left; right: parent.right; top: title.bottom; margins: modal.theme.gap * 1.5 }
      height: childrenRect.height
    }
  }
}
