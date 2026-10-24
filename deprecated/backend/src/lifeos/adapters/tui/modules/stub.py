from __future__ import annotations

from lifeos.adapters.tui.keymap import KeymapEntry, Scope
from lifeos.adapters.tui.module import DetailContents, PaneContents, PaneItem
from lifeos.adapters.tui.undo import UndoableWrite


class StubModule:
    """Throwaway module proving the shell/module boundary from ADR 0008 is
    real rather than aspirational (Step 12) - built before any Projects/
    Tasks code exists, and free of it. Several plain-text items per pane
    (enough to exercise navigation, filter, palette, and selection for
    real), one INSERT-mode action per pane level, and one write+undo
    action - deliberately no glyphs, colors, or status semantics, since
    those are Projects/Tasks-flavored and belong to Step 13.
    """

    def __init__(self) -> None:
        self.shell: object | None = None
        self._buckets: dict[str, dict[str, object]] = {
            "b1": {"label": "bucket one", "items": ["first item", "second item"]},
            "b2": {"label": "bucket two", "items": ["third item"]},
            "b3": {"label": "bucket three", "items": []},
        }
        self._next_bucket_number = 4
        self._flagged: set[str] = set()

    # --- TuiModule contract ---------------------------------------------------

    def context_pane(self) -> PaneContents:
        items = [
            PaneItem(
                id=bucket_id,
                label=str(bucket["label"]),
                payload=bucket_id,
                meta=str(len(bucket["items"])),  # type: ignore[arg-type]
            )
            for bucket_id, bucket in self._buckets.items()
        ]
        return PaneContents(title="BUCKETS", items=items)

    def collection_pane(self, context_item: PaneItem | None) -> PaneContents:
        if context_item is None:
            return PaneContents(title="ITEMS", items=[])
        bucket = self._buckets.get(str(context_item.payload))
        if bucket is None:
            return PaneContents(title="ITEMS", items=[])
        items = []
        for index, label in enumerate(bucket["items"]):  # type: ignore[arg-type]
            item_id = f"{context_item.payload}:{index}"
            meta = "flagged" if item_id in self._flagged else ""
            item = PaneItem(id=item_id, label=str(label), payload=label, meta=meta)
            items.append(item)
        return PaneContents(title=f"ITEMS - {bucket['label']}", items=items)

    def detail_pane(self, collection_item: PaneItem | None) -> DetailContents | None:
        if collection_item is None:
            return None
        flagged = "yes" if collection_item.id in self._flagged else "no"
        return DetailContents(
            title=collection_item.label,
            fields=[("id", collection_item.id), ("flagged", flagged)],
        )

    def keymap_entries(self) -> list[KeymapEntry]:
        return [
            KeymapEntry(Scope.CONTEXT, "a", "add a bucket", self._start_add_bucket),
            KeymapEntry(Scope.COLLECTION, "a", "add an item", self._start_add_item),
            KeymapEntry(Scope.COLLECTION, "t", "toggle flagged", self._toggle_flagged),
        ]

    # --- add a bucket (exercises INSERT mode) ---------------------------------

    def _start_add_bucket(self) -> None:
        shell = self.shell
        assert shell is not None
        shell.prompt_insert(  # type: ignore[attr-defined]
            placeholder="new bucket name", on_commit=self._commit_add_bucket
        )

    def _commit_add_bucket(self, name: str) -> None:
        if not name:
            return
        bucket_id = f"b{self._next_bucket_number}"
        self._next_bucket_number += 1
        self._buckets[bucket_id] = {"label": name, "items": []}
        self.shell.action_reload()  # type: ignore[attr-defined]

    # --- add an item to the selected bucket (exercises INSERT mode) ----------

    def _start_add_item(self) -> None:
        shell = self.shell
        assert shell is not None
        context_item = shell.current_context_item  # type: ignore[attr-defined]
        if context_item is None:
            return
        bucket_id = str(context_item.payload)
        shell.prompt_insert(  # type: ignore[attr-defined]
            placeholder="new item title",
            on_commit=lambda text: self._commit_add_item(bucket_id, text),
        )

    def _commit_add_item(self, bucket_id: str, text: str) -> None:
        if not text:
            return
        bucket = self._buckets.get(bucket_id)
        if bucket is None:
            return
        bucket["items"].append(text)  # type: ignore[attr-defined]
        self.shell.action_reload()  # type: ignore[attr-defined]

    # --- toggle flagged on the selected item (exercises write + undo) --------

    def _toggle_flagged(self) -> None:
        shell = self.shell
        assert shell is not None
        collection_item = shell.current_collection_item  # type: ignore[attr-defined]
        if collection_item is None:
            return
        item_id = collection_item.id
        currently_flagged = item_id in self._flagged
        self._set_flagged(item_id, not currently_flagged)
        shell.undo_stack.push(  # type: ignore[attr-defined]
            UndoableWrite(
                description=f"{'flag' if not currently_flagged else 'unflag'} item",
                undo=lambda: self._set_flagged(item_id, currently_flagged),
                redo=lambda: self._set_flagged(item_id, not currently_flagged),
            )
        )
        shell.action_reload()  # type: ignore[attr-defined]

    def _set_flagged(self, item_id: str, flagged: bool) -> None:
        if flagged:
            self._flagged.add(item_id)
        else:
            self._flagged.discard(item_id)
