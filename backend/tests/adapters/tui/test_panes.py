from textual.app import App, ComposeResult
from textual.widgets import OptionList

from lifeos.adapters.tui.module import DetailContents, PaneContents, PaneItem
from lifeos.adapters.tui.widgets.panes import (
    CollectionPane,
    ContextPane,
    DetailPane,
    ItemListPane,
)


class _PanesHarness(App):
    def __init__(self) -> None:
        super().__init__()
        self.highlighted_events = 0

    def compose(self) -> ComposeResult:
        yield ContextPane(id="context")
        yield CollectionPane(id="collection")
        yield DetailPane(id="detail")

    def on_option_list_option_highlighted(
        self, event: OptionList.OptionHighlighted
    ) -> None:
        self.highlighted_events += 1


def _two_item_contents() -> PaneContents:
    return PaneContents(
        title="PROJECTS",
        items=[
            PaneItem(id="p1", label="life os", payload="life-os-payload", meta="12"),
            PaneItem(id="p2", label="casa", payload="casa-payload", meta="3"),
        ],
    )


async def test_context_pane_renders_one_option_per_item() -> None:
    app = _PanesHarness()
    async with app.run_test():
        pane = app.query_one("#context", ContextPane)
        pane.update_contents(_two_item_contents())
        assert pane.option_count == 2


async def test_context_pane_option_text_includes_label_and_meta() -> None:
    app = _PanesHarness()
    async with app.run_test():
        pane = app.query_one("#context", ContextPane)
        pane.update_contents(_two_item_contents())
        prompts = [
            str(pane.get_option_at_index(i).prompt) for i in range(pane.option_count)
        ]
        assert any("life os" in p and "12" in p for p in prompts)
        assert any("casa" in p and "3" in p for p in prompts)


async def test_context_pane_selected_item_is_none_before_any_highlight() -> None:
    app = _PanesHarness()
    async with app.run_test():
        pane = app.query_one("#context", ContextPane)
        assert pane.selected_item is None


async def test_context_pane_selected_item_returns_the_highlighted_pane_item() -> None:
    app = _PanesHarness()
    async with app.run_test():
        pane = app.query_one("#context", ContextPane)
        pane.update_contents(_two_item_contents())
        pane.highlighted = 1
        selected = pane.selected_item
        assert selected is not None
        assert selected.id == "p2"
        assert selected.payload == "casa-payload"


async def test_update_contents_replaces_previous_items_rather_than_appending() -> None:
    app = _PanesHarness()
    async with app.run_test():
        pane = app.query_one("#context", ContextPane)
        pane.update_contents(_two_item_contents())
        single_item = PaneItem(id="p3", label="learning", payload=None)
        pane.update_contents(PaneContents(title="PROJECTS", items=[single_item]))
        assert pane.option_count == 1
        # a fresh non-empty render highlights the first item (ADR 0008: no
        # pane holds state invisible in the interface) - not a leftover
        # from the previous render, which only had "p1"/"p2", never "p3"
        assert pane.selected_item is not None
        assert pane.selected_item.id == "p3"


async def test_update_contents_with_select_id_highlights_that_item() -> None:
    app = _PanesHarness()
    async with app.run_test():
        pane = app.query_one("#context", ContextPane)
        pane.update_contents(_two_item_contents(), select_id="p2")
        assert pane.selected_item is not None
        assert pane.selected_item.id == "p2"


async def test_update_contents_with_unknown_select_id_falls_back_to_first_item() -> None:
    app = _PanesHarness()
    async with app.run_test():
        pane = app.query_one("#context", ContextPane)
        pane.update_contents(_two_item_contents(), select_id="does-not-exist")
        assert pane.selected_item is not None
        assert pane.selected_item.id == "p1"


async def test_update_contents_with_unreachable_select_id_preserves_prior_selection() -> (
    None
):
    # The real-world trigger: a quick-added task routed to a different
    # project (or a project created while a non-matching status filter is
    # active) passes a select_id for an item this pane never renders. That
    # must not be worse than passing no id at all - it should leave the
    # pane exactly where the user was, not snap to row 0.
    app = _PanesHarness()
    async with app.run_test():
        pane = app.query_one("#context", ContextPane)
        pane.update_contents(_two_item_contents())
        pane.highlighted = 1  # p2
        pane.update_contents(_two_item_contents(), select_id="not-rendered-here")
        assert pane.selected_item is not None
        assert pane.selected_item.id == "p2"


