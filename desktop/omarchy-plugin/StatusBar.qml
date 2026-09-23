import QtQuick

// Barra de estado: modo actual, secuencia pendiente, selección, última acción
// o error, atajos del panel con foco y el estado de la conexión al daemon.
Rectangle {
  id: bar

  property var board
  readonly property var theme: board.theme
  readonly property var modeColors: ({
    NORMAL: theme.accent, INSERT: theme.green, FILTER: theme.yellow,
    SELECT: theme.magenta, PALETTE: theme.cyan
  })
  readonly property var hints: ({
    projects: "a new · e rename · c complete · A archive · f filter · l tasks",
    tasks: "a add · space cycle · @ due · p priority · m move · x select · dd delete",
    detail: "E description · e title · @ due · p priority · h back"
  })

  height: Math.round(theme.fontSize * 2.3)
  color: theme.tint(theme.background, 0.55)
  radius: theme.radius

  Rectangle {
    anchors { left: parent.left; right: parent.right; top: parent.top }
    height: 1
    color: bar.theme.tint(bar.theme.foreground, 0.12)
  }

  Row {
    anchors { left: parent.left; leftMargin: bar.theme.padding; right: right.left; rightMargin: bar.theme.gap * 2; verticalCenter: parent.verticalCenter }
    spacing: bar.theme.gap * 1.5
    clip: true

    Rectangle {
      width: modeText.implicitWidth + bar.theme.gap * 2
      height: bar.theme.fontSize * 1.5
      radius: bar.theme.radius
      color: bar.modeColors[bar.board.mode] || bar.theme.accent
      Text {
        id: modeText
        anchors.centerIn: parent
        text: bar.board.mode
        color: bar.theme.background
        font { family: bar.theme.fontFamily; pixelSize: bar.theme.fontCaption; bold: true; letterSpacing: 1 }
      }
    }
    Text {
      visible: bar.board.pendingKeys !== ""
      text: bar.board.pendingKeys + "…"
      color: bar.theme.yellow
      font { family: bar.theme.fontFamily; pixelSize: bar.theme.fontSmall }
      anchors.verticalCenter: parent.verticalCenter
    }
    Text {
      visible: bar.board.selectedCount > 0
      text: bar.board.selectedCount + " selected"
      color: bar.theme.magenta
      font { family: bar.theme.fontFamily; pixelSize: bar.theme.fontSmall }
      anchors.verticalCenter: parent.verticalCenter
    }
    Text {
      text: bar.board.errorText ? "✗ " + bar.board.errorText : bar.board.lastAction
      color: bar.board.errorText ? bar.theme.red : bar.theme.foreground
      elide: Text.ElideRight
      font { family: bar.theme.fontFamily; pixelSize: bar.theme.fontSmall }
      anchors.verticalCenter: parent.verticalCenter
    }
  }

  Row {
    id: right
    anchors { right: parent.right; rightMargin: bar.theme.padding; verticalCenter: parent.verticalCenter }
    spacing: bar.theme.gap * 2
    Text {
      text: bar.hints[bar.board.focusPane] || ""
      color: bar.theme.dim
      font { family: bar.theme.fontFamily; pixelSize: bar.theme.fontCaption }
      anchors.verticalCenter: parent.verticalCenter
      visible: bar.width > bar.theme.fontSize * 70
    }
    Text {
      readonly property var api: bar.board.api
      text: api.online ? "● " + api.baseUrl.replace("http://", "")
          : api.status === "connecting" ? "● connecting…"
          : "● daemon unreachable · systemctl --user status lifeos-daemon"
      color: api.online ? bar.theme.green : api.status === "connecting" ? bar.theme.yellow : bar.theme.red
      font { family: bar.theme.fontFamily; pixelSize: bar.theme.fontCaption }
      anchors.verticalCenter: parent.verticalCenter
    }
  }
}
