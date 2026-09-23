import QtQuick
import Quickshell
import Quickshell.Io

// Cliente del daemon REST (`lifeos-daemon`, ADR 0009).
//
// Descubre URL y token en `$XDG_RUNTIME_DIR/life-os/daemon.json`, que el
// daemon reescribe con un token nuevo en cada arranque. Lo vigila y además
// lo relee ante un 401 o un error de conexión, así un reinicio del daemon se
// recupera solo.
//
// `request(method, path, body, callback)` llama a
// `callback({ ok, status, data, error })`, donde `error` tiene la forma
// `{ code, message }` de las respuestas de error de la API.
QtObject {
  id: api

  property string discoveryPath: (Quickshell.env("XDG_RUNTIME_DIR") || "/tmp") + "/life-os/daemon.json"
  property string baseUrl: ""
  property string token: ""
  // "connecting" | "ok" | "unreachable" | "unauthorized"
  property string status: "connecting"
  readonly property bool online: status === "ok"

  function applyDiscovery(raw) {
    try {
      var info = JSON.parse(raw)
      var nextUrl = info.base_url || ("http://127.0.0.1:" + info.port)
      var nextToken = info.token || ""
      // Releer el mismo archivo (cada error lo relee) no es una novedad: solo
      // un daemon nuevo (otra URL u otro token) vuelve a "connecting". Si
      // no, un daemon colgado haría oscilar el estado en vez de verse caído.
      var changed = nextUrl !== api.baseUrl || nextToken !== api.token
      api.baseUrl = nextUrl
      api.token = nextToken
      if (changed && api.status !== "ok") api.status = "connecting"
    } catch (e) {
      api.markUnreachable()
    }
  }

  function markUnreachable() {
    api.baseUrl = ""
    api.token = ""
    api.status = "unreachable"
  }

  // Tope por pedido. El daemon es local: una respuesta sana tarda
  // milisegundos, así que pasado este tiempo se lo da por colgado.
  property int requestTimeoutMs: 5000
  property var pending: []

  property Timer watchdog: Timer {
    interval: 500
    repeat: true
    running: api.pending.length > 0
    onTriggered: {
      var now = Date.now()
      var overdue = api.pending.filter(function(e) { return now > e.deadline })
      for (var i = 0; i < overdue.length; i++) {
        overdue[i].finish(0, null, "lifeos-daemon did not answer in " + api.requestTimeoutMs / 1000 + " s")
        try { overdue[i].xhr.abort() } catch (e) {}
      }
    }
  }

  function rediscover() {
    api.discovery.reload()
  }

  function request(method, path, body, callback) {
    if (!api.baseUrl) {
      // Sin daemon.json todavía (p. ej. el shell arrancó antes que el
      // daemon): no se depende solo del watcher, que puede no dispararse
      // por un archivo que no existía; se relee en cada intento, y el
      // sondeo del tablero ya espacia los intentos (3 s).
      api.status = "unreachable"
      api.rediscover()
      if (callback) callback({ ok: false, status: 0, data: null, error: { code: "daemon_unreachable", message: "lifeos-daemon is not running" } })
      return
    }
    var xhr = new XMLHttpRequest()
    // Cada pedido termina exactamente una vez: por respuesta, o por el
    // watchdog si el daemon aceptó la conexión pero no contesta (proceso
    // colgado, base bloqueada). Sin esto el callback no llegaría nunca y el
    // tablero dejaría de sondear (queda `refreshing`). No se usa
    // `xhr.timeout` porque no todas las versiones de Qt lo implementan en QML.
    var entry = { done: false, deadline: Date.now() + api.requestTimeoutMs, finish: null, xhr: xhr }
    entry.finish = function(status, data, statusText) {
      if (entry.done) return
      entry.done = true
      api.pending = api.pending.filter(function(e) { return e !== entry })
      var ok = status >= 200 && status < 300
      var error = null
      if (status === 0) {
        api.status = "unreachable"
        api.rediscover()
        error = { code: "daemon_unreachable", message: statusText || "lifeos-daemon is not running" }
      } else if (status === 401) {
        api.status = "unauthorized"
        api.rediscover()
        error = (data && data.error) || { code: "unauthorized", message: "invalid token" }
      } else {
        api.status = "ok"
        if (!ok) error = (data && data.error) || { code: "http_" + status, message: statusText }
      }
      if (callback) callback({ ok: ok, status: status, data: data, error: error })
    }
    api.pending = api.pending.concat([entry])
    xhr.onreadystatechange = function() {
      if (xhr.readyState !== XMLHttpRequest.DONE) return
      var data = null
      if (xhr.responseText) {
        try { data = JSON.parse(xhr.responseText) } catch (e) { data = null }
      }
      entry.finish(xhr.status, data, xhr.statusText)
    }
    xhr.open(method, api.baseUrl + path)
    xhr.setRequestHeader("Authorization", "Bearer " + api.token)
    if (body !== undefined && body !== null) {
      xhr.setRequestHeader("Content-Type", "application/json")
      xhr.send(JSON.stringify(body))
    } else {
      xhr.send()
    }
  }

  property FileView discovery: FileView {
    path: api.discoveryPath
    watchChanges: true
    printErrors: false
    onFileChanged: reload()
    onLoaded: api.applyDiscovery(text())
    onLoadFailed: api.markUnreachable()
  }
}
