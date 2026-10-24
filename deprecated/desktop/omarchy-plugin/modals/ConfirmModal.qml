import QtQuick

// Confirmación de borrado: y/Enter confirma, n/Esc/q cancela.
ModalFrame {
  id: confirm
  name: "confirm"
  heading: "confirm"
  accentColor: theme.red
  boxWidth: Math.min(theme.fontSize * 40, width * 0.9)

  property string message: ""
  property var yesCallback: null

  function open(text, callback) {
    message = text
    yesCallback = callback
    show()
  }

  function yes() {
    var cb = yesCallback
    hide()
    if (cb) cb()
  }

  Keys.onPressed: function(event) {
    var t = event.text
    if (t === "y" || event.key === Qt.Key_Return || event.key === Qt.Key_Enter) yes()
    else if (t === "n" || t === "q" || event.key === Qt.Key_Escape) hide()
    event.accepted = true
  }

  Column {
    width: parent.width
    spacing: confirm.theme.gap * 1.5
    Text {
      width: parent.width
      text: confirm.message
      wrapMode: Text.WordWrap
      color: confirm.theme.foreground
      font { family: confirm.theme.fontFamily; pixelSize: confirm.theme.fontSize }
    }
    Row {
      anchors.right: parent.right
      spacing: confirm.theme.gap
      Repeater {
        model: [{ label: "No  n", yes: false }, { label: "Delete  y", yes: true }]
        delegate: Rectangle {
          required property var modelData
          width: label.implicitWidth + confirm.theme.gap * 3
          height: confirm.theme.fontSize * 2
          radius: confirm.theme.radius
          color: "transparent"
          border.width: 1
          border.color: modelData.yes ? confirm.theme.red : confirm.theme.tint(confirm.theme.foreground, 0.3)
          Text {
            id: label
            anchors.centerIn: parent
            text: modelData.label
            color: modelData.yes ? confirm.theme.red : confirm.theme.foreground
            font { family: confirm.theme.fontFamily; pixelSize: confirm.theme.fontSmall }
          }
          MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: modelData.yes ? confirm.yes() : confirm.hide() }
        }
      }
    }
  }
}
