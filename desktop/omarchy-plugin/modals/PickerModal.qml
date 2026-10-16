import QtQuick

// Elegir una opción entre pocas: prioridad, mover a proyecto, filtros.
// j/k o flechas, Enter/l o el número, Esc/q/h para salir; también con clic.
ModalFrame {
  id: picker
  name: "picker"
  boxWidth: Math.min(theme.fontSize * 34, width * 0.9)

  property var items: []
  property int cursor: 0
  property var pickCallback: null

  function open(title, options, current, callback) {
    heading = title
    items = options
    pickCallback = callback
    cursor = 0
    for (var i = 0; i < options.length; i++) if (options[i].value === current) cursor = i
    show()
  }

  function pick(i) {
    var cb = pickCallback
    var value = items[i].value
    hide()
    if (cb) cb(value)
  }

  Keys.onPressed: function(event) {
    var t = event.text
    if (event.key === Qt.Key_Down || t === "j") cursor = Math.min(cursor + 1, items.length - 1)
    else if (event.key === Qt.Key_Up || t === "k") cursor = Math.max(cursor - 1, 0)
    else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter || t === "l") pick(cursor)
    else if (t >= "1" && t <= "9" && Number(t) <= items.length) pick(Number(t) - 1)
    else if (event.key === Qt.Key_Escape || t === "q" || t === "h") hide()
    event.accepted = true
  }

  Column {
    width: parent.width
    Repeater {
      model: picker.items
      delegate: Rectangle {
        required property var modelData
        required property int index
        width: parent.width
        height: picker.theme.fontSize * 2.1
        radius: picker.theme.radius
        color: index === picker.cursor ? picker.theme.tint(picker.theme.accent, 0.22) : area.containsMouse ? picker.theme.tint(picker.theme.foreground, 0.05) : "transparent"
        Text {
          anchors { left: parent.left; leftMargin: picker.theme.gap; verticalCenter: parent.verticalCenter }
          text: (index + 1) + "  " + modelData.label
          color: picker.theme.foreground
          font { family: picker.theme.fontFamily; pixelSize: picker.theme.fontSize }
        }
        Text {
          anchors { right: parent.right; rightMargin: picker.theme.gap; verticalCenter: parent.verticalCenter }
          text: modelData.hint || ""
          color: picker.theme.dim
          font { family: picker.theme.fontFamily; pixelSize: picker.theme.fontSmall }
        }
        MouseArea { id: area; anchors.fill: parent; hoverEnabled: true; onClicked: picker.pick(index) }
      }
    }
  }
}
