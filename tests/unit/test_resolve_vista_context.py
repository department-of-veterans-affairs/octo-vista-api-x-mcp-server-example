"""Unit tests for resolve_vista_context helper."""

from typing import Any

from src.utils import (
    VISTA_CONTEXT_DUZ_KEY,
    VISTA_CONTEXT_STATE_KEY,
    VISTA_CONTEXT_STATION_KEY,
    resolve_vista_context,
)


class DummyContext:
    def __init__(self, state: dict[str, Any] | None = None) -> None:
        self._state = state

    def get_state(self, key: str) -> Any:
        if key != VISTA_CONTEXT_STATE_KEY:
            raise KeyError(key)
        return self._state


def test_resolve_uses_context_state_when_available() -> None:
    ctx = DummyContext(
        {
            VISTA_CONTEXT_STATION_KEY: "  508 ",
            VISTA_CONTEXT_DUZ_KEY: "10000000220",
        }
    )

    station, duz = resolve_vista_context(ctx, station_arg=None, duz_arg=None)

    assert station == "508"
    assert duz == "10000000220"


def test_resolve_prefers_explicit_arguments() -> None:
    ctx = DummyContext(
        {
            VISTA_CONTEXT_STATION_KEY: "500",
            VISTA_CONTEXT_DUZ_KEY: "10000000001",
        }
    )

    station, duz = resolve_vista_context(ctx, station_arg="640", duz_arg="123")

    assert station == "640"
    assert duz == "123"


def test_resolve_uses_fallback_callables_when_missing() -> None:
    calls: dict[str, int] = {"station": 0, "duz": 0}

    def fallback_station() -> str:
        calls["station"] += 1
        return "999"

    def fallback_duz() -> str:
        calls["duz"] += 1
        return "111"

    station, duz = resolve_vista_context(
        None,
        station_arg=None,
        duz_arg=None,
        default_station=fallback_station,
        default_duz=fallback_duz,
    )

    assert station == "999"
    assert duz == "111"
    assert calls == {"station": 1, "duz": 1}
