from __future__ import annotations

from lifeos.adapters.tui.keymap import Scope
from lifeos.adapters.tui.modules.stub import StubModule
from lifeos.adapters.tui.undo import UndoStack


def test_context_pane_has_several_buckets_with_counts() -> None:
    module = StubModule()
    contents = module.context_pane()
    assert len(contents.items) >= 3
    labels = [item.label for item in contents.items]
    assert len(set(labels)) == len(labels)  # no duplicate bucket names


def test_collection_pane_lists_items_under_the_given_bucket() -> None:
    module = StubModule()
    first_bucket = module.context_pane().items[0]
    collection = module.collection_pane(first_bucket)
    assert len(collection.items) >= 1


def test_collection_pane_is_empty_for_none_context_item() -> None:
    module = StubModule()
    assert module.collection_pane(None).items == []


def test_detail_pane_renders_fields_for_a_collection_item() -> None:
    module = StubModule()
    bucket = module.context_pane().items[0]
    item = module.collection_pane(bucket).items[0]
    detail = module.detail_pane(item)
    assert detail is not None
    assert detail.title == item.label
    assert len(detail.fields) >= 1


def test_detail_pane_is_none_for_no_selection() -> None:
    module = StubModule()
    assert module.detail_pane(None) is None


def test_keymap_entries_are_plain_and_scope_appropriate() -> None:
    module = StubModule()
    entries = module.keymap_entries()
    assert entries  # at least one binding to exercise INSERT and undo
    for entry in entries:
        assert entry.scope in (Scope.CONTEXT, Scope.COLLECTION, Scope.DETAIL)


def test_module_stays_free_of_application_domain_infrastructure_imports() -> None:
    import lifeos.adapters.tui.modules.stub as stub_module

    source = open(stub_module.__file__).read()
    for forbidden in ("application", "domain", "infrastructure"):
        assert f"lifeos.{forbidden}" not in source
        assert f"from lifeos import {forbidden}" not in source


# --- exercising INSERT mode and undo end-to-end, via the shell contract ------


class _FakeShell:
    """Just enough of ShellScreen's public surface for the stub's own
    actions to call, without mounting a real Textual App - the real wiring
    through actual keypresses is covered in test_app_wiring.py."""

    def __init__(self) -> None:
        self.undo_stack = UndoStack()
        self.reload_count = 0
        self.last_context_select_id: str | None = None
        self.last_collection_select_id: str | None = None
        self._pending_commit: object = None

    def prompt_insert(self, *, placeholder: str, on_commit) -> None:  # noqa: ANN001
        self._pending_commit = on_commit

    def action_reload(
        self,
        *,
        context_select_id: str | None = None,
        collection_select_id: str | None = None,
    ) -> None:
        self.reload_count += 1
        self.last_context_select_id = context_select_id
        self.last_collection_select_id = collection_select_id

    def commit_pending_prompt(self, text: str) -> None:
        assert self._pending_commit is not None
        self._pending_commit(text)
        self._pending_commit = None


def _entry(module: StubModule, scope: Scope, key: str):  # noqa: ANN201
    matches = [e for e in module.keymap_entries() if e.scope is scope and e.key == key]
    assert len(matches) == 1, f"expected exactly one {scope}/{key!r} entry"
    return matches[0]


def test_add_bucket_action_opens_an_insert_prompt_and_commits_a_new_bucket() -> None:
    module = StubModule()
    module.shell = _FakeShell()
    before = len(module.context_pane().items)

    _entry(module, Scope.CONTEXT, "a").action()
    module.shell.commit_pending_prompt("a whole new bucket")

    after = module.context_pane().items
    assert len(after) == before + 1
    assert after[-1].label == "a whole new bucket"
    assert module.shell.reload_count == 1


def test_add_bucket_action_selects_the_new_bucket() -> None:
    module = StubModule()
    module.shell = _FakeShell()

    _entry(module, Scope.CONTEXT, "a").action()
    module.shell.commit_pending_prompt("a whole new bucket")

    new_bucket = module.context_pane().items[-1]
    assert module.shell.last_context_select_id == new_bucket.id


def test_add_item_action_adds_to_the_currently_selected_bucket() -> None:
    module = StubModule()
    module.shell = _FakeShell()
    bucket = module.context_pane().items[0]
    module.shell.current_context_item = bucket  # type: ignore[attr-defined]
    before = len(module.collection_pane(bucket).items)

    _entry(module, Scope.COLLECTION, "a").action()
    module.shell.commit_pending_prompt("a whole new item")

    after = module.collection_pane(bucket).items
    assert len(after) == before + 1
    assert after[-1].label == "a whole new item"


def test_add_item_action_selects_the_new_item() -> None:
    module = StubModule()
    module.shell = _FakeShell()
    bucket = module.context_pane().items[0]
    module.shell.current_context_item = bucket  # type: ignore[attr-defined]

    _entry(module, Scope.COLLECTION, "a").action()
    module.shell.commit_pending_prompt("a whole new item")

    new_item = module.collection_pane(bucket).items[-1]
    assert module.shell.last_collection_select_id == new_item.id


def test_toggle_flag_action_pushes_an_undoable_write() -> None:
    module = StubModule()
    module.shell = _FakeShell()
    bucket = module.context_pane().items[0]
    module.shell.current_context_item = bucket  # type: ignore[attr-defined]
    item = module.collection_pane(bucket).items[0]
    module.shell.current_collection_item = item  # type: ignore[attr-defined]

    assert module.detail_pane(item).fields[-1] == ("flagged", "no")

    _entry(module, Scope.COLLECTION, "t").action()
    assert module.detail_pane(item).fields[-1] == ("flagged", "yes")
    assert module.shell.reload_count == 1

    write = module.shell.undo_stack.undo()
    assert write is not None
    assert module.detail_pane(item).fields[-1] == ("flagged", "no")

    module.shell.undo_stack.redo()
    assert module.detail_pane(item).fields[-1] == ("flagged", "yes")
