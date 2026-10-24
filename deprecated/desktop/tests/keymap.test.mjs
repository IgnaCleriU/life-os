import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { loadLib, plain } from "./load.mjs";

const Keymap = loadLib("keymap.js");
const tuiKeymap = JSON.parse(readFileSync(new URL("./tui-keymap.json", import.meta.url), "utf8"));

test("every TUI binding exists in the board registry, same scope and key", () => {
  const board = new Set(Keymap.ENTRIES.map((e) => `${e.scope} ${e.key}`));
  const missing = tuiKeymap.filter((e) => !board.has(`${e.scope} ${e.key}`));
  assert.deepEqual(missing, [], "bindings present in the TUI but not on the board");
});

test("no typed binding is a strict prefix of another in the same scope", () => {
  const collisions = Keymap.prefixCollisions(Keymap.ENTRIES).map(([a, b]) => `${a.key}/${b.key}`);
  assert.deepEqual(plain(collisions), []);
});

test("the old d/dd collision would be caught", () => {
  const entries = [...Keymap.ENTRIES, { scope: "collection", key: "d", label: "due", action: "x" }];
  assert.ok(Keymap.prefixCollisions(entries).some(([a, b]) => a.key === "d" && b.key === "dd"));
});

test("a key name is not a typed prefix: e does not collide with escape", () => {
  assert.equal(Keymap.isTypedSequence("escape"), false);
  assert.equal(Keymap.isTypedSequence("gg"), true);
});

test("detail scope sees task bindings plus globals", () => {
  const keys = Keymap.forScope(Keymap.ENTRIES, "detail").map((e) => e.key);
  assert.ok(keys.includes("space"));
  assert.ok(keys.includes("u"));
  assert.ok(!Keymap.forScope(Keymap.ENTRIES, "context").some((e) => e.key === "space"));
});

test("resolve prefers the focused scope's binding for a shared key", () => {
  assert.equal(Keymap.resolve(Keymap.ENTRIES, "context", "a").action, "createProject");
  assert.equal(Keymap.resolve(Keymap.ENTRIES, "collection", "a").action, "addTask");
});

test("every action id is unique per scope and key", () => {
  const seen = new Set();
  for (const e of Keymap.ENTRIES) {
    const id = `${e.scope} ${e.key}`;
    assert.ok(!seen.has(id), `duplicate binding ${id}`);
    seen.add(id);
  }
});

test("help rows group keys by action", () => {
  const rows = Keymap.groupedForHelp(Keymap.ENTRIES, "collection");
  const select = rows.find((r) => r.action === "toggleSelect");
  assert.deepEqual([...select.keys], ["x", "v"]);
  assert.equal(Keymap.displayKey("question_mark"), "?");
});
