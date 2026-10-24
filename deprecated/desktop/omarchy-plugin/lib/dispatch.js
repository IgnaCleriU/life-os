.pragma library
// Máquina de secuencias de teclas: misma semántica que KeySequenceBuffer de la
// TUI (backend/src/lifeos/adapters/tui/dispatch.py).
//
// - Un dígito suelto, sin nada pendiente, se consume en silencio (conteo
//   inicial, igual que en la TUI) y no llega al registro.
// - pendiente + tecla que coincide exacto con un atajo del scope -> matched.
// - pendiente + tecla que es prefijo estricto de otro atajo -> waiting.
// - si no -> no_match, y se descarta lo pendiente.

function createBuffer() {
  return { pending: "" }
}

function feed(buffer, registry, scope, key) {
  if (!buffer.pending && key.length === 1 && key >= "0" && key <= "9")
    return { kind: "waiting", entry: null }

  var candidate = buffer.pending + key
  var entry = registry.resolve(registry.ENTRIES, scope, candidate)
  if (entry) {
    buffer.pending = ""
    return { kind: "matched", entry: entry }
  }
  if (registry.isPrefix(registry.ENTRIES, scope, candidate)) {
    buffer.pending = candidate
    return { kind: "waiting", entry: null }
  }
  buffer.pending = ""
  return { kind: "no_match", entry: null }
}

function reset(buffer) {
  buffer.pending = ""
}
