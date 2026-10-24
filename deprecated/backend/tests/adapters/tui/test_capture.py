from __future__ import annotations

from lifeos.adapters.tui import capture


def test_main_inserts_capture_and_delegates_to_the_cli_app(monkeypatch) -> None:  # noqa: ANN001
    calls: list[list[str]] = []
    def _spy() -> None:
        calls.append(list(capture.sys.argv))

    monkeypatch.setattr(capture, "cli_main", _spy)
    monkeypatch.setattr(
        capture.sys, "argv", ["lifeos-capture", "buy", "milk", "!high", "@sat"]
    )

    capture.main()

    assert calls == [["lifeos-capture", "capture", "buy", "milk", "!high", "@sat"]]


def test_main_works_with_no_extra_arguments(monkeypatch) -> None:  # noqa: ANN001
    calls: list[list[str]] = []
    def _spy() -> None:
        calls.append(list(capture.sys.argv))

    monkeypatch.setattr(capture, "cli_main", _spy)
    monkeypatch.setattr(capture.sys, "argv", ["lifeos-capture"])

    capture.main()

    assert calls == [["lifeos-capture", "capture"]]
