"""Tests for /undo."""

from pathlib import Path

import pytest
from lmdk.datatypes import AssistantMessage, UserMessage

from lmti.commands.undo import _format_user_preview, handle_undo
from lmti.repl import ReplState


def test_format_user_preview_short():
    assert _format_user_preview("hi") == "[user] hi"


def test_format_user_preview_long():
    out = _format_user_preview("x" * 200)
    assert out.endswith("…")


def test_handle_undo_empty(console):
    state = ReplState()
    handle_undo(console, state)
    assert state.messages == []


@pytest.fixture
def populated_state():
    state = ReplState()
    state.messages = [
        UserMessage("first"),
        AssistantMessage("a1"),
        UserMessage("second"),
        AssistantMessage("a2"),
    ]
    state.conversation_path = Path("/tmp/x.jsonl")
    return state


def test_handle_undo_cancel(console, monkeypatch, populated_state):
    monkeypatch.setattr("lmti.ui.prompt_selection", lambda *a, **k: None)
    handle_undo(console, populated_state)
    assert len(populated_state.messages) == 4


def test_handle_undo_first_user_clears(console, monkeypatch, populated_state):
    monkeypatch.setattr("lmti.ui.prompt_selection", lambda *a, **k: 1)
    handle_undo(console, populated_state)
    assert populated_state.messages == []
    assert populated_state.conversation_path is None


def test_handle_undo_second_user_truncates(console, monkeypatch, populated_state):
    saved = []
    monkeypatch.setattr("lmti.ui.prompt_selection", lambda *a, **k: 2)
    monkeypatch.setattr(
        "lmti.commands.undo.save_conversation",
        lambda msgs, path: saved.append((list(msgs), path)) or path,
    )
    handle_undo(console, populated_state)
    # Kept first user + its assistant; dropped second user + assistant.
    assert [m.content for m in populated_state.messages] == ["first", "a1"]
    assert saved and saved[0][1] == Path("/tmp/x.jsonl")
