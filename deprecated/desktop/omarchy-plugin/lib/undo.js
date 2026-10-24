.pragma library
// Pila de deshacer/rehacer de la sesión, con la semántica de la TUI
// (backend/src/lifeos/adapters/tui/undo.py): cada escritura registra cómo
// deshacerse y rehacerse; una escritura nueva vacía el rehacer. No persiste:
// vive mientras el shell mantenga cargado el plugin.
//
// `undo`/`redo` de cada entrada son funciones que el tablero arma con
// closures sobre la API; acá solo se decide cuál corre.

function createStack() {
  return { undo: [], redo: [] }
}

function push(stack, label, undoFn, redoFn) {
  stack.undo.push({ label: label, undo: undoFn, redo: redoFn })
  stack.redo = []
}

// Devuelve la entrada a deshacer (ya movida a la pila de rehacer) o null.
function takeUndo(stack) {
  var entry = stack.undo.pop()
  if (!entry) return null
  stack.redo.push(entry)
  return entry
}

function takeRedo(stack) {
  var entry = stack.redo.pop()
  if (!entry) return null
  stack.undo.push(entry)
  return entry
}

function canUndo(stack) { return stack.undo.length > 0 }
function canRedo(stack) { return stack.redo.length > 0 }

// Si deshacer/rehacer falla (p. ej. la tarea se borró desde MCP), la entrada
// ya no se puede aplicar: se descarta en vez de quedar ofreciéndose.
function dropRedo(stack, entry) {
  var i = stack.redo.lastIndexOf(entry)
  if (i !== -1) stack.redo.splice(i, 1)
}

function dropUndo(stack, entry) {
  var i = stack.undo.lastIndexOf(entry)
  if (i !== -1) stack.undo.splice(i, 1)
}
