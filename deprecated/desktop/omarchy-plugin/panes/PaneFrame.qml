import QtQuick

// Marco común de las tres columnas: borde que se enciende con el foco,
// encabezado en versalitas y, opcionalmente, la barra de filtro `/`.
Rectangle {
  id: frame

  property var board
  property string pane: ""
  property string title: ""
  property string info: ""
  property bool canAdd: false
  property bool filterable: false
  property string filterText: ""
  signal addClicked()
  default property alias content: body.data

  readonly property var theme: board.theme
  readonly property bool focused: board.focusPane === pane
  readonly property bool filterOpen: filterable && board.filtering === pane

  color: theme.tint(theme.background, 0.35)
  border.width: 1
  border.color: focused ? theme.accent : theme.tint(theme.foreground, 0.16)
  radius: theme.radius
  clip: true

  Behavior on border.color { ColorAnimation { duration: 120 } }

  MouseArea {
    anchors.fill: parent
    onPressed: function(mouse) { board.focusTo(frame.pane); mouse.accepted = false }
  }

  Item {
    id: head
    anchors { left: parent.left; right: parent.right; top: parent.top }
    height: Math.round(frame.theme.fontSize * 2.2)

    Text {
      anchors { left: parent.left; leftMargin: frame.theme.gap * 1.5; verticalCenter: parent.verticalCenter }
      text: frame.title
      color: frame.focused ? frame.theme.accent : frame.theme.dim
      font { family: frame.theme.fontFamily; pixelSize: frame.theme.fontCaption; letterSpacing: 2 }
    }

    Row {
      anchors { right: parent.right; rightMargin: frame.theme.gap; verticalCenter: parent.verticalCenter }
      spacing: frame.theme.gap
      Text {
        text: frame.info
        color: frame.theme.dim
        font { family: frame.theme.fontFamily; pixelSize: frame.theme.fontCaption }
        anchors.verticalCenter: parent.verticalCenter
      }
      Rectangle {
        visible: frame.canAdd
        width: frame.theme.fontSize * 1.8
        height: frame.theme.fontSize * 1.6
        radius: frame.theme.radius
        color: "transparent"
        border.width: 1
        border.color: addArea.containsMouse ? frame.theme.accent : frame.theme.tint(frame.theme.foreground, 0.3)
        Text {
          anchors.centerIn: parent
          text: "+"
          color: frame.theme.foreground
          font { family: frame.theme.fontFamily; pixelSize: frame.theme.fontSize }
        }
        MouseArea {
          id: addArea
          anchors.fill: parent
          hoverEnabled: true
          cursorShape: Qt.PointingHandCursor
          onClicked: frame.addClicked()
        }
      }
    }
  }

  Item {
    id: filterBar
    anchors { left: parent.left; right: parent.right; top: head.bottom; leftMargin: frame.theme.gap; rightMargin: frame.theme.gap }
    height: (frame.filterOpen || frame.filterText) ? Math.round(frame.theme.fontSize * 2) : 0
    visible: height > 0

    Rectangle {
      anchors.fill: parent
      anchors.bottomMargin: frame.theme.gap / 2
      visible: frame.filterOpen
      color: frame.theme.tint(frame.theme.background, 0.6)
      border.width: 1
      border.color: frame.theme.yellow
      radius: frame.theme.radius

      TextInput {
        id: filterInput
        anchors { fill: parent; leftMargin: frame.theme.gap; rightMargin: frame.theme.gap }
        verticalAlignment: TextInput.AlignVCenter
        color: frame.theme.foreground
        font { family: frame.theme.fontFamily; pixelSize: frame.theme.fontSmall }
        selectByMouse: true
        onTextEdited: frame.board.setFilterText(frame.pane, text)
        Keys.onPressed: function(event) {
          if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) { frame.board.endFilter(false); event.accepted = true }
          else if (event.key === Qt.Key_Escape) { frame.board.endFilter(true); event.accepted = true }
        }
      }
    }

    Text {
      visible: !frame.filterOpen && frame.filterText !== ""
      anchors { left: parent.left; leftMargin: frame.theme.gap; verticalCenter: parent.verticalCenter }
      text: "/" + frame.filterText
      color: frame.theme.yellow
      font { family: frame.theme.fontFamily; pixelSize: frame.theme.fontSmall }
    }
  }

  onFilterOpenChanged: {
    if (filterOpen) {
      filterInput.text = filterText
      filterInput.forceActiveFocus()
    }
  }

  Item {
    id: body
    anchors { left: parent.left; right: parent.right; top: filterBar.bottom; bottom: parent.bottom; margins: frame.theme.gap / 2 }
  }
}
