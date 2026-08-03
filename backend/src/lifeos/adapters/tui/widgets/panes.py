from __future__ import annotations

from typing import ClassVar

from textual.binding import BindingType
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

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

    def update_contents(self, contents: PaneContents) -> None:
        # Every reload rebuilds the option list from scratch, so the
        # highlighted item's identity would otherwise always reset to
        # index 0 - re-select the same item by id if it's still present,
        # so a reload (e.g. after a reorder) doesn't move the cursor out
        # from under the user.
        previous_id = self.selected_item.id if self.selected_item else None
        self._all_items = list(contents.items)
        self._render_items(self._all_items, keep_selected_id=previous_id)

    def _render_items(
        self, items: list[PaneItem], *, keep_selected_id: str | None = None
    ) -> None:
        self.clear_options()
        self._items_by_id = {item.id: item for item in items}
        for item in items:
            text = f"{item.label}  {item.meta}".rstrip()
            self.add_option(Option(text, id=item.id))
        # ADR 0008: "no pane holds state that is invisible in the interface"
        # - a freshly populated pane always has something highlighted (when
        # non-empty) so the pane to its right has something to sync against.
        if keep_selected_id is not None and keep_selected_id in self._items_by_id:
            self.highlighted = next(
                i for i, item in enumerate(items) if item.id == keep_selected_id
            )
        else:
            self.highlighted = 0 if items else None

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
