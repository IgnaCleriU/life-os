"""Tests unitarios del parser de quick-add (Python puro, sin DB ni mocks)."""

from datetime import date

from lifeos.adapters.shared.quick_add import parse_quick_add
from lifeos.domain import Priority


def test_plain_title_without_tokens():
    parsed = parse_quick_add("buy air filters")

    assert parsed.title == "buy air filters"
    assert parsed.priority is Priority.MEDIUM
    assert parsed.due_date is None
    assert parsed.project_name is None


def test_priority_token_low():
    parsed = parse_quick_add("buy air filters !low")

    assert parsed.title == "buy air filters"
    assert parsed.priority is Priority.LOW


def test_priority_token_med():
    parsed = parse_quick_add("buy air filters !med")

    assert parsed.title == "buy air filters"
    assert parsed.priority is Priority.MEDIUM


def test_priority_token_high():
    parsed = parse_quick_add("buy air filters !high")

    assert parsed.title == "buy air filters"
    assert parsed.priority is Priority.HIGH


def test_duplicate_priority_tokens_last_wins():
    parsed = parse_quick_add("buy air filters !low !high")

    assert parsed.title == "buy air filters"
    assert parsed.priority is Priority.HIGH


def test_due_date_today():
    today = date(2026, 7, 28)  # martes

    parsed = parse_quick_add("buy air filters @today", today=today)

    assert parsed.due_date == today


def test_due_date_tomorrow():
    today = date(2026, 7, 28)

    parsed = parse_quick_add("buy air filters @tomorrow", today=today)

    assert parsed.due_date == date(2026, 7, 29)


def test_due_date_iso():
    parsed = parse_quick_add(
        "buy air filters @2026-08-03", today=date(2026, 7, 28)
    )

    assert parsed.due_date == date(2026, 8, 3)


def test_due_date_weekday_rolls_to_next_strictly_future_occurrence():
    # 2026-07-28 es martes; el próximo miércoles estrictamente futuro
    # es 2026-07-29 (mañana), no el propio martes.
    today = date(2026, 7, 28)

    parsed = parse_quick_add("buy air filters @wed", today=today)

    assert parsed.due_date == date(2026, 7, 29)


def test_due_date_weekday_same_as_today_rolls_a_full_week():
    # today es martes (weekday()==1); pedir @tue debe caer la semana
    # que viene, no hoy mismo (@today es la forma de decir "hoy").
    today = date(2026, 7, 28)

    parsed = parse_quick_add("buy air filters @tue", today=today)

    assert parsed.due_date == date(2026, 8, 4)


def test_due_date_all_weekday_abbreviations():
    today = date(2026, 7, 27)  # lunes

    expected = {
        "@mon": date(2026, 8, 3),
        "@tue": date(2026, 7, 28),
        "@wed": date(2026, 7, 29),
        "@thu": date(2026, 7, 30),
        "@fri": date(2026, 7, 31),
        "@sat": date(2026, 8, 1),
        "@sun": date(2026, 8, 2),
    }

    for token, due in expected.items():
        parsed = parse_quick_add(f"walk the dog {token}", today=today)
        assert parsed.due_date == due, token


def test_due_date_duplicate_tokens_last_wins():
    today = date(2026, 7, 28)

    parsed = parse_quick_add(
        "buy air filters @today @tomorrow", today=today
    )

    assert parsed.due_date == date(2026, 7, 29)


def test_project_token_extraction():
    parsed = parse_quick_add("buy air filters #casa")

    assert parsed.title == "buy air filters"
    assert parsed.project_name == "casa"


def test_project_token_duplicate_last_wins():
    parsed = parse_quick_add("buy air filters #casa #trabajo")

    assert parsed.title == "buy air filters"
    assert parsed.project_name == "trabajo"


def test_tag_token_is_stripped_and_discarded():
    parsed = parse_quick_add("buy air filters +errand")

    assert parsed.title == "buy air filters"
    assert not hasattr(parsed, "tags")


def test_multiple_tag_tokens_all_discarded():
    parsed = parse_quick_add("buy air filters +errand +urgent")

    assert parsed.title == "buy air filters"


def test_malformed_priority_token_falls_back_to_title():
    parsed = parse_quick_add("buy air filters !urgent")

    assert parsed.title == "buy air filters !urgent"
    assert parsed.priority is Priority.MEDIUM


def test_malformed_priority_medium_spelled_out_falls_back_to_title():
    parsed = parse_quick_add("buy air filters !medium")

    assert parsed.title == "buy air filters !medium"
    assert parsed.priority is Priority.MEDIUM


def test_bare_bang_falls_back_to_title():
    parsed = parse_quick_add("buy air filters !")

    assert parsed.title == "buy air filters !"
    assert parsed.priority is Priority.MEDIUM


def test_malformed_due_date_word_falls_back_to_title():
    parsed = parse_quick_add("buy air filters @whenever")

    assert parsed.title == "buy air filters @whenever"
    assert parsed.due_date is None


def test_malformed_due_date_invalid_iso_falls_back_to_title():
    parsed = parse_quick_add("buy air filters @2026-13-45")

    assert parsed.title == "buy air filters @2026-13-45"
    assert parsed.due_date is None


def test_bare_at_falls_back_to_title():
    parsed = parse_quick_add("buy air filters @")

    assert parsed.title == "buy air filters @"
    assert parsed.due_date is None


def test_bare_hash_falls_back_to_title():
    parsed = parse_quick_add("buy air filters #")

    assert parsed.title == "buy air filters #"
    assert parsed.project_name is None


def test_bare_plus_falls_back_to_title():
    parsed = parse_quick_add("buy air filters +")

    assert parsed.title == "buy air filters +"


def test_adr_example_string():
    # "buy air filters !high @sat #casa" del propio ADR 0008.
    today = date(2026, 7, 28)  # martes

    parsed = parse_quick_add(
        "buy air filters !high @sat #casa", today=today
    )

    assert parsed.title == "buy air filters"
    assert parsed.priority is Priority.HIGH
    assert parsed.due_date == date(2026, 8, 1)
    assert parsed.project_name == "casa"


def test_empty_input_returns_empty_title():
    parsed = parse_quick_add("")

    assert parsed.title == ""
    assert parsed.priority is Priority.MEDIUM
    assert parsed.due_date is None
    assert parsed.project_name is None


def test_whitespace_only_input_returns_empty_title():
    parsed = parse_quick_add("   ")

    assert parsed.title == ""
    assert parsed.priority is Priority.MEDIUM
    assert parsed.due_date is None
    assert parsed.project_name is None