async def test_removing_the_selected_item_falls_back_to_the_nearest_row_not_row_zero() -> (
    None
):
    app = _PanesHarness()
    async with app.run_test():
        pane = app.query_one("#context", ContextPane)
        three_items = PaneContents(
            title="PROJECTS",
            items=[
                PaneItem(id="p1", label="alpha", payload=None),
                PaneItem(id="p2", label="beta", payload=None),
                PaneItem(id="p3", label="gamma", payload=None),
            ],
        )
        pane.update_contents(three_items)
        pane.highlighted = 2  # p3
        pane.update_contents(
            PaneContents(
                title="PROJECTS",
                items=[
                    PaneItem(id="p1", label="alpha", payload=None),
                    PaneItem(id="p2", label="beta", payload=None),
                ],
            )
        )
        assert pane.selected_item is not None
        assert pane.selected_item.id == "p2"


async def test_update_contents_posts_at_most_one_option_highlighted_message() -> None:
    app = _PanesHarness()
    async with app.run_test() as pilot:
        pane = app.query_one("#context", ContextPane)
        pane.update_contents(_two_item_contents())
        await pilot.pause()
        app.highlighted_events = 0
        pane.update_contents(_two_item_contents(), select_id="p2")
        await pilot.pause()
        assert app.highlighted_events <= 1


def _three_item_contents() -> PaneContents:
    return PaneContents(
        title="PROJECTS",
        items=[
            PaneItem(id="p1", label="write adr", payload=None),
            PaneItem(id="p2", label="write tests", payload=None),
            PaneItem(id="p3", label="casa", payload=None),
        ],
    )


async def test_filter_preserves_the_highlighted_item_by_id() -> None:
    app = _PanesHarness()
    async with app.run_test():
        pane = app.query_one("#context", ContextPane)
        pane.update_contents(_three_item_contents())
        pane.highlighted = 1  # p2 ("write tests")
        pane.filter("write")  # matches p1 and p2, p2 is index 1 of the matches
        assert pane.selected_item is not None
        assert pane.selected_item.id == "p2"


async def test_clear_filter_preserves_the_highlighted_item_by_id() -> None:
    app = _PanesHarness()
    async with app.run_test():
        pane = app.query_one("#context", ContextPane)
        pane.update_contents(_three_item_contents())
        pane.highlighted = 1  # p2 ("write tests")
        pane.filter("write")
        pane.clear_filter()
        assert pane.selected_item is not None
        assert pane.selected_item.id == "p2"


async def test_collection_pane_is_a_distinct_type_from_context_pane() -> None:
    app = _PanesHarness()
    async with app.run_test():
        collection = app.query_one("#collection", CollectionPane)
        collection.update_contents(_two_item_contents())
        assert collection.option_count == 2
        assert not isinstance(collection, ContextPane)


async def test_detail_pane_shows_placeholder_when_contents_is_none() -> None:
    app = _PanesHarness()
    async with app.run_test():
        pane = app.query_one("#detail", DetailPane)
        pane.update_contents(None)
        assert "nothing selected" in str(pane.render())


async def test_detail_pane_renders_title_and_fields() -> None:
    app = _PanesHarness()
    async with app.run_test():
        pane = app.query_one("#detail", DetailPane)
        pane.update_contents(
            DetailContents(
                title="write adr 0008",
                fields=[("status", "doing"), ("priority", "high")],
            )
        )
        rendered = str(pane.render())
        assert "write adr 0008" in rendered
        assert "status" in rendered and "doing" in rendered
        assert "priority" in rendered and "high" in rendered


def test_item_list_pane_has_no_builtin_key_bindings() -> None:
    # ShellScreen owns ALL key dispatch via the keymap registry (single
    # dispatch path, ADR 0008's "single keymap registry" requirement) -
    # OptionList's own default bindings (up/down/enter/...) must not
    # compete with that, or a keypress could be handled twice or handled
    # by the wrong system.
    assert ItemListPane.BINDINGS == []


async def test_detail_pane_can_receive_focus() -> None:
    # DetailPane is a Static subclass, and Static.can_focus defaults to
    # False - but the ADR's h/l/Tab navigation moves focus across all three
    # panes including detail, so it must be focusable like the other two.
    app = _PanesHarness()
    async with app.run_test() as pilot:
        pane = app.query_one("#detail", DetailPane)
        pane.focus()
        await pilot.pause()
        assert app.focused is pane
