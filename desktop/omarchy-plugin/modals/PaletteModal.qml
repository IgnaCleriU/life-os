import QtQuick
import "../lib/keymap.js" as Keymap
import "../lib/format.js" as Format

// Paleta de comandos (^k, modo PALETTE): los mismos atajos del registro,
// filtrados por el panel con foco y buscables por nombre.
ModalFrame {
  id: pal
  name: "palette"
  accentColor: theme.cyan

  property var rows: []
  property var matches: []
  property int cursor: 0

  function open() {
    var scope = board.scopeForPane[board.focusPane]
    var fallback = Keymap.SCOPE_FALLBACK[scope] || scope
    rows = Keymap.groupedForHelp(Keymap.ENTRIES, "global")
      .concat(Keymap.groupedForHelp(Keymap.ENTRIES, fallback))
      .filter(function(r) { return r.palette })
    heading = "command palette · " + board.focusPane + " pane"
    input.text = ""
    refilter()
    show()
    input.forceActiveFocus()
  }

  function refilter() {
    var q = input.text
    matches = rows.filter(function(r) { return Format.fuzzyMatch(q, r.label) })
    cursor = 0
  }

  function run(i) {
    var row = matches[i]
    if (!row) return
    hide()
    board.runAction(row.action)
  }

  Column {
    width: parent.width
    spacing: pal.theme.gap

    TextInput {
      id: input
      width: parent.width
      color: pal.theme.foreground
      font { family: pal.theme.fontFamily; pixelSize: pal.theme.fontTitle }
      onTextEdited: pal.refilter()
      Keys.onPressed: function(event) {
        var ctrl = event.modifiers & Qt.ControlModifier
        if (event.key === Qt.Key_Escape || (ctrl && event.key === Qt.Key_K)) pal.hide()
        else if (event.key === Qt.Key_Down || (ctrl && event.key === Qt.Key_N)) pal.cursor = Math.min(pal.cursor + 1, pal.matches.length - 1)
        else if (event.key === Qt.Key_Up || (ctrl && event.key === Qt.Key_P)) pal.cursor = Math.max(pal.cursor - 1, 0)
        else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) pal.run(pal.cursor)
        else return
        event.accepted = true
      }
      Text {
        visible: input.text === ""
        text: "type a command…"
        color: pal.theme.dim
        font: input.font
      }
    }

    ListView {
      width: parent.width
      height: Math.min(contentHeight, pal.theme.fontSize * 2 * 10)
      clip: true
      model: pal.matches
      currentIndex: pal.cursor
      onCurrentIndexChanged: positionViewAtIndex(currentIndex, ListView.Contain)
      delegate: Rectangle {
        required property var modelData
        required property int index
        width: ListView.view.width
        height: pal.theme.fontSize * 2
        radius: pal.theme.radius
        color: index === pal.cursor ? pal.theme.tint(pal.theme.accent, 0.22) : "transparent"
        Text {
          anchors { left: parent.left; leftMargin: pal.theme.gap; verticalCenter: parent.verticalCenter }
          text: modelData.label
          color: pal.theme.foreground
          font { family: pal.theme.fontFamily; pixelSize: pal.theme.fontSize }
        }
        Text {
          anchors { right: parent.right; rightMargin: pal.theme.gap; verticalCenter: parent.verticalCenter }
          text: modelData.keys.join("  ")
          color: pal.theme.dim
          font { family: pal.theme.fontFamily; pixelSize: pal.theme.fontSmall }
        }
        MouseArea { anchors.fill: parent; onClicked: pal.run(index) }
      }
    }

    Text {
      visible: pal.matches.length === 0
      text: "no matches"
      color: pal.theme.dim
      font { family: pal.theme.fontFamily; pixelSize: pal.theme.fontSmall }
    }
  }
}
