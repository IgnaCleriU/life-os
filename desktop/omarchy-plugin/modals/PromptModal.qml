import QtQuick
import "../lib/format.js" as Format

// Prompt de una línea (modo INSERT): quick-add, renombrar, fecha. Con
// `previewRequest` muestra en vivo cómo se interpreta el texto, pidiendo el
// preview al daemon con debounce; `onAccept(texto, preview)` devuelve un
// mensaje de error para quedarse abierto, o nada para cerrar.
ModalFrame {
  id: prompt
  name: "prompt"
  accentColor: theme.green

  property var options: ({})
  property var preview: null
  property string errorLine: ""
  property bool inFlight: false
  property int generation: 0

  function open(opts) {
    options = opts
    heading = opts.title || ""
    input.text = opts.text || ""
    preview = null
    errorLine = ""
    show()
    input.forceActiveFocus()
    input.cursorPosition = input.text.length
    if (opts.previewRequest) requestPreview(null)
  }

  function requestPreview(then) {
    if (!options.previewRequest) { if (then) then(); return }
    var gen = ++generation
    inFlight = true
    options.previewRequest(input.text, function(data) {
      if (gen !== prompt.generation) return
      prompt.inFlight = false
      prompt.preview = data
      if (then) then()
    })
  }

  function accept() {
    if (debounce.running || inFlight) {
      debounce.stop()
      requestPreview(finish)
      return
    }
    finish()
  }

  function finish() {
    var err = options.onAccept ? options.onAccept(input.text.trim(), preview) : ""
    if (err) { errorLine = err; return }
    hide()
  }

  function chips() {
    var d = preview
    var out = []
    if (!d) return out
    if (d.clears) return [{ text: "clears the due date", kind: "info" }]
    if (d.invalid) return [{ text: "not a date", kind: "error" }]
    if (d.title !== undefined) {
      out.push({ text: d.title || "title…", kind: "title" })
      if (d.project) out.push({ text: "#" + d.project.name + (d.project.id ? "" : " (new)"), kind: "project" })
      if (d.priority && d.priority !== "medium") out.push({ text: "!" + d.priority, kind: "priority" })
    }
    if (d.due_date) out.push({ text: "@" + Format.dueLabel(d.due_date, board.today) + " · " + d.due_date, kind: "due" })
    if (d.error) out.push({ text: d.error.code + ": " + d.error.message, kind: "error" })
    return out
  }

  Timer {
    id: debounce
    interval: 120
    onTriggered: prompt.requestPreview(null)
  }

  Column {
    width: parent.width
    spacing: prompt.theme.gap

    TextInput {
      id: input
      width: parent.width
      color: prompt.theme.foreground
      font { family: prompt.theme.fontFamily; pixelSize: prompt.theme.fontTitle }
      selectByMouse: true
      clip: true
      onTextEdited: { prompt.errorLine = ""; if (prompt.options.previewRequest) debounce.restart() }
      Keys.onPressed: function(event) {
        if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) { prompt.accept(); event.accepted = true }
        else if (event.key === Qt.Key_Escape) { prompt.hide(); event.accepted = true }
      }
      Text {
        visible: input.text === ""
        text: prompt.options.placeholder || ""
        color: prompt.theme.dim
        font: input.font
      }
    }

    Rectangle {
      width: parent.width
      height: 1
      color: prompt.theme.tint(prompt.theme.foreground, 0.12)
      visible: chipFlow.visible
    }

    Flow {
      id: chipFlow
      width: parent.width
      spacing: prompt.theme.gap
      visible: !!prompt.options.previewRequest || prompt.errorLine !== ""
      Repeater {
        model: prompt.chips().concat(prompt.errorLine ? [{ text: prompt.errorLine, kind: "error" }] : [])
        delegate: Rectangle {
          required property var modelData
          readonly property color tone: ({
            title: prompt.theme.foreground, project: prompt.theme.accent, priority: prompt.theme.red,
            due: prompt.theme.cyan, error: prompt.theme.red, info: prompt.theme.dim
          })[modelData.kind] || prompt.theme.foreground
          width: chipText.implicitWidth + prompt.theme.gap * 2
          height: prompt.theme.fontSize * 1.8
          radius: prompt.theme.radius
          color: "transparent"
          border.width: modelData.kind === "title" ? 0 : 1
          border.color: tone
          Text {
            id: chipText
            anchors.centerIn: parent
            text: modelData.text
            color: parent.tone
            font { family: prompt.theme.fontFamily; pixelSize: prompt.theme.fontSmall }
          }
        }
      }
    }
  }
}
