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
      api.baseUrl = info.base_url || ("http://127.0.0.1:" + info.port)
      api.token = info.token || ""
      if (api.status !== "ok") api.status = "connecting"
    } catch (e) {
      api.markUnreachable()
    }
  }

  function markUnreachable() {
    api.baseUrl = ""
    api.token = ""
    api.status = "unreachable"
  }

  function rediscover() {
    api.discovery.reload()
  }

  function request(method, path, body, callback) {
    if (!api.baseUrl) {
      api.status = "unreachable"
      if (callback) callback({ ok: false, status: 0, data: null, error: { code: "daemon_unreachable", message: "lifeos-daemon is not running" } })
      return
    }
    var xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function() {
      if (xhr.readyState !== XMLHttpRequest.DONE) return
      var data = null
      if (xhr.responseText) {
        try { data = JSON.parse(xhr.responseText) } catch (e) { data = null }
      }
      var ok = xhr.status >= 200 && xhr.status < 300
      var error = null
      if (xhr.status === 0) {
        api.status = "unreachable"
        api.rediscover()
        error = { code: "daemon_unreachable", message: "lifeos-daemon is not running" }
      } else if (xhr.status === 401) {
        api.status = "unauthorized"
        api.rediscover()
        error = (data && data.error) || { code: "unauthorized", message: "invalid token" }
      } else {
        api.status = "ok"
        if (!ok) error = (data && data.error) || { code: "http_" + xhr.status, message: xhr.statusText }
      }
      if (callback) callback({ ok: ok, status: xhr.status, data: data, error: error })
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
