import { test } from "node:test";
import assert from "node:assert/strict";
import { loadLib, plain } from "./load.mjs";

const Keymap = loadLib("keymap.js");
const Dispatch = loadLib("dispatch.js");

function feedAll(scope, keys) {
  const buffer = Dispatch.createBuffer();
  return keys.map((k) => Dispatch.feed(buffer, Keymap, scope, k));
}

test("a single key matches immediately", () => {
  const [r] = feedAll("collection", ["space"]);
  assert.equal(r.kind, "matched");
  assert.equal(r.entry.action, "cycleStatus");
});

test("dd waits on the first d and matches on the second", () => {
  const [first, second] = feedAll("collection", ["d", "d"]);
  assert.equal(first.kind, "waiting");
  assert.equal(second.kind, "matched");
  assert.equal(second.entry.action, "deleteTask");
});

test("gg is global", () => {
  const [, r] = feedAll("context", ["g", "g"]);
  assert.equal(r.entry.action, "first");
});

test("an unknown continuation abandons the pending sequence", () => {
  const buffer = Dispatch.createBuffer();
  Dispatch.feed(buffer, Keymap, "collection", "d");
  assert.equal(Dispatch.feed(buffer, Keymap, "collection", "x").kind, "no_match");
  assert.equal(buffer.pending, "");
  assert.equal(Dispatch.feed(buffer, Keymap, "collection", "x").entry.action, "toggleSelect");
});

test("a leading digit is swallowed, like the TUI's count", () => {
  const [digit, j] = feedAll("collection", ["3", "j"]);
  assert.equal(digit.kind, "waiting");
  assert.equal(j.entry.action, "cursorDown");
});

test("unbound keys do not match", () => {
  assert.equal(feedAll("context", ["space"])[0].kind, "no_match");
});

test("an unbound letter that starts a key name does not swallow the next key", () => {
  // "s" no está en PROJECTS pero "slash"/"shift+tab" empiezan con "s".
  const [s, j] = feedAll("context", ["s", "j"]);
  assert.equal(s.kind, "no_match");
  assert.equal(j.entry.action, "cursorDown");
  const [t, k] = feedAll("collection", ["t", "k"]);
  assert.equal(t.kind, "no_match");
  assert.equal(k.entry.action, "cursorUp");
});
