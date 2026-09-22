.pragma library
// Registro de atajos del tablero: la única fuente de verdad para dispatch,
// paleta (^k) y overlay de ayuda (?), igual que el registro de la TUI
// (backend/src/lifeos/adapters/tui/keymap.py).
//
// Las teclas usan los mismos nombres canónicos que la TUI ("j", "G", "gg",
// "ctrl+k", "shift+tab", "slash", "question_mark", "at", "space", "escape")
// y los mismos scopes ("global", "context" = PROJECTS, "collection" = TASKS,
// "detail" = TASK). Así el test de paridad compara ambos registros tal cual
// (ver desktop/tests/keymap.test.mjs).
//
// `action` es un id; BoardView.qml lo resuelve a una función.

var ENTRIES = [
  // --- global (shell) -------------------------------------------------------
  { scope: "global", key: "h", label: "focus previous pane", action: "focusPrev" },
  { scope: "global", key: "l", label: "focus next pane", action: "focusNext" },
  { scope: "global", key: "shift+tab", label: "focus previous pane", action: "focusPrev" },
  { scope: "global", key: "tab", label: "focus next pane", action: "focusNext" },
  { scope: "global", key: "j", label: "cursor down", action: "cursorDown", palette: false },
  { scope: "global", key: "k", label: "cursor up", action: "cursorUp", palette: false },
  { scope: "global", key: "down", label: "cursor down", action: "cursorDown", palette: false },
  { scope: "global", key: "up", label: "cursor up", action: "cursorUp", palette: false },
  { scope: "global", key: "gg", label: "first item", action: "first" },
  { scope: "global", key: "G", label: "last item", action: "last" },
  { scope: "global", key: "ctrl+d", label: "half-page down", action: "pageDown", palette: false },
  { scope: "global", key: "ctrl+u", label: "half-page up", action: "pageUp", palette: false },
  { scope: "global", key: "R", label: "reload from the daemon", action: "reload" },
  { scope: "global", key: "q", label: "hide the board", action: "hide" },
  { scope: "global", key: "escape", label: "back one level", action: "back", palette: false },
  { scope: "global", key: "slash", label: "filter", action: "filter" },
  { scope: "global", key: "ctrl+k", label: "command palette", action: "palette", palette: false },
  { scope: "global", key: "question_mark", label: "keybindings overlay", action: "help" },
  { scope: "global", key: "u", label: "undo", action: "undo" },
  { scope: "global", key: "ctrl+r", label: "redo", action: "redo" },

  // --- PROJECTS (context) ---------------------------------------------------
  { scope: "context", key: "a", label: "create a project", action: "createProject" },
  { scope: "context", key: "e", label: "rename project", action: "renameProject" },
  { scope: "context", key: "enter", label: "open project tasks", action: "focusNext" },
  { scope: "context", key: "c", label: "complete project", action: "completeProject" },
  { scope: "context", key: "A", label: "archive/activate project", action: "toggleArchiveProject" },
  { scope: "context", key: "dd", label: "delete project", action: "deleteProject" },
  { scope: "context", key: "f", label: "filter by status", action: "filterProjects" },

  // --- TASKS (collection) ---------------------------------------------------
  { scope: "collection", key: "a", label: "add a task (quick-add)", action: "addTask" },
  { scope: "collection", key: "o", label: "add a task (quick-add)", action: "addTask" },
  { scope: "collection", key: "enter", label: "open task detail", action: "focusNext" },
  { scope: "collection", key: "space", label: "cycle status", action: "cycleStatus" },
  { scope: "collection", key: "c", label: "complete task", action: "completeTask" },
  { scope: "collection", key: "s", label: "start task", action: "startTask" },
  { scope: "collection", key: "r", label: "reopen task", action: "reopenTask" },
  { scope: "collection", key: "e", label: "rename task", action: "renameTask" },
  { scope: "collection", key: "E", label: "edit description (inline)", action: "editDescription" },
  { scope: "collection", key: "at", label: "set due date", action: "setDueDate" },
  { scope: "collection", key: "p", label: "priority picker", action: "setPriority" },
  { scope: "collection", key: "m", label: "move to another project", action: "moveTask" },
  { scope: "collection", key: "dd", label: "delete task", action: "deleteTask" },
  { scope: "collection", key: "f", label: "filter menu", action: "filterTasks" },
  { scope: "collection", key: "S", label: "cycle sort order", action: "cycleSort" },
  { scope: "collection", key: "x", label: "toggle selection", action: "toggleSelect" },
  { scope: "collection", key: "v", label: "toggle selection", action: "toggleSelect" },
  { scope: "collection", key: "y", label: "copy task as markdown", action: "copyTask" }
]

