"""Prueba headless del tablero de Quickshell contra un `lifeos-daemon` real.

Levanta el daemon con una base SQLite descartable (nunca la del usuario),
siembra datos de ejemplo por REST, monta `BoardView.qml` en un QQuickView
offscreen con stubs mínimos de Quickshell y de `qs.Commons` (Omarchy), y lo
maneja con el teclado y el mouse. Deja capturas en `--out`.

No hace falta Wayland ni Omarchy. Sí hace falta PySide6 y las bibliotecas
de EGL/GL del sistema:

    uv run --with PySide6-Essentials python desktop/tests/qml/run_board.py

(desde `backend/`, para que `lifeos-daemon` esté en el venv).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parents[1] / "omarchy-plugin"
PORT = 8791

TOKYO_NIGHT = """accent = "#7aa2f7"
background = "#1a1b26"
foreground = "#a9b1d6"
red = "#f7768e"
yellow = "#e0af68"
green = "#9ece6a"
cyan = "#449dab"
bright_cyan = "#0db9d7"
magenta = "#ad8ee6"
bright_magenta = "#bb9af7"
"""


# --- stubs -------------------------------------------------------------------


def write_stubs(root: Path, env: dict[str, str], theme_dir: Path) -> None:
    """Módulos QML mínimos que imitan lo que el plugin usa de Quickshell y
    de Omarchy. Se generan por corrida para hornear `env()`."""
    qs = root / "Quickshell"
    (qs / "Io").mkdir(parents=True)
    (qs / "qmldir").write_text("module Quickshell\nsingleton Quickshell 1.0 Quickshell.qml\n")
    (qs / "Quickshell.qml").write_text(
        "pragma Singleton\nimport QtQuick\nQtObject {\n"
        f"  readonly property var envValues: {json.dumps(env)}\n"
        "  function env(name) { return envValues[name] || \"\" }\n"
        "  function execDetached(argv) { console.log(\"EXEC\", JSON.stringify(argv)) }\n"
        "}\n"
    )
    (qs / "Io" / "qmldir").write_text("module Quickshell.Io\nFileView 1.0 FileView.qml\n")
    (qs / "Io" / "FileView.qml").write_text(
        """import QtQuick
