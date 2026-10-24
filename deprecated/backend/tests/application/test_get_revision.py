"""Tests del caso de uso GetRevision (sin DB, con una fuente fake)."""

from lifeos.application.use_cases.get_revision import GetRevision


class _FakeRevisionSource:
    def __init__(self) -> None:
        self.value = "1"

    def current(self) -> str:
        return self.value


def test_returns_the_current_revision():
    source = _FakeRevisionSource()

    assert GetRevision(source).execute() == "1"


def test_reflects_changes_in_the_source():
    source = _FakeRevisionSource()
    use_case = GetRevision(source)
    before = use_case.execute()

    source.value = "2"

    assert use_case.execute() != before
