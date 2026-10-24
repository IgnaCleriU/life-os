import QtQuick
import "../lib/format.js" as Format

// Columna TASK: la tarea del cursor, con controles clicables para estado,
// prioridad, fecha y proyecto, y la descripción editable en el mismo panel
// (`E`), sin suspender el tablero para abrir `$EDITOR` como hace la TUI.
PaneFrame {
  id: pane
  pane: "detail"
  title: "TASK"
  info: board.currentTask ? board.currentTask.id.slice(0, 8) : ""

  readonly property var task: board.currentTask
  property string editingTaskId: ""

  function editDescription() {
    if (!task) return
    board.focusPane = "detail"
    desc.forceActiveFocus()
    desc.cursorPosition = desc.text.length
  }

  function syncDescription() {
    if (!desc.activeFocus) desc.text = task ? (task.description || "") : ""
  }

  onTaskChanged: syncDescription()

  Flickable {
    anchors.fill: parent
    anchors.margins: pane.theme.gap
    contentHeight: column.height
    clip: true
    boundsBehavior: Flickable.StopAtBounds
    visible: pane.task !== null

    Column {
      id: column
      width: parent.width
      spacing: pane.theme.gap * 1.5

      Text {
        width: parent.width
        text: pane.task ? pane.task.title : ""
        wrapMode: Text.WordWrap
        color: pane.theme.foreground
        font { family: pane.theme.fontFamily; pixelSize: pane.theme.fontTitle; bold: true }
        MouseArea {
          anchors.fill: parent
          cursorShape: Qt.IBeamCursor
          onClicked: pane.board.runAction("renameTask")
        }
      }

      Grid {
        columns: 2
        columnSpacing: pane.theme.gap * 1.5
        rowSpacing: pane.theme.gap
        verticalItemAlignment: Grid.AlignVCenter

        Label { text: "STATUS" }
        Segmented {
          options: [
            { value: "todo", label: "· todo" },
            { value: "doing", label: "◐ doing" },
            { value: "done", label: "✓ done" }
          ]
          current: pane.task ? pane.task.status : ""
          onPicked: function(v) {
            var labels = { todo: "reopened", doing: "started", done: "completed" }
            pane.board.setTaskStatus([pane.task], v, labels[v], { toast: false })
          }
        }

        Label { text: "PRIORITY" }
        Segmented {
          options: [{ value: "low", label: "low" }, { value: "medium", label: "medium" }, { value: "high", label: "high" }]
          current: pane.task ? pane.task.priority : ""
          onPicked: function(v) { pane.board.setPriority([pane.task], v) }
        }

        Label { text: "DUE" }
        Chip {
          text: !pane.task ? "" : pane.task.due_date
                ? Format.dueLabel(pane.task.due_date, pane.board.today) + " · " + pane.task.due_date
                : "none · @ to set"
          textColor: {
            var u = pane.task ? Format.dueUrgency(pane.task, pane.board.today) : ""
            return u === "overdue" ? pane.theme.red : u === "soon" ? pane.theme.yellow : pane.theme.foreground
          }
          onClicked: pane.board.runAction("setDueDate")
        }

        Label { text: "PROJECT" }
        Chip {
          text: pane.task ? pane.board.projectName(pane.task.project_id) : ""
          onClicked: pane.board.runAction("moveTask")
        }
      }

      Label { text: "DESCRIPTION" }

      Rectangle {
        width: parent.width
        height: Math.max(pane.theme.fontSize * 9, desc.contentHeight + pane.theme.gap * 2)
        radius: pane.theme.radius
        color: pane.theme.tint(pane.theme.background, 0.5)
        border.width: 1
        border.color: desc.activeFocus ? pane.theme.green : pane.theme.tint(pane.theme.foreground, 0.16)

        TextEdit {
          id: desc
          anchors { fill: parent; margins: pane.theme.gap }
          wrapMode: TextEdit.Wrap
          selectByMouse: true
          color: pane.theme.foreground
          font { family: pane.theme.fontFamily; pixelSize: pane.theme.fontSmall }
          onActiveFocusChanged: {
            pane.board.editingDescription = activeFocus
            if (activeFocus) {
              pane.editingTaskId = pane.task ? pane.task.id : ""
            } else if (pane.editingTaskId) {
              pane.board.saveDescription(pane.editingTaskId, text)
              pane.editingTaskId = ""
            }
          }
          Keys.onPressed: function(event) {
            if (event.key === Qt.Key_Escape) {
              pane.board.restoreFocus()
              event.accepted = true
            }
          }
        }
        Text {
          visible: desc.text === "" && !desc.activeFocus
          anchors { fill: parent; margins: pane.theme.gap }
          text: "No description. Press E (or click) to write one."
          color: pane.theme.dim
          wrapMode: Text.WordWrap
          font { family: pane.theme.fontFamily; pixelSize: pane.theme.fontSmall }
        }
      }

      Text {
        width: parent.width
        wrapMode: Text.WordWrap
        text: desc.activeFocus ? "Saved when you leave the field (Esc). Undo with u." : ""
        color: pane.theme.dim
        font { family: pane.theme.fontFamily; pixelSize: pane.theme.fontCaption }
      }
    }
  }

  Text {
    visible: pane.task === null
    anchors { left: parent.left; right: parent.right; top: parent.top; margins: pane.theme.gap * 1.5 }
    text: "No task selected."
    color: pane.theme.dim
    font { family: pane.theme.fontFamily; pixelSize: pane.theme.fontSmall }
  }

  component Label: Text {
    color: pane.theme.dim
    font { family: pane.theme.fontFamily; pixelSize: pane.theme.fontCaption; letterSpacing: 1.5 }
  }

  component Chip: Rectangle {
    id: chip
    property alias text: chipText.text
    property color textColor: pane.theme.foreground
    signal clicked()
    width: chipText.implicitWidth + pane.theme.gap * 2
    height: pane.theme.fontSize * 1.9
    radius: pane.theme.radius
    color: "transparent"
    border.width: 1
    border.color: chipArea.containsMouse ? pane.theme.accent : pane.theme.tint(pane.theme.foreground, 0.25)
    Text {
      id: chipText
      anchors.centerIn: parent
      color: chip.textColor
      font { family: pane.theme.fontFamily; pixelSize: pane.theme.fontSmall }
    }
    MouseArea { id: chipArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: chip.clicked() }
  }

  component Segmented: Row {
    id: seg
    property var options: []
    property string current: ""
    signal picked(string value)
    spacing: pane.theme.gap / 2
    Repeater {
      model: seg.options
      delegate: Rectangle {
        required property var modelData
        readonly property bool on: modelData.value === seg.current
        width: segText.implicitWidth + pane.theme.gap * 2
        height: pane.theme.fontSize * 1.9
        radius: pane.theme.radius
        color: on ? pane.theme.tint(pane.theme.accent, 0.22) : "transparent"
        border.width: 1
        border.color: on || segArea.containsMouse ? pane.theme.accent : pane.theme.tint(pane.theme.foreground, 0.25)
        Text {
          id: segText
          anchors.centerIn: parent
          text: modelData.label
          color: on ? pane.theme.foreground : pane.theme.dim
          font { family: pane.theme.fontFamily; pixelSize: pane.theme.fontSmall }
        }
        MouseArea {
          id: segArea
          anchors.fill: parent
          hoverEnabled: true
          cursorShape: Qt.PointingHandCursor
          onClicked: if (!parent.on) seg.picked(parent.modelData.value)
        }
      }
    }
  }
}
