from __future__ import annotations

from typing import ClassVar

from textual.binding import BindingType
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option, OptionDoesNotExist

from lifeos.adapters.tui.module import DetailContents, PaneContents, PaneItem


class ItemListPane(OptionList):
    """Shared rendering for the context and collection panes: a selectable
    list built from a `PaneContents`. Not mounted directly — `ContextPane`
    and `CollectionPane` subclass it so the shell can target each by type.

    Key dispatch is owned entirely by ShellScreen's keymap registry (ADR
    0008's single-dispatch-path requirement), so OptionList's own default
    bindings (up/down/enter/...) are cleared here - otherwise a keypress
    could be handled twice, or by the wrong system, depending on focus.
    Cursor movement is still driven through OptionList's own
    action_cursor_down()/action_cursor_up()/etc., just invoked by the
    shell's dispatch instead of Textual's binding resolution.
    """

    BINDINGS: ClassVar[list[BindingType]] = []

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._items_by_id: dict[str, PaneItem] = {}
        self._all_items: list[PaneItem] = []

    def update_contents(
        self, contents: PaneContents, select_id: str | None = None
    ) -> None:
        self._all_items = list(contents.items)
        self._render_items(self._all_items, select_id=select_id)

    def _render_items(
        self, items: list[PaneItem], select_id: str | None = None
    ) -> None:
        # Captured before clear_options() wipes them - the only state this
        # class needs to remember "where the user was" across a re-render.
        previous_item = self.selected_item
        previous_index = self.highlighted
        self.clear_options()
        self._items_by_id = {item.id: item for item in items}
        for item in items:
            text = f"{item.label}  {item.meta}".rstrip()
            self.add_option(Option(text, id=item.id))
        # ADR 0008: "no pane holds state that is invisible in the interface"
        # - a freshly populated pane always has something highlighted (when
        # non-empty). Written exactly once, so a single re-render posts at
        # most one OptionHighlighted message.
        self.highlighted = self._resolve_highlight(
            items,
            select_id=select_id,
            previous_id=None if previous_item is None else previous_item.id,
            previous_index=previous_index,
        )

    def _resolve_highlight(
        self,
        items: list[PaneItem],
        *,
        select_id: str | None,
        previous_id: str | None,
        previous_index: int | None,
    ) -> int | None:
        """Where the highlight lands after a re-render, in priority order:
        an explicit `select_id` (e.g. the item just created) if it's
        actually rendered; else wherever the pane's own prior selection
        still is - so an id that isn't in this render (a create routed
        elsewhere, or hidden by a filter) leaves the pane exactly where the
        user was instead of resetting it; else the same row position,
        clamped, so removing the selected row lands on the row that took
        its place rather than jumping to the top; else row 0, or nothing
        for an empty pane."""
        if not items:
            return None
        for candidate_id in (select_id, previous_id):
            if candidate_id is None:
                continue
            try:
                return self.get_option_index(candidate_id)
            except OptionDoesNotExist:
                continue
        if previous_index is not None:
            return min(previous_index, len(items) - 1)
        return 0

    def filter(self, text: str) -> None:
        """Live substring filter (case-insensitive) over the full item set
        captured at the last `update_contents()` call - not the currently
        rendered (possibly already-filtered) subset, so filtering is never
        cumulative across keystrokes."""
        needle = text.casefold()
        matches = [item for item in self._all_items if needle in item.label.casefold()]
        self._render_items(matches)

    def clear_filter(self) -> None:
        self._render_items(self._all_items)

    @property
    def selected_item(self) -> PaneItem | None:
        option = self.highlighted_option
        if option is None or option.id is None:
            return None
        return self._items_by_id.get(option.id)


class ContextPane(ItemListPane):
    """The leftmost pane: top-level items (e.g. projects)."""


class CollectionPane(ItemListPane):
    """The middle pane: items under the selected context item (e.g. tasks)."""


class DetailPane(Static):
    """The rightmost pane: a read-only preview of the selected collection item."""

    can_focus = True
    """`Static.can_focus` defaults to False, but the ADR's h/l/Tab
    navigation moves focus across all three panes, detail included."""

    def update_contents(self, contents: DetailContents | None) -> None:
        if contents is None:
            self.update("(nothing selected)")
            return
        lines = [contents.title, ""]
        lines.extend(f"{label:<12} {value}" for label, value in contents.fields)
        self.update("\n".join(lines))
