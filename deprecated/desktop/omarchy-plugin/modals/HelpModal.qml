import QtQuick
import "../lib/keymap.js" as Keymap

// Overlay de atajos (?), generado del mismo registro que el dispatch y la
// paleta, así ninguno de los tres puede divergir de los otros.
ModalFrame {
  id: help
  name: "help"
  heading: "keybindings · generated from the registry"
  boxWidth: Math.min(theme.fontSize * 72, width * 0.94)

  readonly property var groups: [
    { title: "GLOBAL", rows: Keymap.groupedForHelp(Keymap.ENTRIES, "global") },
    { title: "PROJECTS PANE", rows: Keymap.groupedForHelp(Keymap.ENTRIES, "context") },
    { title: "TASKS & DETAIL PANES", rows: Keymap.groupedForHelp(Keymap.ENTRIES, "collection") }
  ]

  function open() { show() }

  Keys.onPressed: function(event) {
    var t = event.text
    if (event.key === Qt.Key_Escape || t === "?" || t === "q") help.hide()
    else if (t === "j" || event.key === Qt.Key_Down) flick.contentY = Math.min(flick.contentY + 40, Math.max(0, flick.contentHeight - flick.height))
    else if (t === "k" || event.key === Qt.Key_Up) flick.contentY = Math.max(flick.contentY - 40, 0)
    event.accepted = true
  }

  Flickable {
    id: flick
    width: parent.width
    height: Math.min(contentHeight, help.height * 0.62)
    contentHeight: grid.height
    clip: true
    boundsBehavior: Flickable.StopAtBounds

    Row {
      id: grid
      width: parent.width
      spacing: help.theme.gap * 3
      Repeater {
        model: help.groups
        delegate: Column {
          required property var modelData
          width: (grid.width - grid.spacing * 2) / 3
          spacing: help.theme.gap / 2
          Text {
            text: modelData.title
            color: help.theme.accent
            font { family: help.theme.fontFamily; pixelSize: help.theme.fontCaption; letterSpacing: 1.5 }
            bottomPadding: help.theme.gap / 2
          }
          Repeater {
            model: modelData.rows
            delegate: Item {
              required property var modelData
              width: parent.width
              height: help.theme.fontSize * 1.6
              Text {
                anchors { left: parent.left; right: keys.left; rightMargin: help.theme.gap; verticalCenter: parent.verticalCenter }
                text: modelData.label
                elide: Text.ElideRight
                color: help.theme.dim
                font { family: help.theme.fontFamily; pixelSize: help.theme.fontSmall }
              }
              Text {
                id: keys
                anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                text: modelData.keys.join(" ")
                color: help.theme.foreground
                font { family: help.theme.fontFamily; pixelSize: help.theme.fontSmall }
              }
            }
          }
        }
      }
    }
  }
}