// El panel de detalle muestra la tarea del cursor, así que ahí rigen los
// mismos atajos que en TASKS (en la TUI el detalle solo tiene los globales;
// esto es un superset, no un cambio de significado).
var SCOPE_FALLBACK = { detail: "collection" }

function forScope(entries, scope) {
  var effective = SCOPE_FALLBACK[scope] || scope
  var out = []
  for (var i = 0; i < entries.length; i++) {
    var s = entries[i].scope
    if (s === "global" || s === scope || s === effective) out.push(entries[i])
  }
  return out
}

function resolve(entries, scope, key) {
  var list = forScope(entries, scope)
  for (var i = 0; i < list.length; i++) if (list[i].key === key) return list[i]
  return null
}

function isPrefix(entries, scope, key) {
  var list = forScope(entries, scope)
  for (var i = 0; i < list.length; i++) {
    var k = list[i].key
    if (k !== key && k.indexOf(key) === 0) return true
  }
  return false
}

// Pares [corta, larga] donde la tecla corta es prefijo estricto de la larga
// dentro de un mismo scope efectivo y ambas son secuencias de caracteres
// sueltos ("d" vs "dd"). Los nombres de tecla ("tab", "escape") no son
// secuencias tecleadas, así que "e" no "colisiona" con "escape".
function prefixCollisions(entries) {
  var scopes = ["global", "context", "collection", "detail"]
  var found = []
  for (var s = 0; s < scopes.length; s++) {
    var list = forScope(entries, scopes[s])
    for (var i = 0; i < list.length; i++) {
      for (var j = 0; j < list.length; j++) {
        var a = list[i].key, b = list[j].key
        if (a === b || !isTypedSequence(a) || !isTypedSequence(b)) continue
        if (b.length > a.length && b.indexOf(a) === 0) found.push([list[i], list[j]])
      }
    }
  }
  return found
}

var NAMED_KEYS = {
  "shift+tab": true, tab: true, escape: true, slash: true, question_mark: true,
  at: true, space: true, enter: true, up: true, down: true
}

function isTypedSequence(key) {
  return !NAMED_KEYS[key] && key.indexOf("ctrl+") !== 0
}

var DISPLAY = {
  "shift+tab": "⇧Tab", tab: "Tab", escape: "Esc", slash: "/", question_mark: "?",
  at: "@", space: "Space", enter: "Enter", up: "↑", down: "↓",
  "ctrl+d": "^d", "ctrl+u": "^u", "ctrl+k": "^k", "ctrl+r": "^r"
}

function displayKey(key) {
  return DISPLAY[key] || key
}

// Entradas agrupadas por acción para la ayuda y la paleta: una fila por
// acción de un scope, con todas sus teclas ("j ↓").
function groupedForHelp(entries, scope) {
  var rows = []
  var index = {}
  for (var i = 0; i < entries.length; i++) {
    var e = entries[i]
    if (e.scope !== scope) continue
    var id = e.action + "|" + e.label
    if (index[id] === undefined) {
      index[id] = rows.length
      rows.push({ action: e.action, label: e.label, keys: [], palette: e.palette !== false })
    }
    rows[index[id]].keys.push(displayKey(e.key))
  }
  return rows
}
