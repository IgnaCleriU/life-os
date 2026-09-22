.pragma library
// Funciones puras de presentación y filtrado del tablero. Sin Qt: se testean
// en node (desktop/tests/format.test.mjs).

var STATUS_GLYPHS = { todo: "·", doing: "◐", done: "✓" }
var NEXT_STATUS = { todo: "doing", doing: "done", done: "todo" }
var PRIORITY_RANK = { high: 0, medium: 1, low: 2 }
var SORT_ORDERS = ["created", "due", "priority"]
var TASK_FILTERS = ["all", "open", "todo", "doing", "done"]
var PROJECT_FILTERS = ["active", "completed", "archived", "all"]

function pad2(n) { return (n < 10 ? "0" : "") + n }

function isoDate(d) {
  return d.getFullYear() + "-" + pad2(d.getMonth() + 1) + "-" + pad2(d.getDate())
}

function parseIso(s) {
  var p = String(s).split("-")
  return new Date(Number(p[0]), Number(p[1]) - 1, Number(p[2]))
}

function startOfDay(d) {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate())
}

function dayDiff(iso, today) {
  return Math.round((parseIso(iso) - startOfDay(today)) / 86400000)
}

var WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

// "overdue 2d", "today", "tomorrow", "Fri 25", "Oct 04".
function dueLabel(iso, today) {
  if (!iso) return ""
  var n = dayDiff(iso, today)
  if (n < 0) return "overdue " + (-n) + "d"
  if (n === 0) return "today"
  if (n === 1) return "tomorrow"
  var d = parseIso(iso)
  if (n < 7) return WEEKDAYS[d.getDay()] + " " + d.getDate()
  return MONTHS[d.getMonth()] + " " + pad2(d.getDate())
}

// "overdue" | "soon" | "" — el color lo decide la vista.
function dueUrgency(task, today) {
  if (!task.due_date || task.status === "done") return ""
  var n = dayDiff(task.due_date, today)
  if (n < 0) return "overdue"
  if (n <= 1) return "soon"
  return ""
}

function glyph(status) { return STATUS_GLYPHS[status] || "?" }
function nextStatus(status) { return NEXT_STATUS[status] || "todo" }

function priorityMark(priority) {
  if (priority === "high") return "!!"
  if (priority === "low") return "·"
  return ""
}

// Igual que `y` en la TUI: "- [ ] título" / "- [x] título", con la fecha.
function markdownLine(task) {
  var line = "- [" + (task.status === "done" ? "x" : " ") + "] " + task.title
  if (task.due_date) line += " (due " + task.due_date + ")"
  return line
}

function matchesText(value, text) {
  if (!text) return true
  return String(value).toLowerCase().indexOf(String(text).toLowerCase()) !== -1
}

function filterProjects(projects, statusFilter, text) {
  var out = []
  for (var i = 0; i < projects.length; i++) {
    var p = projects[i]
    if (statusFilter !== "all" && p.status !== statusFilter) continue
    if (!matchesText(p.name, text)) continue
    out.push(p)
  }
  return out
}

function taskMatchesStatus(task, statusFilter) {
  if (statusFilter === "all") return true
  if (statusFilter === "open") return task.status !== "done"
  return task.status === statusFilter
}

function compareTasks(order) {
  if (order === "due") {
    return function(a, b) {
      var da = a.due_date || "9999-99-99", db = b.due_date || "9999-99-99"
      if (da !== db) return da < db ? -1 : 1
      return a.created_at < b.created_at ? -1 : a.created_at > b.created_at ? 1 : 0
    }
  }
  if (order === "priority") {
    return function(a, b) {
      var d = PRIORITY_RANK[a.priority] - PRIORITY_RANK[b.priority]
      if (d !== 0) return d
      return a.created_at < b.created_at ? -1 : a.created_at > b.created_at ? 1 : 0
    }
  }
  return function(a, b) {
    return a.created_at < b.created_at ? -1 : a.created_at > b.created_at ? 1 : 0
  }
}

function visibleTasks(tasks, projectId, statusFilter, text, order) {
  var out = []
  for (var i = 0; i < tasks.length; i++) {
    var t = tasks[i]
    if (t.project_id !== projectId) continue
    if (!taskMatchesStatus(t, statusFilter)) continue
    if (!matchesText(t.title, text)) continue
    out.push(t)
  }
  out.sort(compareTasks(order))
  return out
}

function nextInCycle(list, current) {
  var i = list.indexOf(current)
  return list[(i + 1) % list.length]
}

// { <projectId>: { open, done, total } }
function projectCounts(tasks) {
  var counts = {}
  for (var i = 0; i < tasks.length; i++) {
    var t = tasks[i]
    var c = counts[t.project_id] || (counts[t.project_id] = { open: 0, done: 0, total: 0 })
    c.total++
    if (t.status === "done") c.done++
    else c.open++
  }
  return counts
}

// Índice a mostrar tras un refresco: el mismo id si sigue visible, si no el
// índice anterior acotado a la lista (así borrar no manda el cursor arriba).
function cursorIndex(list, id, previousIndex) {
  for (var i = 0; i < list.length; i++) if (list[i].id === id) return i
  if (list.length === 0) return -1
  return Math.max(0, Math.min(previousIndex, list.length - 1))
}

// Subsecuencia difusa para la paleta: "cmp" encuentra "complete project".
function fuzzyMatch(query, text) {
  var q = String(query).toLowerCase(), s = String(text).toLowerCase()
  var j = 0
  for (var i = 0; i < q.length; i++) {
    if (q.charAt(i) === " ") continue
    j = s.indexOf(q.charAt(i), j)
    if (j === -1) return false
    j++
  }
  return true
}

// Diff de refresco para notificar cambios hechos fuera del tablero (MCP,
// CLI, TUI): tareas nuevas agrupadas por proyecto.
function addedTasks(before, after) {
  var known = {}
  for (var i = 0; i < before.length; i++) known[before[i].id] = true
  var out = []
  for (var j = 0; j < after.length; j++) if (!known[after[j].id]) out.push(after[j])
  return out
}

function summarizeAdded(added, projectsById) {
  var byProject = {}
  var order = []
  for (var i = 0; i < added.length; i++) {
    var pid = added[i].project_id
    if (!byProject[pid]) { byProject[pid] = 0; order.push(pid) }
    byProject[pid]++
  }
  var parts = []
  for (var k = 0; k < order.length; k++) {
    var n = byProject[order[k]]
    var p = projectsById[order[k]]
    parts.push(n + (n === 1 ? " task" : " tasks") + " added to " + (p ? p.name : "a project"))
  }
  return parts.join(", ")
}
