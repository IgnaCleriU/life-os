import QtQuick
import "lib/keymap.js" as Keymap
import "lib/dispatch.js" as Dispatch
import "lib/undo.js" as Undo
import "lib/format.js" as Format
import "panes"
import "modals"

// El tablero: tres columnas PROJECTS · TASKS · TASK, barra de estado,
// modales y notificaciones. Todo lo que hace pasa por la API REST (`api`);
// no hay lógica de negocio acá, solo estado de interfaz y la traducción de
// teclas/clics a llamadas (ADR 0009).
//
// No depende de Quickshell.Wayland: la ventana layer-shell la pone
// Board.qml. Eso permite cargar este componente en un QQuickView común para
// probarlo sin compositor (desktop/tests/qml/).
FocusScope {
  id: board

  required property var api
  required property var theme
  property bool shown: true

  signal dismissRequested()
  signal notifyRequested(string title, string body)
  signal copyRequested(string text)
  signal pulse(string id)

  // --- datos (tal cual los devuelve la API) ---------------------------------
  property var projects: []
  property var tasks: []
  property string revision: ""
  property bool loaded: false
  property date today: new Date()

  // --- estado de interfaz ---------------------------------------------------
  property string focusPane: "projects"        // projects | tasks | detail
  property string mode: "NORMAL"               // NORMAL | INSERT | FILTER | SELECT | PALETTE
  property string projectFilter: "active"
  property string taskFilter: "all"
  property string sortOrder: "created"
  property string projectText: ""
  property string taskText: ""
  property string filtering: ""                // pane con el filtro abierto
  property string currentProjectId: ""
  property string currentTaskId: ""
  property int projectIndex: -1
  property int taskIndex: -1
  property var selected: ({})
  property int selectedCount: 0
  property string lastAction: ""
  property string errorText: ""
  property string pendingKeys: ""
  property string activeModal: ""

  // --- derivados (se recalculan en recompute()) ----------------------------
  property var visibleProjects: []
  property var visibleTasks: []
  property var counts: ({})
  readonly property var currentProject: findById(projects, currentProjectId)
  readonly property var currentTask: findById(tasks, currentTaskId)

  // Ids a resaltar cuando termine el próximo refresco (las filas se recrean
  // con el modelo nuevo; un pulso anterior se perdería).
  property var queuedPulses: []

  function queuePulse(id) {
    queuedPulses = queuedPulses.concat([id])
  }

  function flushPulses() {
    var q = queuedPulses
    queuedPulses = []
    Qt.callLater(function() { for (var i = 0; i < q.length; i++) board.pulse(q[i]) })
  }

  function restoreFocus() {
    keyCatcher.forceActiveFocus()
  }

  property var keyBuffer: Dispatch.createBuffer()
  property var undoStack: Undo.createStack()
  readonly property var scopeForPane: ({ projects: "context", tasks: "collection", detail: "detail" })
  readonly property var panes: ["projects", "tasks", "detail"]

  function findById(list, id) {
    if (!id) return null
    for (var i = 0; i < list.length; i++) if (list[i].id === id) return list[i]
    return null
  }

  function projectName(id) {
    var p = findById(projects, id)
    return p ? p.name : "—"
  }

  // ==========================================================================
  // Datos
  // ==========================================================================

  function recompute() {
    counts = Format.projectCounts(tasks)
    var vp = Format.filterProjects(projects, projectFilter, projectText)
    visibleProjects = vp
    var pi = Format.cursorIndex(vp, currentProjectId, projectIndex)
    var nextProjectId = pi >= 0 ? vp[pi].id : ""
    if (nextProjectId !== currentProjectId) {
      currentProjectId = nextProjectId
      clearSelection()
    }
    projectIndex = pi

    var vt = Format.visibleTasks(tasks, currentProjectId, taskFilter, taskText, sortOrder)
    visibleTasks = vt
    var ti = Format.cursorIndex(vt, currentTaskId, taskIndex)
    currentTaskId = ti >= 0 ? vt[ti].id : ""
    taskIndex = ti
    updateMode()
  }

  // Recarga proyectos y tareas. `external` indica que la recarga la disparó
  // un cambio de revisión ajeno (MCP, CLI, TUI): se avisa qué se agregó.
  //
  // La revisión se pide *antes* que los datos y se guarda solo si la recarga
  // salió bien: una escritura que caiga en el medio deja una revisión más
  // nueva que la guardada y el próximo sondeo vuelve a recargar; una recarga
  // fallida no marca nada como visto, así que el sondeo la reintenta.
  property bool refreshing: false

  function refresh(external) {
    refreshing = true
    function fail(r) { board.refreshing = false; showApiError(r) }
    api.request("GET", "/revision", null, function(v) {
      if (!v.ok) { fail(v); return }
      var rev = v.data.revision
      api.request("GET", "/projects", null, function(r) {
        if (!r.ok) { fail(r); return }
        var nextProjects = r.data
        api.request("GET", "/tasks", null, function(t) {
          if (!t.ok) { fail(t); return }
          var previous = board.tasks
          board.today = new Date()
          board.projects = nextProjects
          board.tasks = t.data
          board.revision = rev
          var wasLoaded = board.loaded
          board.loaded = true
          board.refreshing = false
          board.recompute()
          if (external && wasLoaded) announceExternal(previous, t.data)
          board.flushPulses()
        })
      })
    })
  }

  function announceExternal(before, after) {
    var added = Format.addedTasks(before, after)
    if (added.length === 0) return
    var byId = {}
    for (var i = 0; i < projects.length; i++) byId[projects[i].id] = projects[i]
    var summary = Format.summarizeAdded(added, byId)
    for (var j = 0; j < added.length; j++) board.queuePulse(added[j].id)
    if (board.shown) toasts.show(summary, "agent", false)
    else board.notifyRequested("Life OS", summary)
  }

  function poll() {
    if (board.refreshing) return
    api.request("GET", "/revision", null, function(r) {
      if (!r.ok || board.refreshing) return
      if (!board.loaded) board.refresh(false)
      else if (r.data.revision !== board.revision) board.refresh(true)
    })
  }

  Timer {
    id: syncTimer
    interval: board.api.online ? (board.shown ? 1000 : 5000) : 3000
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: board.poll()
  }

  Connections {
    target: board.api
    function onStatusChanged() {
      if (board.api.status === "connecting") board.poll()
    }
  }

  // ==========================================================================
  // Escrituras con deshacer
  // ==========================================================================

  // Corre `calls` (funciones que reciben un callback) en serie; se detiene en
  // el primer error. `done(ok)` al final.
  function runAll(calls, done) {
    var i = 0
    function step() {
      if (i >= calls.length) { done(true); return }
      calls[i++](function(r) {
        if (!r.ok) { showApiError(r); done(false); return }
        step()
      })
    }
    step()
  }

  function call(method, path, body) {
    return function(cb) { api.request(method, path, body, cb) }
  }

  // Ejecuta una escritura y registra cómo deshacerla y rehacerla. `doCalls`,
  // `undoCalls` y `redoCalls` son listas de `call(...)`; si `redoCalls` se
  // omite, rehacer repite `doCalls`.
  function write(label, doCalls, undoCalls, redoCalls, options) {
    runAll(doCalls, function(ok) {
      if (!ok) return
      Undo.push(undoStack, label, undoCalls, redoCalls || doCalls)
      board.lastAction = label
      board.errorText = ""
      if (!options || options.toast !== false) toasts.show(label, "info", true)
      board.refresh(false)
    })
  }

  function undo() {
    var entry = Undo.takeUndo(undoStack)
    if (!entry) { showError("nothing to undo"); return }
    runAll(entry.undo, function(ok) {
      // En falla, runAll ya mostró el error: no se pisa, y la entrada se
      // descarta porque ya no se puede aplicar. En una acción de varios
      // pasos (p. ej. deshacer un borrado en lote) los pasos previos al que
      // falló quedan aplicados: se acepta, porque el caso requiere que otro
      // cliente toque esas mismas tareas en medio, y el error queda a la vista.
      if (ok) {
        board.lastAction = "undo: " + entry.label
        board.errorText = ""
      } else {
        Undo.dropRedo(undoStack, entry)
      }
      board.refresh(false)
    })
  }

  function redo() {
    var entry = Undo.takeRedo(undoStack)
    if (!entry) { showError("nothing to redo"); return }
    runAll(entry.redo, function(ok) {
      if (ok) {
        board.lastAction = "redo: " + entry.label
        board.errorText = ""
      } else {
        Undo.dropUndo(undoStack, entry)
      }
      board.refresh(false)
    })
  }

  function showError(message) {
    errorText = message
  }

  function showApiError(r) {
    var e = r.error || { code: "error", message: "request failed" }
    showError(e.code + ": " + e.message)
    if (e.code !== "daemon_unreachable") toasts.show(e.code + ": " + e.message, "error", false)
  }

  // --- rutas por transición -------------------------------------------------
  readonly property var taskStatusRoute: ({ todo: "reopen", doing: "start", done: "complete" })
  readonly property var projectStatusRoute: ({ active: "activate", archived: "archive", completed: "complete" })

  function taskStatusCall(id, status) {
    return call("POST", "/tasks/" + id + "/" + taskStatusRoute[status], null)
  }

  function projectStatusCall(id, status) {
    return call("POST", "/projects/" + id + "/" + projectStatusRoute[status], null)
  }

  // Tareas sobre las que actúa un comando: la selección si hay, si no la del
  // cursor (como en la TUI).
  function targetTasks() {
    var out = []
    if (selectedCount > 0) {
      for (var i = 0; i < tasks.length; i++) if (selected[tasks[i].id]) out.push(tasks[i])
      return out
    }
    return currentTask ? [currentTask] : []
  }

  function labelFor(ts, verb) {
    return ts.length > 1 ? verb + " " + ts.length + " tasks" : verb + " “" + ts[0].title + "”"
  }

  function setTaskStatus(ts, status, verb, options) {
    if (ts.length === 0) { showError("no task selected"); return }
    var changed = ts.filter(function(t) { return t.status !== status })
    if (changed.length === 0) { showError("already " + status); return }
    for (var i = 0; i < changed.length; i++) board.queuePulse(changed[i].id)
    write(labelFor(changed, verb),
          changed.map(function(t) { return taskStatusCall(t.id, status) }),
          changed.map(function(t) { return taskStatusCall(t.id, t.status) }),
          null, options)
    clearSelection()
  }

  function cycleStatus(task) {
    var t = task || currentTask
    if (!t) { showError("no task selected"); return }
    setTaskStatus([t], Format.nextStatus(t.status), "→ " + Format.nextStatus(t.status) + ":", { toast: false })
  }

  function patchTask(t, fields, label) {
    var before = {}
    for (var k in fields) before[k] = t[k]
    write(label, [call("PATCH", "/tasks/" + t.id, fields)], [call("PATCH", "/tasks/" + t.id, before)], null, { toast: false })
  }

  function setPriority(ts, priority) {
    var changed = ts.filter(function(t) { return t.priority !== priority })
    if (changed.length === 0) return
    write(changed.length > 1 ? "priority " + priority + " on " + changed.length + " tasks" : "priority " + priority + ": " + changed[0].title,
          changed.map(function(t) { return call("PATCH", "/tasks/" + t.id, { priority: priority }) }),
          changed.map(function(t) { return call("PATCH", "/tasks/" + t.id, { priority: t.priority }) }),
          null, { toast: false })
    clearSelection()
  }

  function moveTasks(ts, projectId) {
    var moving = ts.filter(function(t) { return t.project_id !== projectId })
    if (moving.length === 0) return
    board.queuePulse(projectId)
    write(labelFor(moving, "moved") + " → " + projectName(projectId),
          moving.map(function(t) { return call("POST", "/tasks/" + t.id + "/move", { project_id: projectId }) }),
          moving.map(function(t) { return call("POST", "/tasks/" + t.id + "/move", { project_id: t.project_id }) }))
    clearSelection()
  }

  function deleteTasks(ts) {
    write(labelFor(ts, "deleted"),
          ts.map(function(t) { return call("DELETE", "/tasks/" + t.id, null) }),
          ts.map(function(t) { return call("POST", "/tasks/" + t.id + "/restore", null) }))
    clearSelection()
  }

  function saveDescription(taskId, text) {
    var t = findById(tasks, taskId)
    if (!t || (t.description || "") === text) return
    patchTask(t, { description: text === "" ? null : text }, "edited description")
  }

  // ==========================================================================
  // Navegación y modos
  // ==========================================================================

  function updateMode() {
    if (activeModal === "prompt" || editingDescription) mode = "INSERT"
    else if (activeModal === "palette") mode = "PALETTE"
    else if (filtering) mode = "FILTER"
    else if (selectedCount > 0) mode = "SELECT"
    else mode = "NORMAL"
  }

  property bool editingDescription: false
  onEditingDescriptionChanged: updateMode()
  onActiveModalChanged: updateMode()
  onFilteringChanged: updateMode()

  function focusTo(pane) {
    if (filtering && filtering !== pane) filtering = ""
    focusPane = pane
    keyCatcher.forceActiveFocus()
  }

  function focusShift(delta) {
    var i = panes.indexOf(focusPane) + delta
    focusTo(panes[Math.max(0, Math.min(panes.length - 1, i))])
  }

  function selectProject(id) {
    if (id === currentProjectId) return
    currentProjectId = id
    currentTaskId = ""
    taskIndex = 0
    clearSelection()
    recompute()
  }

  function selectTask(id) {
    currentTaskId = id
    recompute()
  }

  function moveCursor(delta, absolute) {
    var pane = focusPane === "detail" ? "tasks" : focusPane
    var list = pane === "projects" ? visibleProjects : visibleTasks
    if (list.length === 0) return
    var cur = pane === "projects" ? projectIndex : taskIndex
    var n = absolute === "first" ? 0 : absolute === "last" ? list.length - 1
          : Math.max(0, Math.min(list.length - 1, cur + delta))
    if (pane === "projects") selectProject(list[n].id)
    else selectTask(list[n].id)
  }

  function back() {
    if (selectedCount > 0) { clearSelection(); lastAction = "selection cleared"; return }
    var pane = focusPane
    if (pane === "projects" && projectText) { projectText = ""; recompute(); lastAction = "filter cleared"; return }
    if (pane === "tasks" && taskText) { taskText = ""; recompute(); lastAction = "filter cleared"; return }
    if (pane === "projects") { board.dismissRequested(); return }
    focusShift(-1)
  }

  function clearSelection() {
    selected = ({})
    selectedCount = 0
    updateMode()
  }

  function toggleSelect(id) {
    var tid = id || currentTaskId
    if (!tid) { showError("no task selected"); return }
    var next = {}
    for (var k in selected) next[k] = selected[k]
    if (next[tid]) delete next[tid]
    else next[tid] = true
    selected = next
    selectedCount = Object.keys(next).length
    lastAction = selectedCount + " selected"
    updateMode()
  }

  function startFilter() {
    if (focusPane === "detail") { showError("nothing to filter in the detail pane"); return }
    filtering = focusPane
  }

  function endFilter(clear) {
    if (clear) {
      if (filtering === "projects") projectText = ""
      else taskText = ""
      recompute()
    }
    filtering = ""
    keyCatcher.forceActiveFocus()
  }

  function setFilterText(pane, text) {
    if (pane === "projects") projectText = text
    else taskText = text
    recompute()
  }

  // ==========================================================================
  // Acciones del keymap (ids de lib/keymap.js)
  // ==========================================================================

  function needProject() {
    if (currentProject) return true
    showError("no project selected")
    return false
  }

  function needTask() {
    if (currentTask) return true
    showError("no task selected")
    return false
  }

  readonly property var actions: ({
    focusPrev: function() { board.focusShift(-1) },
    focusNext: function() {
      if (board.focusPane === "tasks" && !board.needTask()) return
      board.focusShift(1)
    },
    cursorDown: function() { board.moveCursor(1) },
    cursorUp: function() { board.moveCursor(-1) },
    first: function() { board.moveCursor(0, "first") },
    last: function() { board.moveCursor(0, "last") },
    pageDown: function() { board.moveCursor(8) },
    pageUp: function() { board.moveCursor(-8) },
    reload: function() { board.refresh(false); board.lastAction = "reloaded from the daemon" },
    hide: function() { board.dismissRequested() },
    back: function() { board.back() },
    filter: function() { board.startFilter() },
    palette: function() { paletteModal.open() },
    help: function() { help.open() },
    undo: function() { board.undo() },
    redo: function() { board.redo() },

    createProject: function() {
      prompt.open({ title: "new project", placeholder: "project name", onAccept: function(v) {
        if (!v) return "name is required"
        board.api.request("POST", "/projects", { name: v }, function(r) {
          if (!r.ok) { board.showApiError(r); return }
          var id = r.data.id
          Undo.push(board.undoStack, "created project " + v,
                    [board.call("DELETE", "/projects/" + id, null)],
                    [board.call("POST", "/projects/" + id + "/restore", null)])
          board.lastAction = "created project " + v
          if (board.projectFilter !== "all") board.projectFilter = "active"
          board.currentProjectId = id
          board.queuePulse(id)
          board.refresh(false)
        })
      } })
    },
    renameProject: function() {
      if (!board.needProject()) return
      var p = board.currentProject
      prompt.open({ title: "rename project", text: p.name, onAccept: function(v) {
        if (!v) return "name is required"
        if (v === p.name) return
        board.write("renamed " + p.name + " → " + v,
                    [board.call("PATCH", "/projects/" + p.id, { name: v })],
                    [board.call("PATCH", "/projects/" + p.id, { name: p.name })], null, { toast: false })
      } })
    },
    completeProject: function() { board.setProjectStatus("completed") },
    toggleArchiveProject: function() {
      if (!board.needProject()) return
      board.setProjectStatus(board.currentProject.status === "archived" ? "active" : "archived")
    },
    deleteProject: function() {
      if (!board.needProject()) return
      var p = board.currentProject
      confirm.open("Delete project “" + p.name + "”? You can undo it with u.", function() {
        board.write("deleted project " + p.name,
                    [board.call("DELETE", "/projects/" + p.id, null)],
                    [board.call("POST", "/projects/" + p.id + "/restore", null)])
      })
    },
    filterProjects: function() {
      picker.open("project status", Format.PROJECT_FILTERS.map(function(v) { return { value: v, label: v } }),
                  board.projectFilter, function(v) { board.projectFilter = v; board.lastAction = "projects: " + v; board.recompute() })
    },

    addTask: function() { board.openQuickAdd() },
    cycleStatus: function() { board.cycleStatus() },
    completeTask: function() { board.setTaskStatus(board.targetTasks(), "done", "completed") },
    startTask: function() { board.setTaskStatus(board.targetTasks(), "doing", "started") },
    reopenTask: function() { board.setTaskStatus(board.targetTasks(), "todo", "reopened") },
    renameTask: function() {
      if (!board.needTask()) return
      var t = board.currentTask
      prompt.open({ title: "edit title", text: t.title, onAccept: function(v) {
        if (!v) return "title is required"
        if (v === t.title) return
        board.patchTask(t, { title: v }, "renamed task")
      } })
    },
    editDescription: function() {
      if (!board.needTask()) return
      board.focusPane = "detail"
      detailPane.editDescription()
    },
    setDueDate: function() { board.openDuePrompt() },
    setPriority: function() {
      var ts = board.targetTasks()
      if (ts.length === 0) { board.showError("no task selected"); return }
      picker.open("priority", [
        { value: "low", label: "low", hint: "!low" },
        { value: "medium", label: "medium", hint: "!med" },
        { value: "high", label: "high", hint: "!high" }
      ], ts[0].priority, function(v) { board.setPriority(ts, v) })
    },
    moveTask: function() { board.openMovePicker() },
    deleteTask: function() {
      var ts = board.targetTasks()
      if (ts.length === 0) { board.showError("no task selected"); return }
      var what = ts.length > 1 ? ts.length + " tasks" : "“" + ts[0].title + "”"
      confirm.open("Delete " + what + "? You can undo it with u.", function() { board.deleteTasks(ts) })
    },
    filterTasks: function() {
      picker.open("task status", Format.TASK_FILTERS.map(function(v) {
        return { value: v, label: v, hint: v === "open" ? "todo + doing" : "" }
      }), board.taskFilter, function(v) { board.taskFilter = v; board.lastAction = "tasks: " + v; board.recompute() })
    },
    cycleSort: function() {
      board.sortOrder = Format.nextInCycle(Format.SORT_ORDERS, board.sortOrder)
      board.lastAction = "sort: " + board.sortOrder
      board.recompute()
    },
    toggleSelect: function() { board.toggleSelect() },
    copyTask: function() {
      if (!board.needTask()) return
      var md = Format.markdownLine(board.currentTask)
      board.copyRequested(md)
      board.lastAction = "copied as markdown"
      toasts.show("Copied: " + md, "info", false)
    }
  })

  function runAction(id) {
    var fn = actions[id]
    if (fn) fn()
  }

  function setProjectStatus(status) {
    if (!needProject()) return
    var p = currentProject
    if (p.status === status) { showError("already " + status); return }
    board.queuePulse(p.id)
    write(p.name + " → " + status, [projectStatusCall(p.id, status)], [projectStatusCall(p.id, p.status)], null, { toast: false })
  }

  function openQuickAdd() {
    if (!needProject()) return
    var project = currentProject
    prompt.open({
      title: "quick-add · default #" + project.name,
      placeholder: "buy air filters !high @sat #casa",
      previewRequest: function(text, cb) {
        if (!text.trim()) { cb(null); return }
        board.api.request("POST", "/quick-add/preview", { text: text, default_project_id: project.id }, function(r) {
          cb(r.ok ? r.data : null)
        })
      },
      onAccept: function(v, preview) {
        if (!v) return "title is required"
        if (preview && preview.error) return preview.error.code + ": " + preview.error.message
        board.api.request("POST", "/quick-add", { text: v, default_project_id: project.id }, function(r) {
          if (!r.ok) { board.showApiError(r); return }
          var t = r.data
          Undo.push(board.undoStack, "created “" + t.title + "”",
                    [board.call("DELETE", "/tasks/" + t.id, null)],
                    [board.call("POST", "/tasks/" + t.id + "/restore", null)])
          board.lastAction = "created “" + t.title + "” in " + board.projectName(t.project_id)
          board.currentProjectId = t.project_id
          board.currentTaskId = t.id
          board.focusPane = "tasks"
          board.queuePulse(t.id)
          board.refresh(false)
        })
      }
    })
  }

  function openDuePrompt() {
    if (!needTask()) return
    var t = currentTask
    // Mismo parser que quick-add: el preview devuelve la fecha de "x @<texto>".
    function asQuickAdd(v) { return "x @" + v.replace(/^@/, "") }
    prompt.open({
      title: "due date · today, tomorrow, mon..sun, YYYY-MM-DD · empty clears",
      text: t.due_date || "",
      placeholder: "sat",
      previewRequest: function(text, cb) {
        if (!text.trim()) { cb({ clears: true }); return }
        board.api.request("POST", "/quick-add/preview", { text: asQuickAdd(text.trim()), default_project_id: t.project_id }, function(r) {
          cb(r.ok ? { due_date: r.data.due_date, invalid: !r.data.due_date } : null)
        })
      },
      onAccept: function(v, preview) {
        if (!v) {
          if (t.due_date) board.patchTask(t, { due_date: null }, "cleared due date: " + t.title)
          return
        }
        if (/^\d{4}-\d{2}-\d{2}$/.test(v) && !preview) {
          if (v !== t.due_date) board.patchTask(t, { due_date: v }, "due " + v + ": " + t.title)
          return
        }
        if (!preview || preview.invalid) return "invalid date: " + v
        if (preview.due_date !== t.due_date)
          board.patchTask(t, { due_date: preview.due_date }, "due " + Format.dueLabel(preview.due_date, board.today) + ": " + t.title)
      }
    })
  }

  function openMovePicker() {
    var ts = targetTasks()
    if (ts.length === 0) { showError("no task selected"); return }
    var options = []
    for (var i = 0; i < projects.length; i++) {
      var p = projects[i]
      if (p.status === "active" && p.id !== ts[0].project_id) options.push({ value: p.id, label: p.name })
    }
    if (options.length === 0) { showError("no other active project"); return }
    picker.open("move to project", options, "", function(v) { board.moveTasks(ts, v) })
  }

  // ==========================================================================
  // Teclado
  // ==========================================================================

  // Traduce un evento de Qt al nombre canónico del registro ("j", "G",
  // "ctrl+k", "shift+tab", "slash", "at", "space", "escape"...).
  function keyName(event) {
    var k = event.key
    if (k === Qt.Key_Backtab || (k === Qt.Key_Tab && (event.modifiers & Qt.ShiftModifier))) return "shift+tab"
    if (k === Qt.Key_Tab) return "tab"
    if (k === Qt.Key_Escape) return "escape"
    if (k === Qt.Key_Return || k === Qt.Key_Enter) return "enter"
    if (k === Qt.Key_Space) return "space"
    if (k === Qt.Key_Up) return "up"
    if (k === Qt.Key_Down) return "down"
    if (k === Qt.Key_Left) return "h"
    if (k === Qt.Key_Right) return "l"
    if (event.modifiers & Qt.ControlModifier) {
      if (k >= Qt.Key_A && k <= Qt.Key_Z) return "ctrl+" + String.fromCharCode(k - Qt.Key_A + 97)
      return ""
    }
    var t = event.text
    if (t === "/") return "slash"
    if (t === "?") return "question_mark"
    if (t === "@") return "at"
    if (t && t.length === 1 && t.charCodeAt(0) > 32) return t
    return ""
  }

  function handleKey(event) {
    var name = keyName(event)
    if (!name) return false
    var result = Dispatch.feed(keyBuffer, Keymap, scopeForPane[focusPane], name)
    pendingKeys = keyBuffer.pending
    if (result.kind === "matched") {
      errorText = ""
      runAction(result.entry.action)
      return true
    }
    return result.kind === "waiting" || name.length === 1
  }

  FocusScope {
    id: keyCatcher
    anchors.fill: parent
    focus: true
    Keys.onPressed: function(event) {
      if (board.handleKey(event)) event.accepted = true
    }
  }

  // ==========================================================================
  // Vista
  // ==========================================================================

  readonly property alias dragGhost: ghost

  function startDrag(task) {
    var ts = selected[task.id] ? targetTasks() : [task]
    ghost.dragTasks = ts
    ghost.dragging = true
  }

  function endDrag() {
    if (ghost.dragging) ghost.Drag.drop()
    ghost.dragging = false
    ghost.dragTasks = []
  }

  Rectangle {
    id: card
    anchors.fill: parent
    color: board.theme.surface
    border.color: board.theme.tint(board.theme.accent, 0.45)
    border.width: 1
    radius: board.theme.radius

    // Absorbe los clics sobre el fondo del tablero (para que no lleguen al
    // velo de Board.qml, que lo cierra) y devuelve el foco al teclado.
    MouseArea {
      anchors.fill: parent
      onPressed: board.restoreFocus()
    }

    Row {
      id: header
      anchors { left: parent.left; right: parent.right; top: parent.top; margins: board.theme.padding }
      height: Math.round(board.theme.fontSize * 2)
      spacing: board.theme.gap

      Text {
        text: "LIFE OS"
        color: board.theme.accent
        font { family: board.theme.fontFamily; pixelSize: board.theme.fontSmall; bold: true; letterSpacing: 2 }
        anchors.verticalCenter: parent.verticalCenter
      }
      Text {
        text: "projects & tasks"
        color: board.theme.dim
        font { family: board.theme.fontFamily; pixelSize: board.theme.fontSmall }
        anchors.verticalCenter: parent.verticalCenter
      }
    }

    Row {
      anchors { right: parent.right; top: parent.top; margins: board.theme.padding }
      height: header.height
      spacing: board.theme.gap * 2
      Repeater {
        model: [
          { key: "^k", label: "commands", action: "palette" },
          { key: "?", label: "keys", action: "help" },
          { key: "q", label: "hide", action: "hide" }
        ]
        delegate: Text {
          required property var modelData
          text: modelData.key + " " + modelData.label
          color: hint.containsMouse ? board.theme.foreground : board.theme.dim
          font { family: board.theme.fontFamily; pixelSize: board.theme.fontCaption }
          anchors.verticalCenter: parent.verticalCenter
          MouseArea { id: hint; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: board.runAction(modelData.action) }
        }
      }
    }

    Item {
      id: columns
      anchors {
        left: parent.left; right: parent.right; top: header.bottom; bottom: statusBar.top
        leftMargin: board.theme.padding; rightMargin: board.theme.padding
        topMargin: board.theme.gap; bottomMargin: board.theme.gap
      }
      // Anchos enteros: un borde de 1 px en coordenadas fraccionales se
      // dibuja a medias y los bordes tenues directamente desaparecen.
      readonly property real unit: (width - board.theme.gap * 2) / 3.6
      // Sin daemon quedan a la vista los últimos datos, atenuados; las
      // escrituras fallan con `daemon_unreachable` en la barra de estado.
      opacity: board.api.online || !board.loaded ? 1 : 0.5
      Behavior on opacity { NumberAnimation { duration: 200 } }

      ProjectsPane {
        id: projectsPane
        board: board
        x: 0
        width: Math.round(columns.unit * 0.95)
        height: Math.floor(parent.height)
      }
      TasksPane {
        id: tasksPane
        board: board
        x: projectsPane.width + board.theme.gap
        width: Math.round(columns.unit * 1.5)
        height: Math.floor(parent.height)
      }
      DetailPane {
        id: detailPane
        board: board
        x: tasksPane.x + tasksPane.width + board.theme.gap
        width: Math.floor(columns.width - x)
        height: Math.floor(parent.height)
      }
    }

    StatusBar {
      id: statusBar
      board: board
      anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
    }

    Toasts {
      id: toasts
      board: board
      anchors { right: parent.right; bottom: statusBar.top; margins: board.theme.padding }
    }

    // Fantasma que sigue al puntero al arrastrar tareas hacia un proyecto.
    Rectangle {
      id: ghost
      property var dragTasks: []
      property bool dragging: false
      z: 40
      visible: dragging
      width: ghostText.implicitWidth + board.theme.gap * 2
      height: board.theme.fontSize * 1.9
      radius: board.theme.radius
      color: board.theme.surface
      border.width: 1
      border.color: board.theme.magenta
      Drag.active: dragging
      Drag.keys: ["lifeos-task"]
      Drag.hotSpot.x: 12
      Drag.hotSpot.y: 12
      Text {
        id: ghostText
        anchors.centerIn: parent
        text: ghost.dragTasks.length > 1 ? "move " + ghost.dragTasks.length + " tasks" : ghost.dragTasks.length ? "move “" + ghost.dragTasks[0].title + "”" : ""
        color: board.theme.foreground
        font { family: board.theme.fontFamily; pixelSize: board.theme.fontSmall }
      }
    }

    // --- modales ------------------------------------------------------------
    PromptModal { id: prompt; board: board; anchors.fill: parent }
    PickerModal { id: picker; board: board; anchors.fill: parent }
    ConfirmModal { id: confirm; board: board; anchors.fill: parent }
    PaletteModal { id: paletteModal; board: board; anchors.fill: parent }
    HelpModal { id: help; board: board; anchors.fill: parent }
  }

  // Al volver a mostrarse, el foco va al catcher y se refresca de inmediato.
  onShownChanged: {
    if (shown) {
      keyCatcher.forceActiveFocus()
      poll()
    }
  }

  Component.onCompleted: keyCatcher.forceActiveFocus()
}
