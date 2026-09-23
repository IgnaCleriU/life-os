import QtQuick
import "../lib/format.js" as Format

// Columna TASKS: tareas del proyecto actual, filtradas (`f`, `/`) y
// ordenadas (`S`). Clic en el glifo cambia el estado, Ctrl+clic selecciona,
// y arrastrar una fila (o la selección) sobre un proyecto la mueve.
PaneFrame {
  id: pane
  pane: "tasks"
  title: "TASKS"
  info: board.taskFilter + " · " + board.sortOrder
  canAdd: true
  filterable: true
  filterText: board.taskText
  onAddClicked: { board.focusTo("tasks"); board.runAction("addTask") }

  ListView {
    id: list
    anchors.fill: parent
    model: pane.board.visibleTasks
    currentIndex: pane.board.taskIndex
    boundsBehavior: Flickable.StopAtBounds
    clip: true
    spacing: 1
    onCurrentIndexChanged: positionViewAtIndex(currentIndex, ListView.Contain)

    delegate: Rectangle {
      id: row
      required property var modelData
      required property int index
      readonly property var theme: pane.theme
      readonly property var task: modelData
      readonly property bool current: task.id === pane.board.currentTaskId
      readonly property bool isSelected: pane.board.selected[task.id] === true
      readonly property string urgency: Format.dueUrgency(task, pane.board.today)

      width: ListView.view.width
      height: theme.fontSize * 2.1
      radius: theme.radius
      color: isSelected ? theme.tint(theme.magenta, 0.16)
           : current ? theme.tint(theme.accent, pane.focused ? 0.24 : 0.12)
           : mouse.containsMouse ? theme.tint(theme.foreground, 0.05) : "transparent"

      Rectangle {
        id: flashRect
        anchors.fill: parent
        radius: parent.radius
        color: row.theme.green
        opacity: 0
      }
      NumberAnimation { id: flash; target: flashRect; property: "opacity"; from: 0.4; to: 0; duration: 900; easing.type: Easing.OutCubic }
      Connections {
        target: pane.board
        function onPulse(id) { if (id === row.task.id) flash.restart() }
      }

      Rectangle {
        visible: row.isSelected
        anchors { left: parent.left; top: parent.top; bottom: parent.bottom; topMargin: 4; bottomMargin: 4 }
        width: 3
        radius: 1
        color: row.theme.magenta
      }

      MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        drag.target: pane.board.dragGhost
        drag.threshold: 8
        onPressed: function(ev) {
          pane.board.focusTo("tasks")
          var p = mapToItem(pane.board.dragGhost.parent, ev.x, ev.y)
          pane.board.dragGhost.x = p.x - 12
          pane.board.dragGhost.y = p.y - 12
        }
        onClicked: function(ev) {
          if (ev.modifiers & Qt.ControlModifier) pane.board.toggleSelect(row.task.id)
          else pane.board.selectTask(row.task.id)
        }
        onDoubleClicked: { pane.board.selectTask(row.task.id); pane.board.focusTo("detail") }
        drag.onActiveChanged: {
          if (drag.active) pane.board.startDrag(row.task)
          else pane.board.endDrag()
        }
      }

      Text {
        id: glyph
        anchors { left: parent.left; leftMargin: row.theme.gap; verticalCenter: parent.verticalCenter }
        width: row.theme.fontSize * 1.4
        horizontalAlignment: Text.AlignHCenter
        text: Format.glyph(row.task.status)
        color: row.task.status === "done" ? row.theme.green
             : row.task.status === "doing" ? row.theme.yellow : row.theme.foreground
        font { family: row.theme.fontFamily; pixelSize: row.theme.fontSize; bold: true }
        MouseArea {
          anchors.fill: parent
          anchors.margins: -4
          cursorShape: Qt.PointingHandCursor
          onClicked: { pane.board.selectTask(row.task.id); pane.board.cycleStatus(row.task) }
        }
      }

      Text {
        anchors { left: glyph.right; leftMargin: row.theme.gap / 2; right: meta.left; rightMargin: row.theme.gap; verticalCenter: parent.verticalCenter }
        text: row.task.title
        elide: Text.ElideRight
        color: row.task.status === "done" ? row.theme.dim : row.theme.foreground
        font { family: row.theme.fontFamily; pixelSize: row.theme.fontSize; strikeout: row.task.status === "done" }
      }

      Row {
        id: meta
        anchors { right: parent.right; rightMargin: row.theme.gap; verticalCenter: parent.verticalCenter }
        spacing: row.theme.gap
        Text {
          text: Format.priorityMark(row.task.priority)
          visible: text !== ""
          color: row.task.priority === "high" ? row.theme.red : row.theme.dim
          font { family: row.theme.fontFamily; pixelSize: row.theme.fontSmall; bold: true }
        }
        Text {
          text: Format.dueLabel(row.task.due_date, pane.board.today)
          visible: text !== ""
          color: row.urgency === "overdue" ? row.theme.red : row.urgency === "soon" ? row.theme.yellow : row.theme.dim
          font { family: row.theme.fontFamily; pixelSize: row.theme.fontSmall }
        }
      }
    }

    Text {
      visible: list.count === 0
      anchors { left: parent.left; right: parent.right; top: parent.top; margins: pane.theme.gap * 1.5 }
      wrapMode: Text.WordWrap
      text: !pane.board.loaded ? "Loading…"
          : !pane.board.currentProject ? "Select a project."
          : "No tasks here. Press a (or +) to add one."
      color: pane.theme.dim
      font { family: pane.theme.fontFamily; pixelSize: pane.theme.fontSmall }
    }
  }
}
