import { test } from "node:test";
import assert from "node:assert/strict";
import { loadLib, plain } from "./load.mjs";

const Undo = loadLib("undo.js");

test("undo then redo returns the same entry", () => {
  const stack = Undo.createStack();
  Undo.push(stack, "rename", () => "u", () => "r");
  const undone = Undo.takeUndo(stack);
  assert.equal(undone.label, "rename");
  assert.ok(Undo.canRedo(stack));
  assert.equal(Undo.takeRedo(stack), undone);
  assert.ok(Undo.canUndo(stack));
});

test("a new write clears redo", () => {
  const stack = Undo.createStack();
  Undo.push(stack, "a", null, null);
  Undo.takeUndo(stack);
  Undo.push(stack, "b", null, null);
  assert.equal(Undo.takeRedo(stack), null);
});

test("empty stacks return null", () => {
  const stack = Undo.createStack();
  assert.equal(Undo.takeUndo(stack), null);
  assert.equal(Undo.takeRedo(stack), null);
});

test("a failed undo can be dropped instead of moving to redo", () => {
  const stack = Undo.createStack();
  Undo.push(stack, "a", null, null);
  const entry = Undo.takeUndo(stack);
  Undo.dropRedo(stack, entry);
  assert.equal(Undo.canRedo(stack), false);
  assert.equal(Undo.canUndo(stack), false);
});
