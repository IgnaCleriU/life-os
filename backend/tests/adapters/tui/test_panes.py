from textual.app import App, ComposeResult

from lifeos.adapters.tui.module import DetailContents, PaneContents, PaneItem
from lifeos.adapters.tui.widgets.panes import (
    CollectionPane,
    ContextPane,
    DetailPane,
    ItemListPane,
)


class _PanesHarness(App):
    def compose(self) -> ComposeResult:
        yield ContextPane(id="context")
        yield CollectionPane(id="collection")
        yield DetailPane(id="detail")


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
        # nothing highlighted yet after a fresh render
        assert pane.selected_item is None


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
