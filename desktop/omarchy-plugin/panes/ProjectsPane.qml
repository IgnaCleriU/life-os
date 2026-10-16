import QtQuick

// Columna PROJECTS: proyectos filtrados por estado (`f`) y texto (`/`), con
// tareas abiertas y una barra de progreso hechas/total. Soltar una tarea
// arrastrada sobre un proyecto la mueve ahí.
PaneFrame {
  id: pane
  pane: "projects"
  title: "PROJECTS"
  info: board.projectFilter
  canAdd: true
  filterable: true
  filterText: board.projectText
  onAddClicked: { board.focusTo("projects"); board.runAction("createProject") }

  ListView {
    id: list
    anchors.fill: parent
    model: pane.board.visibleProjects
    currentIndex: pane.board.projectIndex
    boundsBehavior: Flickable.StopAtBounds
    clip: true
    spacing: 1
    onCurrentIndexChanged: positionViewAtIndex(currentIndex, ListView.Contain)

    delegate: Rectangle {
      id: row
      required property var modelData
      required property int index
      readonly property var theme: pane.theme
      readonly property bool current: modelData.id === pane.board.currentProjectId
      readonly property var count: pane.board.counts[modelData.id] || { open: 0, done: 0, total: 0 }
      readonly property bool dropping: drop.containsDrag

      width: ListView.view.width
      height: theme.fontSize * 2.1
      radius: theme.radius
      color: dropping ? theme.tint(theme.magenta, 0.22)
           : current ? theme.tint(theme.accent, pane.focused ? 0.24 : 0.12)
           : hover.containsMouse ? theme.tint(theme.foreground, 0.05) : "transparent"
      border.width: dropping ? 1 : 0
      border.color: theme.magenta

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
        function onPulse(id) { if (id === row.modelData.id) flash.restart() }
      }

      Text {
        id: glyph
        anchors { left: parent.left; leftMargin: row.theme.gap; verticalCenter: parent.verticalCenter }
        width: row.theme.fontSize * 1.2
        text: row.modelData.status === "completed" ? "✓" : row.modelData.status === "archived" ? "▫" : "▸"
        color: row.modelData.status === "completed" ? row.theme.green
             : row.modelData.status === "archived" ? row.theme.dim : row.theme.accent
        font { family: row.theme.fontFamily; pixelSize: row.theme.fontSize }
      }
      Text {
        anchors { left: glyph.right; right: meta.left; rightMargin: row.theme.gap; verticalCenter: parent.verticalCenter }
        text: row.modelData.name
        elide: Text.ElideRight
        color: row.modelData.status === "archived" ? row.theme.dim : row.theme.foreground
        font { family: row.theme.fontFamily; pixelSize: row.theme.fontSize }
      }
      Row {
        id: meta
        anchors { right: parent.right; rightMargin: row.theme.gap; verticalCenter: parent.verticalCenter }
        spacing: row.theme.gap
        Text {
          text: row.count.open > 0 ? row.count.open : ""
          color: row.theme.dim
          font { family: row.theme.fontFamily; pixelSize: row.theme.fontCaption }
          anchors.verticalCenter: parent.verticalCenter
        }
        Rectangle {
          width: row.theme.fontSize * 3.4
          height: 4
          radius: 2
          anchors.verticalCenter: parent.verticalCenter
          color: row.theme.tint(row.theme.foreground, 0.14)
          Rectangle {
            height: parent.height
            radius: 2
            color: row.theme.green
            width: row.count.total > 0 ? parent.width * row.count.done / row.count.total : 0
            Behavior on width { NumberAnimation { duration: 250 } }
          }
        }
      }

      MouseArea {
        id: hover
        anchors.fill: parent
        hoverEnabled: true
        onClicked: { pane.board.focusTo("projects"); pane.board.selectProject(row.modelData.id) }
        onDoubleClicked: pane.board.focusTo("tasks")
      }
      DropArea {
        id: drop
        anchors.fill: parent
        keys: ["lifeos-task"]
        onDropped: function(dropEvent) {
          pane.board.moveTasks(pane.board.dragGhost.dragTasks, row.modelData.id)
          dropEvent.accept()
        }
      }
    }

    Text {
      visible: list.count === 0
      anchors { left: parent.left; right: parent.right; top: parent.top; margins: pane.theme.gap * 1.5 }
      wrapMode: Text.WordWrap
      text: !pane.board.loaded ? "Loading…" : "No " + pane.board.projectFilter + " projects. Press a to create one, or f to change the filter."
      color: pane.theme.dim
      font { family: pane.theme.fontFamily; pixelSize: pane.theme.fontSmall }
    }
  }
}