// Stub de Quickshell.Io.FileView: lee con XMLHttpRequest (file://) y
// simula watchChanges sondeando el contenido.
QtObject {
  id: fv
  property string path: ""
  property bool watchChanges: false
  property bool printErrors: true
  property string _text: ""
  property bool _ok: false
  signal loaded()
  signal loadFailed()
  signal fileChanged()
  function text() { return _text }
  function _read() {
    var x = new XMLHttpRequest()
    x.open("GET", "file://" + path, false)
    try { x.send() } catch (e) { return null }
    return (x.status === 200 || x.status === 0) && x.responseText !== "" ? x.responseText : null
  }
  function reload() {
    var t = _read()
    if (t === null) { _ok = false; _text = ""; loadFailed() }
    else { _ok = true; _text = t; loaded() }
  }
  onPathChanged: reload()
  property Timer _watch: Timer {
    interval: 300; repeat: true; running: fv.watchChanges
    onTriggered: { var t = fv._read(); if ((t === null) !== !fv._ok || (t !== null && t !== fv._text)) fv.fileChanged() }
  }
}
"""
    )
    commons = root / "qs" / "Commons"
    commons.mkdir(parents=True)
    (commons / "qmldir").write_text(
        "module qs.Commons\nsingleton Color 1.0 Color.qml\nsingleton Style 1.0 Style.qml\n"
    )
    (commons / "Color.qml").write_text(
        "pragma Singleton\nimport QtQuick\nQtObject {\n"
        f'  readonly property string currentThemePath: "{theme_dir}"\n'
        '  property color background: "#1a1b26"\n'
        '  property color foreground: "#a9b1d6"\n'
        '  property color accent: "#7aa2f7"\n'
        '  property color urgent: "#f7768e"\n'
        '  property color muted: "#414868"\n'
        "  readonly property QtObject menu: QtObject {\n"
        '    property color background: Qt.rgba(0.102, 0.106, 0.149, 0.94)\n'
        '    property color border: "#a9b1d6"\n'
        '    property color scrim: Qt.rgba(0.102, 0.106, 0.149, 0.5)\n'
        '    property color selectedBackground: Qt.rgba(0.66, 0.69, 0.84, 0.08)\n'
        '    property color selectedText: "#7aa2f7"\n'
        "  }\n}\n"
    )
    (commons / "Style.qml").write_text(
        "pragma Singleton\nimport QtQuick\nQtObject {\n"
        "  property int cornerRadius: 0\n  property int gapsOut: 5\n"
        "  readonly property QtObject font: QtObject {\n"
        '    readonly property string menuFamily: "DejaVu Sans Mono"\n'
        "    readonly property int caption: 10\n    readonly property int bodySmall: 11\n"
        "    readonly property int body: 12\n    readonly property int title: 14\n"
        "  }\n"
        "  readonly property QtObject spacing: QtObject {\n"
        "    readonly property int lg: 8\n    readonly property int panelPadding: 18\n"
        "  }\n}\n"
    )


# --- daemon y datos ----------------------------------------------------------


class Daemon:
    def __init__(self, workdir: Path) -> None:
        self.runtime = workdir / "run"
        self.env = {
            **os.environ,
            "DATABASE_URL": f"sqlite:///{workdir / 'board.db'}",
            "XDG_RUNTIME_DIR": str(self.runtime),
            "APP_PORT": str(PORT),
        }
        self.proc: subprocess.Popen | None = None

    def start(self) -> None:
        self.runtime.mkdir(parents=True, exist_ok=True)
        exe = shutil.which("lifeos-daemon") or str(Path(sys.prefix) / "bin" / "lifeos-daemon")
        self.proc = subprocess.Popen([exe], env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(100):
            if (self.runtime / "life-os" / "daemon.json").exists():
                try:
                    self.get("/health")
                    return
                except OSError:
                    pass
            time.sleep(0.1)
        raise RuntimeError("lifeos-daemon did not start")

    def stop(self) -> None:
        if self.proc:
            self.proc.terminate()
            self.proc.wait(10)
            self.proc = None

    @property
    def token(self) -> str:
        return json.loads((self.runtime / "life-os" / "daemon.json").read_text())["token"]

    def _req(self, method: str, path: str, body=None):
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(f"http://127.0.0.1:{PORT}{path}", data=data, method=method)
        req.add_header("Authorization", f"Bearer {self.token}")
        if data:
            req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else None

    def get(self, path):
        return self._req("GET", path)

    def post(self, path, body=None):
        return self._req("POST", path, body)

    def patch(self, path, body):
        return self._req("PATCH", path, body)


def seed(d: Daemon) -> None:
    today = date.today()

    def day(n):
        return (today + timedelta(days=n)).isoformat()

    ids = {}
    for name in ["Life OS", "Casa", "Finanzas", "Viaje a Bariloche", "Mudanza", "Curso de Rust"]:
        ids[name] = d.post("/projects", {"name": name})["id"]
    d.post(f"/projects/{ids['Mudanza']}/complete")
    d.post(f"/projects/{ids['Curso de Rust']}/archive")

    def task(project, title, status="todo", priority="medium", due=None, desc=None):
        t = d.post(f"/projects/{ids[project]}/tasks", {"title": title, "priority": priority, "due_date": due, "description": desc})
        if status == "doing":
            d.post(f"/tasks/{t['id']}/start")
        elif status == "done":
            d.post(f"/tasks/{t['id']}/complete")

    task("Life OS", "Cerrar MVP: cargar el roadmap por MCP", "doing", "high", day(2),
         "Step 8 del roadmap: crear el proyecto y las fases como tareas desde Claude, y verificar por REST.")
    task("Life OS", "Probar el tablero en Omarchy", priority="high", due=day(1))
    task("Life OS", "Actualizar la línea de estado en CLAUDE.md", priority="low", due=day(-1))
    task("Life OS", "Parser quick-add compartido", "done", "high")
    task("Casa", "Comprar filtros de aire", priority="high", due=day(4))
    task("Casa", "Llamar al plomero por la pérdida del baño", due=day(-3), desc="Gotea debajo de la bacha.")
    task("Casa", "Limpiar canaletas", priority="low")
    task("Casa", "Cambiar lamparitas del pasillo", "done", "low")
    task("Finanzas", "Pagar monotributo", priority="high", due=day(3))
    task("Finanzas", "Conciliar gastos de agosto", "doing")
    task("Viaje a Bariloche", "Comprar pasajes", priority="high", due=day(7))
    task("Mudanza", "Contratar flete", "done")


# --- escenario ---------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(tempfile.gettempdir()) / "lifeos-board-shots")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    workdir = Path(tempfile.mkdtemp(prefix="lifeos-board-"))
    theme_dir = workdir / "theme"
    theme_dir.mkdir()
    (theme_dir / "colors.toml").write_text(TOKYO_NIGHT)
    daemon = Daemon(workdir)
    daemon.start()
    seed(daemon)

    stubs = workdir / "stubs"
    write_stubs(stubs, {"XDG_RUNTIME_DIR": str(daemon.runtime)}, theme_dir)
    harness_dir = workdir / "harness"
    shutil.copytree(PLUGIN, harness_dir)
    shutil.copy(HERE / "Harness.qml", harness_dir / "Harness.qml")

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ["QML_XHR_ALLOW_FILE_READ"] = "1"
    from PySide6.QtCore import QEventLoop, QPoint, QPointF, Qt, QTimer, QUrl
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQuick import QQuickView
    from PySide6.QtTest import QTest

    _app = QGuiApplication(sys.argv)  # vive mientras dure la prueba
    view = QQuickView()
    view.engine().addImportPath(str(stubs))
    errors: list[str] = []
    view.engine().warnings.connect(lambda ws: errors.extend(w.toString() for w in ws))
    view.setSource(QUrl.fromLocalFile(str(harness_dir / "Harness.qml")))
    if view.status() != QQuickView.Ready:
        for e in view.errors():
            print("QML ERROR:", e.toString())
        daemon.stop()
        return 1
    view.show()
    from PySide6.QtCore import QObject

    board = view.rootObject().findChild(QObject, "board")

    def pump(ms: int) -> None:
        loop = QEventLoop()
        QTimer.singleShot(ms, loop.quit)
        loop.exec()

    def wait_for(predicate, timeout=6000, what="condition") -> None:
        end = time.time() + timeout / 1000
        while time.time() < end:
            if predicate():
                return
            pump(50)
        raise AssertionError(f"timed out waiting for {what}")

    from PySide6.QtQml import QJSValue

    def prop(name):
        value = board.property(name)
        return value.toVariant() if isinstance(value, QJSValue) else value

    def tasks():
        return [dict(t) for t in (prop("tasks") or [])]

    from PySide6.QtCore import QEvent
    from PySide6.QtGui import QKeyEvent

    def send(key, text="", modifiers=Qt.NoModifier):
        for kind in (QEvent.KeyPress, QEvent.KeyRelease):
            QGuiApplication.sendEvent(view, QKeyEvent(kind, key, modifiers, text))
        pump(40)

    def char(ch, modifiers=None):
        if modifiers is None:
            modifiers = Qt.ShiftModifier if ch.isupper() or ch in "?@!#" else Qt.NoModifier
        send(ord(ch.upper()), ch, modifiers)

    def keys(*seq):
        """Teclas sueltas: un carácter, un nombre de Qt.Key_ ("Return",
        "Escape"...) o una tupla (carácter, modificadores)."""
        for k in seq:
            if isinstance(k, tuple):
                ch, mods = k
                if mods & Qt.ControlModifier:
                    send(ord(ch.upper()), "", mods)
                else:
                    char(ch, mods)
            elif k == "space":
                send(Qt.Key_Space, " ")
            elif k == "slash":
                send(Qt.Key_Slash, "/")
            elif len(k) == 1:
                char(k)
            else:
                send(getattr(Qt, "Key_" + k))
            pump(60)

    def typed(text):
        for ch in text:
            char(ch)
        pump(60)

    def shot(name):
        pump(250)
        view.grabWindow().save(str(args.out / f"{name}.png"))
        print("shot", name)

    checks: list[str] = []

    def check(cond, label):
        checks.append(("ok  " if cond else "FAIL") + " " + label)
        print(checks[-1])

    try:
        wait_for(lambda: prop("loaded"), what="initial load")
        pump(300)
        check(prop("currentProjectId") != "", "a project is selected on load")
        check(len(prop("visibleProjects")) == 4, "active filter hides completed/archived projects")
        shot("01-board")

        # j baja al segundo proyecto (Casa); l enfoca TASKS.
        keys("j", "l")
        check(prop("focusPane") == "tasks", "l focuses the tasks pane")

        # Quick-add con preview en vivo.
        keys("a")
        check(prop("activeModal") == "prompt" and prop("mode") == "INSERT", "a opens quick-add in INSERT mode")
        typed("llamar al gasista !high @fri #fin")
        pump(500)
        shot("02-quick-add-preview")
        typed("anzas")
        keys("Return")
        wait_for(lambda: any(t["title"] == "llamar al gasista" for t in tasks()), what="quick-add task")
        created = next(t for t in tasks() if t["title"] == "llamar al gasista")
        check(created["priority"] == "high" and created["due_date"] is not None, "quick-add parsed priority and due date")
        pump(300)
        check(prop("currentTaskId") == created["id"], "cursor lands on the new task")

        # Ambiguo / desconocido: el prompt se queda abierto con el error.
        keys("a")
        typed("algo #nada")
        keys("Return")
        pump(400)
        check(prop("activeModal") == "prompt", "an unknown #project keeps the prompt open")
        shot("03-quick-add-error")
        keys("Escape")

        # Space cicla el estado; u deshace.
        before = next(t for t in tasks() if t["id"] == prop("currentTaskId"))["status"]
        keys("space")
        wait_for(lambda: next(t for t in tasks() if t["id"] == created["id"])["status"] != before, what="status cycle")
        keys("u")
        wait_for(lambda: next(t for t in tasks() if t["id"] == created["id"])["status"] == before, what="undo status")
        check(True, "space cycles status and u undoes it")

        # dd + confirmación, y deshacer.
        keys("d", "d")
        check(prop("activeModal") == "confirm", "dd asks for confirmation")
        shot("04-confirm-delete")
        keys("y")
        wait_for(lambda: all(t["id"] != created["id"] for t in tasks()), what="delete")
        keys("u")
        wait_for(lambda: any(t["id"] == created["id"] for t in tasks()), what="undo delete")
        check(True, "dd deletes and u restores")

        # Selección en lote + prioridad.
        keys("g", "g", "x", "j", "x")
        check(prop("selectedCount") == 2 and prop("mode") == "SELECT", "x selects in bulk (SELECT mode)")
        keys("p")
        keys("1")
        wait_for(lambda: prop("selectedCount") == 0, what="bulk priority")
        pump(400)
        shot("05-after-bulk-priority")

        # Filtro /.
        keys("slash")
        typed("gasi")
        check(prop("mode") == "FILTER" and len(prop("visibleTasks")) == 1, "/ filters tasks live")
        keys("Return")
        keys("Escape")
        check(prop("taskText") == "", "Esc clears the filter")

        # Detalle y descripción inline.
        keys("g", "g")
        keys("Return")
        check(prop("focusPane") == "detail", "Enter opens the detail pane")
        keys(("E", Qt.ShiftModifier))
        check(prop("mode") == "INSERT", "E edits the description inline")
        typed(" Preguntar por la garantía.")
        keys("Escape")
        cur = prop("currentTaskId")
        wait_for(lambda: "garantía" in (next(t for t in tasks() if t["id"] == cur)["description"] or ""), what="description save")
        check(True, "the description is saved on Esc")
        shot("06-detail")

        # Paleta y ayuda.
        keys(("K", Qt.ControlModifier))
        check(prop("mode") == "PALETTE", "^k opens the palette")
        typed("sort")
        shot("07-palette")
        keys("Return")
        check(prop("sortOrder") == "due", "the palette runs the chosen command")
        keys(("?", Qt.ShiftModifier))
        check(prop("activeModal") == "help", "? opens the keybindings overlay")
        shot("08-help")
        keys("Escape")

        # Cambio externo (el agente vía MCP escribe directo en la base; acá,
        # por REST, que para el tablero es igual: sube la revisión).
        casa = next(p for p in daemon.get("/projects") if p["name"] == "Casa")
        daemon.post("/quick-add", {"text": "Pedir presupuesto de pintura @sat", "default_project_id": casa["id"]})
        wait_for(lambda: any(t["title"] == "Pedir presupuesto de pintura" for t in tasks()), what="external task")
        check(True, "an external write shows up without reloading")
        shot("09-external-change")

        # Una letra sin atajo que empieza un nombre de tecla ("s" de "slash")
        # no debe tragarse la tecla siguiente.
        keys("h", "h", "g", "g")
        before_index = prop("projectIndex")
        keys("s", "j")
        check(prop("projectIndex") == before_index + 1, "an unbound s does not swallow the next key")
        keys("k", "l")

        # Deshacer algo que ya no se puede aplicar: el error queda a la vista.
        victim = prop("currentTaskId")
        keys("e")
        typed(" (editada)")
        keys("Return")
        wait_for(lambda: next(t for t in tasks() if t["id"] == victim)["title"].endswith("(editada)"), what="rename")
        daemon._req("DELETE", f"/tasks/{victim}")
        pump(1500)
        keys("u")
        wait_for(lambda: "task_not_found" in (prop("errorText") or ""), what="undo error")
        check(not (prop("lastAction") or "").startswith("undo"), "a failed undo keeps its error instead of reporting success")
        daemon.post(f"/tasks/{victim}/restore")
        pump(1500)

        # Arrastrar la tarea del cursor sobre otro proyecto.
        keys("h")
        projects_list = [dict(p) for p in prop("visibleProjects")]
        keys("l")
        moving = prop("currentTaskId")
        origin = next(t for t in tasks() if t["id"] == moving)["project_id"]
        target_index, target = next((i, p) for i, p in enumerate(projects_list) if p["id"] != origin)
        vis = [dict(t) for t in prop("visibleTasks")]
        row = next(i for i, t in enumerate(vis) if t["id"] == moving)
        # Geometría: se leen las posiciones de los ListView del tablero.
        from PySide6.QtQuick import QQuickItem

        lists = [o for o in board.findChildren(QQuickItem) if o.metaObject().className().startswith("QQuickListView")]
        plist, tlist = lists[0], lists[1]

        def center(item: QQuickItem, index: int) -> QPoint:
            h = item.property("contentItem").childItems()[0].height()
            pt = item.mapToScene(QPointF(item.width() / 2, index * (h + 1) + h / 2 - item.property("contentY")))
            return QPoint(int(pt.x()), int(pt.y()))

        src = center(tlist, row)
        dst = center(plist, target_index)
        QTest.mousePress(view, Qt.LeftButton, Qt.NoModifier, src)
        for step in range(1, 21):
            QTest.mouseMove(view, QPoint(src.x() + (dst.x() - src.x()) * step // 20, src.y() + (dst.y() - src.y()) * step // 20))
            pump(20)
        shot("10-dragging")
        QTest.mouseRelease(view, Qt.LeftButton, Qt.NoModifier, dst)
        wait_for(lambda: next(t for t in tasks() if t["id"] == moving)["project_id"] == target["id"], what="drag to move")
        check(True, "dragging a task onto a project moves it")

        # Daemon caído: el tablero lo dice y se recupera solo.
        daemon.stop()
        wait_for(lambda: board.property("api").property("status") == "unreachable", timeout=8000, what="unreachable")
        shot("11-daemon-down")
        check(True, "the status bar reports an unreachable daemon")
        # Un "daemon" que acepta conexiones pero nunca responde: el watchdog
        # de Api.qml tiene que cortar los pedidos, o el sondeo quedaría
        # trabado para siempre.
        import socket as _socket

        hung = _socket.socket()
        hung.bind(("127.0.0.1", 0))
        hung.listen(16)
        hung_port = hung.getsockname()[1]
        info = daemon.runtime / "life-os"
        info.mkdir(parents=True, exist_ok=True)
        (info / "daemon.json").write_text(
            json.dumps({"base_url": f"http://127.0.0.1:{hung_port}", "port": hung_port, "token": "x"})
        )
        board.property("api").setProperty("requestTimeoutMs", 1500)
        wait_for(lambda: board.property("api").property("baseUrl").endswith(str(hung_port)), timeout=8000, what="hung daemon discovered")
        pump(1500)
        wait_for(lambda: board.property("api").property("status") == "unreachable" and not board.property("refreshing"), timeout=10000, what="watchdog")
        check(True, "a daemon that never answers is reported instead of stalling the board")
        (info / "daemon.json").unlink()
        hung.close()

        daemon.start()
        wait_for(lambda: board.property("api").property("status") == "ok", timeout=10000, what="reconnect")
        check(True, "the board reconnects after the daemon restarts (new token)")
    finally:
        daemon.stop()

    bad = [e for e in errors if "stubs" not in e]
    for e in bad:
        print("QML WARNING:", e)
    failed = [c for c in checks if c.startswith("FAIL")]
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed; screenshots in {args.out}")
    return 1 if failed or bad else 0


if __name__ == "__main__":
    sys.exit(main())
