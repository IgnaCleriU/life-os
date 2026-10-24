import { test } from "node:test";
import assert from "node:assert/strict";
import { loadLib, plain } from "./load.mjs";

const F = loadLib("format.js");
const today = new Date(2026, 8, 22); // martes 22/09/2026

const task = (over) => ({
  id: over.id ?? "t", project_id: "p1", title: "x", status: "todo", priority: "medium",
  due_date: null, created_at: "2026-09-01T00:00:00Z", ...over,
});

test("due labels", () => {
  assert.equal(F.dueLabel("2026-09-20", today), "overdue 2d");
  assert.equal(F.dueLabel("2026-09-22", today), "today");
  assert.equal(F.dueLabel("2026-09-23", today), "tomorrow");
  assert.equal(F.dueLabel("2026-09-25", today), "Fri 25");
  assert.equal(F.dueLabel("2026-10-04", today), "Oct 04");
  assert.equal(F.dueLabel(null, today), "");
});

test("due urgency ignores done tasks", () => {
  assert.equal(F.dueUrgency(task({ due_date: "2026-09-21" }), today), "overdue");
  assert.equal(F.dueUrgency(task({ due_date: "2026-09-23" }), today), "soon");
  assert.equal(F.dueUrgency(task({ due_date: "2026-09-21", status: "done" }), today), "");
});

test("glyphs and cycle match the TUI", () => {
  assert.equal(F.glyph("todo"), "·");
  assert.equal(F.glyph("doing"), "◐");
  assert.equal(F.glyph("done"), "✓");
  assert.deepEqual(["todo", "doing", "done"].map(F.nextStatus), ["doing", "done", "todo"]);
});

test("markdown line", () => {
  assert.equal(F.markdownLine(task({ title: "a" })), "- [ ] a");
  assert.equal(F.markdownLine(task({ title: "b", status: "done", due_date: "2026-09-25" })), "- [x] b (due 2026-09-25)");
});

test("visible tasks: project, status, text, sort", () => {
  const tasks = [
    task({ id: "1", title: "Comprar filtros", priority: "low", due_date: "2026-09-30", created_at: "1" }),
    task({ id: "2", title: "Llamar plomero", priority: "high", created_at: "2" }),
    task({ id: "3", title: "Hecha", status: "done", due_date: "2026-09-24", created_at: "3" }),
    task({ id: "4", project_id: "p2", title: "Otra", created_at: "4" }),
  ];
  const ids = (list) => plain(list.map((t) => t.id));
  assert.deepEqual(ids(F.visibleTasks(tasks, "p1", "all", "", "created")), ["1", "2", "3"]);
  assert.deepEqual(ids(F.visibleTasks(tasks, "p1", "open", "", "created")), ["1", "2"]);
  assert.deepEqual(ids(F.visibleTasks(tasks, "p1", "all", "LLAM", "created")), ["2"]);
  assert.deepEqual(ids(F.visibleTasks(tasks, "p1", "all", "", "due")), ["3", "1", "2"]);
  assert.deepEqual(ids(F.visibleTasks(tasks, "p1", "all", "", "priority")), ["2", "3", "1"]);
});

test("project filter and counts", () => {
  const projects = [
    { id: "p1", name: "Casa", status: "active" },
    { id: "p2", name: "Rust", status: "archived" },
  ];
  assert.deepEqual(plain(F.filterProjects(projects, "active", "").map((p) => p.id)), ["p1"]);
  assert.deepEqual(plain(F.filterProjects(projects, "all", "ru").map((p) => p.id)), ["p2"]);
  const counts = F.projectCounts([task({ id: "a" }), task({ id: "b", status: "done" })]);
  assert.deepEqual({ ...counts.p1 }, { open: 1, done: 1, total: 2 });
});

test("cursor keeps the id, else clamps the old index", () => {
  const list = [{ id: "a" }, { id: "b" }];
  assert.equal(F.cursorIndex(list, "b", 0), 1);
  assert.equal(F.cursorIndex(list, "gone", 5), 1);
  assert.equal(F.cursorIndex([], "gone", 5), -1);
});

test("cycles and fuzzy match", () => {
  assert.equal(F.nextInCycle(F.SORT_ORDERS, "priority"), "created");
  assert.ok(F.fuzzyMatch("cmp pr", "complete project"));
  assert.ok(!F.fuzzyMatch("zz", "complete project"));
});

test("external additions are summarized per project", () => {
  const before = [task({ id: "1" })];
  const after = [task({ id: "1" }), task({ id: "2" }), task({ id: "3" }), task({ id: "4", project_id: "p2" })];
  const added = F.addedTasks(before, after);
  assert.deepEqual(plain(added.map((t) => t.id)), ["2", "3", "4"]);
  const summary = F.summarizeAdded(added, { p1: { name: "Casa" }, p2: { name: "Finanzas" } });
  assert.equal(summary, "2 tasks added to Casa, 1 task added to Finanzas");
});
